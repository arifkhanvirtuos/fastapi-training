# Quick Start Guide - File Upload Feature

## 1. Install Dependencies

```bash
cd /Users/virtuosdigital/Arif/fastapilearning/sql_app
pip install pillow aiofiles
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## 2. Run Database Migration

The migration will add `profile_picture_url` and `profile_picture_thumbnail_url` fields to the users table.

```bash
# Start Python interactive shell
python3

# Run migration
from database import init_db
init_db()
exit()
```

## 3. Start the Server

```bash
uvicorn main:app --reload
```

## 4. Test the API

### Step 1: Register a User

```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'
```

### Step 2: Login and Get Token

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123"
```

Copy the `access_token` from the response.

### Step 3: Upload Profile Picture

```bash
# Replace YOUR_TOKEN with the access_token from step 2
# Replace /path/to/image.jpg with your actual image path

curl -X POST "http://localhost:8000/users/me/profile-picture" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg"
```

Example with a real token:

```bash
curl -X POST "http://localhost:8000/users/me/profile-picture" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -F "file=@profile.jpg"
```

### Step 4: View Profile Picture

```bash
# Get your user ID from the upload response or login response
# Replace USER_ID with actual user ID

# View in browser (full size)
open "http://localhost:8000/users/USER_ID/profile-picture?size=full"

# View in browser (thumbnail)
open "http://localhost:8000/users/USER_ID/profile-picture?size=thumbnail"

# Download with curl
curl "http://localhost:8000/users/USER_ID/profile-picture?size=full" -o profile_full.jpg
curl "http://localhost:8000/users/USER_ID/profile-picture?size=thumbnail" -o profile_thumb.jpg
```

### Step 5: Delete Profile Picture

```bash
curl -X DELETE "http://localhost:8000/users/me/profile-picture" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 5. View API Documentation

Visit the interactive API docs:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Look for the "File Upload" section to test the endpoints interactively.

## 6. Test with the Swagger UI

1. Open http://localhost:8000/docs
2. Click on "Authorize" button (top right)
3. Get a token from the `/token` endpoint
4. Enter the token in the format: `Bearer your_token_here`
5. Click "Authorize"
6. Navigate to the "File Upload" section
7. Test the endpoints:
   - `POST /users/me/profile-picture` - Upload
   - `GET /users/{user_id}/profile-picture` - Download
   - `DELETE /users/me/profile-picture` - Delete

## 7. Folder Structure After Upload

```
sql_app/
├── uploads/              # Created automatically
│   └── {user_id}/
│       └── 2026/
│           └── 02/
│               ├── {uuid}.jpg        # Full size
│               └── {uuid}_thumb.jpg  # Thumbnail
├── main.py
├── models.py
├── schemas.py
├── requirements.txt
└── ...
```

## Troubleshooting

### Error: "Import 'PIL' could not be resolved"

```bash
pip install pillow
```

### Error: "Import 'aiofiles' could not be resolved"

```bash
pip install aiofiles
```

### Error: "Column 'profile_picture_url' does not exist"

Run the migration:

```python
from database import init_db
init_db()
```

### Error: "401 Unauthorized"

Make sure you:

1. Have a valid token from `/token` endpoint
2. Include it in the `Authorization` header
3. Format: `Authorization: Bearer {token}`

### Error: "413 File too large"

The maximum file size is 5MB. Reduce your image size or compress it.

### Error: "400 Invalid file type"

Only image files are allowed: JPEG, PNG, GIF, WebP

## Sample Test Images

You can use any image file, or download test images:

```bash
# Download a sample image
curl "https://picsum.photos/800/600" -o test_image.jpg
```

## Next Steps

1. ✅ Install dependencies
2. ✅ Run migration
3. ✅ Start server
4. ✅ Test upload endpoint
5. ✅ Test download endpoint
6. ✅ Test delete endpoint
7. 📚 Read FILE_UPLOAD_LECTURE.md for detailed documentation
8. 🎯 Review FILE_UPLOAD_IMPLEMENTATION.md for architecture

---

**Need Help?** Check the comprehensive documentation:

- [FILE_UPLOAD_LECTURE.md](FILE_UPLOAD_LECTURE.md) - Complete learning guide
- [FILE_UPLOAD_IMPLEMENTATION.md](FILE_UPLOAD_IMPLEMENTATION.md) - Implementation details
