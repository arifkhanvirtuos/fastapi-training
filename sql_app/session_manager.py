"""
Redis-based Session Manager for FastAPI
Provides secure session storage and management
"""

import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from redis_client import RedisClient


class SessionManager:
    """Manage user sessions in Redis"""
    
    def __init__(self, redis: RedisClient, session_ttl: int = 86400):
        """
        Initialize session manager
        
        Args:
            redis: Redis client
            session_ttl: Session time-to-live in seconds (default: 24 hours)
        """
        self.redis = redis
        self.session_ttl = session_ttl
    
    async def create_session(
        self,
        user_id: str,
        data: Dict[str, Any] = None
    ) -> str:
        """
        Create new session
        
        Args:
            user_id: User ID
            data: Additional session data
        
        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "ip_address": None,
            "user_agent": None,
            **(data or {})
        }
        
        await self.redis.set(
            f"session:{session_id}",
            session_data,
            ex=self.session_ttl
        )
        
        # Also index by user_id for quick user lookup
        await self.redis.lpush(f"user_sessions:{user_id}", session_id)
        await self.redis.expire(f"user_sessions:{user_id}", self.session_ttl)
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        data = await self.redis.get(f"session:{session_id}")
        if not data:
            return None
        
        # Parse if JSON string
        if isinstance(data, str):
            try:
                return json.loads(data)
            except:
                return None
        
        return data
    
    async def update_activity(self, session_id: str) -> bool:
        """Update last activity timestamp (extends TTL)"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session["last_activity"] = datetime.utcnow().isoformat()
        
        await self.redis.set(
            f"session:{session_id}",
            session,
            ex=self.session_ttl
        )
        
        return True
    
    async def destroy_session(self, session_id: str) -> bool:
        """Delete session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        await self.redis.delete(f"session:{session_id}")
        
        # Remove from user sessions
        user_id = session.get("user_id")
        if user_id:
            # Find and remove from list
            sessions = await self.redis.lrange(f"user_sessions:{user_id}", 0, -1)
            if session_id in sessions:
                await self.redis.delete(f"user_sessions:{user_id}")
                # Re-add all except this one
                for sid in sessions:
                    if sid != session_id:
                        await self.redis.lpush(f"user_sessions:{user_id}", sid)
        
        return True
    
    async def get_user_sessions(self, user_id: str) -> list:
        """Get all sessions for a user"""
        session_ids = await self.redis.lrange(f"user_sessions:{user_id}", 0, -1)
        
        sessions = []
        for session_id in session_ids:
            session = await self.get_session(session_id)
            if session:
                sessions.append(session)
        
        return sessions
    
    async def destroy_all_user_sessions(self, user_id: str) -> int:
        """Destroy all sessions for a user (logout everywhere)"""
        session_ids = await self.redis.lrange(f"user_sessions:{user_id}", 0, -1)
        
        deleted = 0
        for session_id in session_ids:
            if await self.destroy_session(session_id):
                deleted += 1
        
        await self.redis.delete(f"user_sessions:{user_id}")
        
        return deleted
    
    async def set_session_data(
        self,
        session_id: str,
        key: str,
        value: Any
    ) -> bool:
        """Set custom data in session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session[key] = value
        await self.redis.set(
            f"session:{session_id}",
            session,
            ex=self.session_ttl
        )
        
        return True
    
    async def get_session_data(self, session_id: str, key: str) -> Any:
        """Get custom data from session"""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        return session.get(key)
