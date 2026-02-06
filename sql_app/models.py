# create table user( username VARCHAR(50) PRIMARY KEY, full_name VARCHAR(100), email VARCHAR(100) UNIQUE, hashed_password VARCHAR(100), is_active BOOLEAN DEFAULT TRUE );


from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, ARRAY, JSON, Numeric, Text, DateTime, Index, Table, func, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from enum import Enum


# User Role Enumeration
class UserRole(str, Enum):
    """User roles in the system for role-based access control"""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"

# Try relative import first (when used as a package), fall back to absolute
try:
    from .database import Base
except ImportError:
    from database import Base
# Association table for many-to-many relationship
product_raw_material_association = Table(
    'product_raw_material_association',
    Base.metadata,
    Column('product_id', UUID(as_uuid=True), ForeignKey('products.id'), primary_key=True),
    Column('raw_material_id', UUID(as_uuid=True), ForeignKey('raw_materials.id'), primary_key=True)
)
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid= True), primary_key= True, default=uuid.uuid4)
    email = Column(String(100), unique=True,  index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    full_name = Column(String(100), nullable=True)
    phone_number = Column(String(15), nullable=True)
    role = Column(SQLEnum(UserRole, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=UserRole.USER, server_default='user')
    is_active = Column(Boolean, default= False)
    address = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default= func.now())
    updated_at = Column(DateTime, nullable=False, server_default= func.now(), onupdate= func.now())
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    __table_args__=  (Index('idx_user_email', 'email'), Index('idx_user_phone', 'phone_number'), Index('idx_user_composite', 'email', 'is_active'),)




class Product(Base):
    __tablename__ = "products"
    id = Column(UUID(as_uuid= True), primary_key= True, default = uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    raw_materials  = relationship("RawMaterial", secondary=product_raw_material_association, back_populates="products")
    tags = Column(ARRAY(String), nullable=True)
    extra_data = Column(JSONB, nullable = True)  # Renamed from 'metadata' which is reserved


class RawMaterial(Base):
    __tablename__ = "raw_materials"
    id = Column(UUID(as_uuid= True), primary_key= True, default= uuid.uuid4)
    name = Column(String(100), nullable=False)
    quantity = Column(Float, nullable=False)
    products = relationship("Product", secondary=product_raw_material_association, back_populates="raw_materials")



class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(UUID(as_uuid= True), primary_key= True, default= uuid.uuid4)
    user_id = Column(UUID(as_uuid= True), ForeignKey("users.id"), nullable=False)
    address = Column(String(200), nullable=True)
    city = Column(String(50), nullable=True)
    country = Column(String(50), nullable=True)
    postal_code = Column(String(20), nullable=True)
    user = relationship("User", back_populates="profile")









# indexes 

# CREATE INDEX idx_user_email ON users(email);
# CREATE INDEX idx_product_name ON products(name);
# CREATE INDEX idx_user_composite ON users(email, is_active);

