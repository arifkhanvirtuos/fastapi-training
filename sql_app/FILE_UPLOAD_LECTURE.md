# FastAPI File Upload & Download - Complete Guide

**Duration:** 1 hour  
**Level:** Intermediate

## Table of Contents

1. [File Upload with UploadFile](#1-file-upload-with-uploadfile)
2. [File Validation](#2-file-validation)
3. [Saving Files to Disk/Cloud](#3-saving-files-to-diskcloud)
4. [File Download & Streaming](#4-file-download--streaming)
5. [Image Processing with Pillow](#5-image-processing-with-pillow)
6. [Practice Assignment](#6-practice-assignment)
7. [Best Practices](#7-best-practices)

---

## 1. File Upload with UploadFile

### What is UploadFile?

`UploadFile` is FastAPI's built-in class for handling file uploads. It's based on Starlette's `UploadFile` and provides several advantages over using `bytes`:

- **Memory Efficient**: Files are stored in memory up to a size limit, then automatically stored on disk
- **Async Support**: Full async/await support for better performance
- **Metadata Access**: Provides filename, content type, and other metadata
- **Stream-based**: Can read files in chunks to handle large files

### Basic File Upload

```python
from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    Basic file upload endpoint
    File(...) makes the parameter required
    """
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size
    }
```

### UploadFile Attributes & Methods

```python
# Attributes
file.filename      # Original filename (str)
file.content_type  # MIME type (e.g., 'image/jpeg')
file.size          # File size in bytes (optional)
file.file          # SpooledTemporaryFile object

# Methods
await file.read()           # Read entire file
await file.read(size)       # Read specific number of bytes
await file.seek(offset)     # Move file pointer
await file.write(data)      # Write to file
await file.close()          # Close file
```

### Multiple File Upload

```python
@app.post("/upload-multiple/")
async def upload_multiple_files(files: list[UploadFile] = File(...)):
    """Upload multiple files at once"""
    results = []
    for file in files:
        results.append({
            "filename": file.filename,
            "content_type": file.content_type,
        })
    return {"uploaded_files": results}
```

### Optional File Upload

```python
@app.post("/upload-optional/")
async def upload_optional_file(file: UploadFile | None = File(None)):
    """File upload is optional"""
    if file is None:
        return {"message": "No file uploaded"}
    return {"filename": file.filename}
```

---

## 2. File Validation

### Why Validate Files?

- **Security**: Prevent malicious file uploads (malware, scripts)
- **Storage**: Prevent storage exhaustion from large files
- **Compatibility**: Ensure only supported file types
- **Performance**: Avoid processing invalid files

### File Size Validation

```python
from fastapi import HTTPException

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

async def validate_file_size(file: UploadFile):
    """Validate file size"""
    # Read file in chunks to avoid memory issues
    size = 0
    chunk_size = 1024 * 1024  # 1 MB chunks

    while chunk := await file.read(chunk_size):
        size += len(chunk)
        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {MAX_FILE_SIZE} bytes"
            )

    # Reset file pointer to beginning
    await file.seek(0)
    return size

@app.post("/upload-validated/")
async def upload_validated_file(file: UploadFile = File(...)):
    size = await validate_file_size(file)
    return {"filename": file.filename, "size": size}
```

### File Type Validation (MIME Type)

```python
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp"
}

def validate_content_type(file: UploadFile):
    """Validate file MIME type"""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {ALLOWED_CONTENT_TYPES}"
        )
```

### File Extension Validation

```python
import os

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

def validate_file_extension(filename: str):
    """Validate file extension"""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed: {ALLOWED_EXTENSIONS}"
        )
```

### Magic Bytes Validation (Most Secure)

```python
import imghdr

async def validate_image_file(file: UploadFile):
    """
    Validate image file by reading magic bytes
    More secure than checking MIME type or extension
    """
    # Read first 512 bytes for magic number check
    header = await file.read(512)
    await file.seek(0)

    # Detect image type from content
    image_type = imghdr.what(None, h=header)

    if image_type not in ['jpeg', 'png', 'gif', 'webp']:
        raise HTTPException(
            status_code=400,
            detail="Invalid image file"
        )

    return image_type
```

### Combined Validation Function

```python
async def validate_upload_file(
    file: UploadFile,
    max_size: int = 5 * 1024 * 1024,
    allowed_types: set = None
):
    """
    Comprehensive file validation
    """
    if allowed_types is None:
        allowed_types = {"image/jpeg", "image/png", "image/gif"}

    # Validate content type
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {file.content_type}"
        )

    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = {".jpg", ".jpeg", ".png", ".gif"}
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension: {ext}"
        )

    # Validate size
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(contents)} bytes"
        )

    # Reset file pointer
    await file.seek(0)

    return True
```

---

## 3. Saving Files to Disk/Cloud

### Saving to Local Disk

```python
import aiofiles
import os
import uuid
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

async def save_file_to_disk(file: UploadFile) -> str:
    """
    Save uploaded file to disk with unique filename
    Returns: path to saved file
    """
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    # Save file using aiofiles for async I/O
    async with aiofiles.open(file_path, 'wb') as f:
        contents = await file.read()
        await f.write(contents)

    return str(file_path)

@app.post("/upload-save/")
async def upload_and_save(file: UploadFile = File(...)):
    """Upload and save file to disk"""
    await validate_upload_file(file)
    file_path = await save_file_to_disk(file)
    return {"filename": file.filename, "saved_path": file_path}
```

### Chunked File Writing (Large Files)

```python
async def save_large_file(file: UploadFile) -> str:
    """
    Save large file in chunks to avoid memory issues
    """
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            await f.write(chunk)

    return str(file_path)
```

### Organized File Storage

```python
from datetime import datetime

def get_upload_path(user_id: str, file_type: str) -> Path:
    """
    Organize files by user and date
    Structure: uploads/{user_id}/{year}/{month}/{file}
    """
    now = datetime.now()
    upload_path = (
        UPLOAD_DIR /
        str(user_id) /
        str(now.year) /
        f"{now.month:02d}"
    )
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path

async def save_user_file(file: UploadFile, user_id: str) -> str:
    """Save file with organized structure"""
    upload_path = get_upload_path(user_id, "profile_pictures")
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_path / unique_filename

    async with aiofiles.open(file_path, 'wb') as f:
        contents = await file.read()
        await f.write(contents)

    # Return relative path for database storage
    return str(file_path.relative_to(UPLOAD_DIR))
```

### Saving to AWS S3 (Cloud Storage)

```python
import boto3
from botocore.exceptions import ClientError

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id='YOUR_ACCESS_KEY',
    aws_secret_access_key='YOUR_SECRET_KEY',
    region_name='us-east-1'
)

BUCKET_NAME = "my-app-uploads"

async def upload_to_s3(file: UploadFile, object_name: str = None) -> str:
    """
    Upload file to S3 bucket
    Returns: S3 object URL
    """
    if object_name is None:
        object_name = f"{uuid.uuid4()}_{file.filename}"

    try:
        # Upload file
        contents = await file.read()
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=object_name,
            Body=contents,
            ContentType=file.content_type
        )

        # Generate URL
        url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{object_name}"
        return url

    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-s3/")
async def upload_file_to_s3(file: UploadFile = File(...)):
    """Upload file to AWS S3"""
    await validate_upload_file(file)
    url = await upload_to_s3(file)
    return {"filename": file.filename, "url": url}
```

---

## 4. File Download & Streaming

### Basic File Download

```python
from fastapi.responses import FileResponse

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download file from server
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )
```

### Download with Custom Headers

```python
@app.get("/download-custom/{filename}")
async def download_with_headers(filename: str):
    """Download with custom headers"""
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream',
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache"
        }
    )
```

### Streaming Large Files

```python
from fastapi.responses import StreamingResponse
import aiofiles

async def file_iterator(file_path: Path, chunk_size: int = 1024 * 1024):
    """
    Async generator for streaming file in chunks
    """
    async with aiofiles.open(file_path, 'rb') as f:
        while chunk := await f.read(chunk_size):
            yield chunk

@app.get("/stream/{filename}")
async def stream_file(filename: str):
    """
    Stream large file in chunks
    Better for large files to avoid memory issues
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return StreamingResponse(
        file_iterator(file_path),
        media_type='application/octet-stream',
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
```

### Streaming with Progress Support (Range Requests)

```python
from fastapi import Request
import os

@app.get("/stream-range/{filename}")
async def stream_with_range(filename: str, request: Request):
    """
    Stream file with HTTP Range support (for resumable downloads)
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range")

    if range_header:
        # Parse range header
        byte_range = range_header.replace("bytes=", "").split("-")
        start = int(byte_range[0])
        end = int(byte_range[1]) if byte_range[1] else file_size - 1

        async def ranged_file_iterator():
            async with aiofiles.open(file_path, 'rb') as f:
                await f.seek(start)
                remaining = end - start + 1
                while remaining > 0:
                    chunk_size = min(1024 * 1024, remaining)
                    chunk = await f.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        return StreamingResponse(
            ranged_file_iterator(),
            status_code=206,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(end - start + 1),
            }
        )

    # No range, return full file
    return FileResponse(file_path)
```

### Image Download/Display

```python
@app.get("/images/{filename}")
async def get_image(filename: str):
    """
    Serve image file with proper content type
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    # Detect image type
    ext = os.path.splitext(filename)[1].lower()
    media_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }

    media_type = media_types.get(ext, 'application/octet-stream')

    return FileResponse(
        path=file_path,
        media_type=media_type
    )
```

---

## 5. Image Processing with Pillow

### Installing Pillow

```bash
pip install Pillow
```

### Basic Image Processing

```python
from PIL import Image
import io

async def process_image(file: UploadFile) -> bytes:
    """
    Basic image processing: resize and optimize
    """
    # Read uploaded file
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    # Convert to RGB (removes alpha channel)
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Resize image (maintain aspect ratio)
    max_size = (800, 800)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Save to bytes
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=85, optimize=True)
    output.seek(0)

    return output.getvalue()

@app.post("/upload-process-image/")
async def upload_and_process_image(file: UploadFile = File(...)):
    """Upload and process image"""
    await validate_image_file(file)
    processed_image = await process_image(file)

    # Save processed image
    file_path = UPLOAD_DIR / f"{uuid.uuid4()}.jpg"
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(processed_image)

    return {"message": "Image processed and saved", "path": str(file_path)}
```

### Create Thumbnails

```python
async def create_thumbnail(
    file: UploadFile,
    size: tuple = (150, 150)
) -> bytes:
    """
    Create thumbnail from uploaded image
    """
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    # Create thumbnail (crops to square)
    image.thumbnail(size, Image.Resampling.LANCZOS)

    # Save to bytes
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=85)
    output.seek(0)

    return output.getvalue()

async def save_with_thumbnail(file: UploadFile, user_id: str):
    """
    Save original image and thumbnail
    """
    # Save original
    upload_path = get_upload_path(user_id, "profile_pictures")
    original_filename = f"{uuid.uuid4()}.jpg"
    original_path = upload_path / original_filename

    processed_image = await process_image(file)
    async with aiofiles.open(original_path, 'wb') as f:
        await f.write(processed_image)

    # Reset file pointer
    await file.seek(0)

    # Create and save thumbnail
    thumbnail_filename = f"{uuid.uuid4()}_thumb.jpg"
    thumbnail_path = upload_path / thumbnail_filename

    thumbnail_image = await create_thumbnail(file)
    async with aiofiles.open(thumbnail_path, 'wb') as f:
        await f.write(thumbnail_image)

    return {
        "original": str(original_path.relative_to(UPLOAD_DIR)),
        "thumbnail": str(thumbnail_path.relative_to(UPLOAD_DIR))
    }
```

### Image Format Conversion

```python
async def convert_to_webp(file: UploadFile) -> bytes:
    """
    Convert image to WebP format for better compression
    """
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    # Convert to RGB
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Save as WebP
    output = io.BytesIO()
    image.save(output, format='WEBP', quality=85, method=6)
    output.seek(0)

    return output.getvalue()
```

### Add Watermark

```python
from PIL import ImageDraw, ImageFont

async def add_watermark(file: UploadFile, text: str = "© MyApp") -> bytes:
    """
    Add watermark to image
    """
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    # Create drawing context
    draw = ImageDraw.Draw(image)

    # Get image size
    width, height = image.size

    # Create watermark text
    try:
        font = ImageFont.truetype("Arial.ttf", 36)
    except:
        font = ImageFont.load_default()

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Position watermark (bottom right)
    x = width - text_width - 20
    y = height - text_height - 20

    # Draw semi-transparent watermark
    draw.text(
        (x, y),
        text,
        fill=(255, 255, 255, 128),
        font=font
    )

    # Save to bytes
    output = io.BytesIO()
    image.save(output, format='PNG')
    output.seek(0)

    return output.getvalue()
```

### Image Validation with Pillow

```python
async def validate_and_get_image_info(file: UploadFile) -> dict:
    """
    Validate image and get detailed information
    """
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Validate image
        image.verify()

        # Re-open for getting info (verify() closes the file)
        image = Image.open(io.BytesIO(contents))

        return {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "width": image.width,
            "height": image.height,
            "is_animated": getattr(image, "is_animated", False),
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image file: {str(e)}"
        )
```

---

## 6. Practice Assignment

### Task: Create Profile Picture Upload Endpoint

Build a complete profile picture upload system with the following features:

#### Requirements:

1. **Upload Endpoint** (`POST /users/me/profile-picture`)
   - Accept image file upload
   - Validate file type (JPEG, PNG only)
   - Validate file size (max 5MB)
   - Require user authentication

2. **Image Processing**
   - Resize to max 1000x1000 (maintain aspect ratio)
   - Create thumbnail (200x200)
   - Convert to JPEG format
   - Optimize quality (85%)

3. **Storage**
   - Save original processed image
   - Save thumbnail
   - Store file paths in database (User model)
   - Organize by user ID

4. **Download Endpoint** (`GET /users/{user_id}/profile-picture`)
   - Return user's profile picture
   - Support query parameter `size=thumbnail` or `size=full`
   - Return 404 if no picture exists

5. **Delete Endpoint** (`DELETE /users/me/profile-picture`)
   - Delete profile picture files
   - Update database
   - Require authentication

#### Database Schema Addition:

```python
# Add to User model
profile_picture_url = Column(String(500), nullable=True)
profile_picture_thumbnail_url = Column(String(500), nullable=True)
```

#### Expected API Behavior:

```bash
# Upload profile picture
curl -X POST "http://localhost:8000/users/me/profile-picture" \
  -H "Authorization: Bearer {token}" \
  -F "file=@profile.jpg"

# Response
{
  "message": "Profile picture uploaded successfully",
  "profile_picture_url": "users/123/2024/01/abc-123.jpg",
  "thumbnail_url": "users/123/2024/01/abc-123_thumb.jpg"
}

# Get profile picture (full size)
curl "http://localhost:8000/users/123/profile-picture?size=full"

# Get profile picture (thumbnail)
curl "http://localhost:8000/users/123/profile-picture?size=thumbnail"

# Delete profile picture
curl -X DELETE "http://localhost:8000/users/me/profile-picture" \
  -H "Authorization: Bearer {token}"
```

#### Bonus Challenges:

1. Add image rotation correction (handle EXIF orientation)
2. Implement image cropping to exact square
3. Add support for animated GIFs
4. Implement CDN URL generation
5. Add rate limiting (max 5 uploads per hour)
6. Create image compression pipeline with multiple sizes
7. Add virus scanning before processing

---

## 7. Best Practices

### Security

1. **Always Validate Files**
   - Check file size
   - Validate MIME type
   - Verify file extension
   - Use magic bytes validation

2. **Sanitize Filenames**

   ```python
   import re

   def sanitize_filename(filename: str) -> str:
       # Remove dangerous characters
       filename = re.sub(r'[^\w\s.-]', '', filename)
       # Remove path separators
       filename = filename.replace('/', '').replace('\\', '')
       return filename
   ```

3. **Store Files Outside Web Root**
   - Don't serve files directly from upload directory
   - Use separate endpoint to serve files
   - Implement access control

4. **Scan for Malware**

   ```python
   import clamd

   async def scan_file(file_path: str):
       cd = clamd.ClamdUnixSocket()
       scan_result = cd.scan(file_path)
       # Check scan_result for viruses
   ```

### Performance

1. **Use Async I/O**
   - Use `aiofiles` for file operations
   - Use async methods for UploadFile

2. **Stream Large Files**
   - Don't load entire file into memory
   - Process in chunks

3. **Implement Caching**

   ```python
   from fastapi import Response

   @app.get("/images/{filename}")
   async def get_image_cached(filename: str):
       return FileResponse(
           path=file_path,
           headers={
               "Cache-Control": "public, max-age=31536000",
               "ETag": generate_etag(file_path)
           }
       )
   ```

4. **Use Background Tasks for Processing**

   ```python
   from fastapi import BackgroundTasks

   def process_image_background(file_path: str):
       # Heavy processing here
       pass

   @app.post("/upload/")
   async def upload(
       file: UploadFile,
       background_tasks: BackgroundTasks
   ):
       file_path = await save_file_to_disk(file)
       background_tasks.add_task(process_image_background, file_path)
       return {"message": "Upload started"}
   ```

### Storage Management

1. **Implement File Cleanup**

   ```python
   import asyncio
   from datetime import datetime, timedelta

   async def cleanup_old_files():
       """Remove files older than 30 days"""
       cutoff = datetime.now() - timedelta(days=30)
       for file_path in UPLOAD_DIR.rglob('*'):
           if file_path.is_file():
               mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
               if mtime < cutoff:
                   file_path.unlink()
   ```

2. **Monitor Disk Usage**

   ```python
   import shutil

   def get_disk_usage():
       total, used, free = shutil.disk_usage(UPLOAD_DIR)
       return {
           "total_gb": total / (1024**3),
           "used_gb": used / (1024**3),
           "free_gb": free / (1024**3),
           "usage_percent": (used / total) * 100
       }
   ```

3. **Use Content Deduplication**

   ```python
   import hashlib

   async def get_file_hash(file: UploadFile) -> str:
       """Calculate file hash to detect duplicates"""
       sha256 = hashlib.sha256()
       while chunk := await file.read(8192):
           sha256.update(chunk)
       await file.seek(0)
       return sha256.hexdigest()
   ```

### Error Handling

```python
from fastapi import status

@app.post("/upload/")
async def upload_with_error_handling(file: UploadFile = File(...)):
    try:
        # Validate file
        await validate_upload_file(file)

        # Save file
        file_path = await save_file_to_disk(file)

        return {"filename": file.filename, "path": file_path}

    except HTTPException:
        raise
    except Exception as e:
        # Log error
        print(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading file"
        )
```

---

## Key Takeaways

1. ✅ **UploadFile** is the preferred way to handle file uploads in FastAPI
2. ✅ Always **validate** file size, type, and content before processing
3. ✅ Use **async I/O** with `aiofiles` for better performance
4. ✅ **Stream large files** in chunks to avoid memory issues
5. ✅ Use **Pillow** for image processing, resizing, and optimization
6. ✅ Implement **proper security** measures (validation, sanitization, scanning)
7. ✅ Store files with **organized structure** (by user, date, type)
8. ✅ Use **FileResponse** for downloads and **StreamingResponse** for large files
9. ✅ Implement **background tasks** for heavy processing
10. ✅ Monitor and manage **storage** to prevent exhaustion

---

## Additional Resources

- [FastAPI File Upload Docs](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [aiofiles GitHub](https://github.com/Tinche/aiofiles)
- [AWS S3 boto3 Docs](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3.html)
- [Starlette UploadFile](https://www.starlette.io/requests/#request-files)

---

**Created:** February 6, 2026  
**Duration:** 1 hour  
**Topics Covered:** File Upload, Validation, Storage, Download, Streaming, Image Processing
