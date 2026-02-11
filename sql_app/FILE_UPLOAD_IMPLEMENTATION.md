# File Upload Implementation - Profile Picture Feature

## Overview

This implementation demonstrates a complete file upload system in FastAPI with profile picture upload, validation, processing, and download capabilities.

## 📁 Files Modified

### 1. **FILE_UPLOAD_LECTURE.md** (New)

Comprehensive 1-hour lecture covering:

- File upload with `UploadFile`
- File validation (size, type, magic bytes)
- Saving files to disk/cloud
- File download and streaming
- Image processing with Pillow
- Best practices and security

### 2. **requirements.txt**

Added dependencies:

```txt
pillow>=10.0.0
aiofiles>=23.0.0
```

### 3. **models.py**

Added to `User` model:

```python
profile_picture_url = Column(String(500), nullable=True)
profile_picture_thumbnail_url = Column(String(500), nullable=True)
```

### 4. **schemas.py**

- Updated `UserResponse` to include profile picture fields
- Added `ProfilePictureUploadResponse` schema

### 5. **main.py**

Added:

- File upload imports (`UploadFile`, `File`, `FileResponse`, `aiofiles`, `Pillow`)
- Upload configuration (directory, max size, allowed types)
- Validation helpers (`validate_image_file`, `validate_upload_file`)
- Image processing functions (`process_image`, `create_thumbnail`)
- Three new endpoints (upload, download, delete)

### 6. **Alembic Migration**

Created: `a1b2c3d4e5f6_add_profile_picture_fields_to_users.py`

## 🚀 New API Endpoints

### 1. Upload Profile Picture

```http
POST /users/me/profile-picture
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: [image file]
```

**Features:**

- ✅ Validates file type (JPEG, PNG, GIF, WebP)
- ✅ Validates file size (max 5MB)
- ✅ Validates actual file content (magic bytes)
- ✅ Resizes to max 1000x1000 (maintains aspect ratio)
- ✅ Creates 200x200 thumbnail
- ✅ Converts to JPEG format
- ✅ Optimizes quality (85%)
- ✅ Deletes old profile pictures
- ✅ Stores organized by user/year/month

**Response:**

```json
{
  "message": "Profile picture uploaded successfully",
  "profile_picture_url": "users/123/2024/01/abc-123.jpg",
  "thumbnail_url": "users/123/2024/01/abc-123_thumb.jpg"
}
```

### 2. Get Profile Picture

```http
GET /users/{user_id}/profile-picture?size=full
GET /users/{user_id}/profile-picture?size=thumbnail
```

**Parameters:**

- `user_id` (path): UUID of the user
- `size` (query): "full" or "thumbnail" (default: "full")

**Response:** Image file (JPEG)

**Headers:**

```
Content-Type: image/jpeg
Cache-Control: public, max-age=3600
```

### 3. Delete Profile Picture

```http
DELETE /users/me/profile-picture
Authorization: Bearer {token}
```

**Response:**

```json
{
  "message": "Profile picture deleted successfully"
}
```

## 📂 File Organization

Uploaded files are organized as:

```
uploads/
  └── {user_id}/
      └── {year}/
          └── {month}/
              ├── {uuid}.jpg          # Full size
              └── {uuid}_thumb.jpg    # Thumbnail
```

Example:

```
uploads/
  └── 550e8400-e29b-41d4-a716-446655440000/
      └── 2026/
          └── 02/
              ├── a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg
              └── a1b2c3d4-e5f6-7890-abcd-ef1234567890_thumb.jpg
```

## 🔒 Security Features

1. **Triple Validation:**
   - Content-Type header check
   - File extension validation
   - Magic bytes validation (actual file content)

2. **Size Limits:**
   - Maximum file size: 5MB
   - Prevents storage exhaustion

3. **File Type Restriction:**
   - Only image files (JPEG, PNG, GIF, WebP)
   - No executable files

4. **Authentication:**
   - All upload/delete operations require authentication
   - Users can only modify their own pictures

5. **File Sanitization:**
   - All uploads converted to JPEG
   - Removes EXIF data
   - Optimized for web

## 🎨 Image Processing

### Full Size Image

- **Max dimensions:** 1000x1000 pixels
- **Format:** JPEG
- **Quality:** 85%
- **Optimization:** Enabled
- **Aspect ratio:** Maintained

### Thumbnail

- **Max dimensions:** 200x200 pixels
- **Format:** JPEG
- **Quality:** 85%
- **Optimization:** Enabled
- **Aspect ratio:** Maintained

## 📝 Usage Examples

### 1. Upload with cURL

```bash
curl -X POST "http://localhost:8000/users/me/profile-picture" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@/path/to/profile.jpg"
```

### 2. Upload with Python

```python
import requests

url = "http://localhost:8000/users/me/profile-picture"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
files = {"file": open("profile.jpg", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

### 3. Upload with JavaScript (Fetch)

```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);

fetch("http://localhost:8000/users/me/profile-picture", {
  method: "POST",
  headers: {
    Authorization: "Bearer " + token,
  },
  body: formData,
})
  .then((response) => response.json())
  .then((data) => console.log(data));
```

### 4. Display Profile Picture

```html
<!-- Full size -->
<img
  src="http://localhost:8000/users/{user_id}/profile-picture?size=full"
  alt="Profile"
/>

<!-- Thumbnail -->
<img
  src="http://localhost:8000/users/{user_id}/profile-picture?size=thumbnail"
  alt="Profile Thumbnail"
/>
```

## 🧪 Testing Guide

### 1. Install Dependencies

```bash
cd sql_app
pip install -r requirements.txt
```

### 2. Run Migration

```bash
# Using Python
python -c "from database import init_db; init_db()"

# Or using Alembic directly (if installed)
alembic upgrade head
```

### 3. Start Server

```bash
python run.sh
# or
uvicorn main:app --reload
```

### 4. Register and Login

```bash
# Register
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'

# Login
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123"
```

### 5. Upload Profile Picture

```bash
# Save the token from login response
TOKEN="your_access_token_here"

# Upload picture
curl -X POST "http://localhost:8000/users/me/profile-picture" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_image.jpg"
```

### 6. View Profile Picture

```bash
# Get your user ID from the login response or /users/me endpoint
USER_ID="your_user_id"

# Download full size
curl "http://localhost:8000/users/$USER_ID/profile-picture?size=full" \
  -o downloaded_full.jpg

# Download thumbnail
curl "http://localhost:8000/users/$USER_ID/profile-picture?size=thumbnail" \
  -o downloaded_thumb.jpg
```

### 7. Delete Profile Picture

```bash
curl -X DELETE "http://localhost:8000/users/me/profile-picture" \
  -H "Authorization: Bearer $TOKEN"
```

## 📊 Database Schema

The migration adds two new fields to the `users` table:

```sql
ALTER TABLE users
ADD COLUMN profile_picture_url VARCHAR(500),
ADD COLUMN profile_picture_thumbnail_url VARCHAR(500);
```

## 🎯 Key Learning Points

1. **UploadFile** is FastAPI's way to handle file uploads efficiently
2. **Async file I/O** with `aiofiles` improves performance
3. **Triple validation** (content-type, extension, magic bytes) ensures security
4. **Image processing** with Pillow optimizes images for web
5. **Organized storage** makes files easy to manage
6. **Thumbnails** improve performance for listings/previews
7. **FileResponse** efficiently serves static files
8. **Background tasks** can be used for heavy processing
9. **Authentication** protects upload/delete operations
10. **Database references** track file locations

## 🚨 Error Handling

The implementation handles various error cases:

| Status Code | Description                                     |
| ----------- | ----------------------------------------------- |
| 400         | Invalid file type, extension, or size parameter |
| 401         | Unauthorized (missing or invalid token)         |
| 404         | User or profile picture not found               |
| 413         | File too large (>5MB)                           |
| 500         | Server error during upload/processing           |

## 🔄 Future Enhancements

Consider adding:

- [ ] Image cropping UI
- [ ] EXIF orientation correction
- [ ] Multiple image sizes (small, medium, large)
- [ ] CDN integration
- [ ] Rate limiting (uploads per hour)
- [ ] Virus scanning
- [ ] Animated GIF support
- [ ] Video profile pictures
- [ ] Background removal
- [ ] Face detection/centering

## 📚 Related Documentation

- [FILE_UPLOAD_LECTURE.md](FILE_UPLOAD_LECTURE.md) - Complete lecture notes
- [FastAPI File Upload Docs](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [aiofiles Documentation](https://github.com/Tinche/aiofiles)

## ✅ Assignment Checklist

- [x] Upload endpoint with authentication
- [x] File validation (type, size, content)
- [x] Image processing (resize, thumbnail)
- [x] Organized storage structure
- [x] Download endpoint (full & thumbnail)
- [x] Delete endpoint
- [x] Database integration
- [x] Error handling
- [x] Security features
- [x] API documentation

---

**Created:** February 6, 2026  
**Author:** FastAPI Learning Project  
**Status:** ✅ Complete & Ready for Testing
