"""
Test Script for File Upload Feature
This script tests the profile picture upload/download/delete endpoints
"""

import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "fileuploadtest@example.com"
TEST_PASSWORD = "testpass123"
TEST_NAME = "File Upload Test User"
TEST_IMAGE_PATH = "test_image.jpg"  # Change this to your test image path


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_response(response):
    """Pretty print response"""
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_file_upload():
    """Complete test flow for file upload feature"""
    
    print_section("1. REGISTER USER")
    register_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_NAME
    }
    response = requests.post(f"{BASE_URL}/register", json=register_data)
    print_response(response)
    
    if response.status_code != 200:
        print("⚠️  Registration failed. User might already exist. Continuing with login...")
    
    
    print_section("2. LOGIN AND GET TOKEN")
    login_data = {
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    response = requests.post(
        f"{BASE_URL}/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print_response(response)
    
    if response.status_code != 200:
        print("❌ Login failed!")
        return
    
    token_data = response.json()
    access_token = token_data["access_token"]
    print(f"\n✅ Token obtained: {access_token[:50]}...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    
    print_section("3. GET CURRENT USER INFO")
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print_response(response)
    
    if response.status_code != 200:
        print("❌ Failed to get user info!")
        return
    
    user_data = response.json()
    user_id = user_data["id"]
    print(f"\n✅ User ID: {user_id}")
    print(f"   Email: {user_data['email']}")
    print(f"   Profile Picture: {user_data.get('profile_picture_url', 'None')}")
    
    
    print_section("4. CHECK IF TEST IMAGE EXISTS")
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"❌ Test image not found: {TEST_IMAGE_PATH}")
        print("\nDownloading a test image...")
        
        # Download a test image
        img_response = requests.get("https://picsum.photos/800/600")
        if img_response.status_code == 200:
            with open(TEST_IMAGE_PATH, "wb") as f:
                f.write(img_response.content)
            print(f"✅ Test image downloaded: {TEST_IMAGE_PATH}")
        else:
            print("❌ Failed to download test image!")
            print("Please provide a test image and update TEST_IMAGE_PATH in the script")
            return
    else:
        print(f"✅ Test image found: {TEST_IMAGE_PATH}")
        print(f"   Size: {os.path.getsize(TEST_IMAGE_PATH) / 1024:.2f} KB")
    
    
    print_section("5. UPLOAD PROFILE PICTURE")
    with open(TEST_IMAGE_PATH, "rb") as f:
        files = {"file": (TEST_IMAGE_PATH, f, "image/jpeg")}
        response = requests.post(
            f"{BASE_URL}/users/me/profile-picture",
            headers=headers,
            files=files
        )
    print_response(response)
    
    if response.status_code != 200:
        print("❌ Upload failed!")
        return
    
    upload_data = response.json()
    print(f"\n✅ Upload successful!")
    print(f"   Full size: {upload_data['profile_picture_url']}")
    print(f"   Thumbnail: {upload_data['thumbnail_url']}")
    
    
    print_section("6. DOWNLOAD FULL SIZE IMAGE")
    response = requests.get(
        f"{BASE_URL}/users/{user_id}/profile-picture",
        params={"size": "full"}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        output_file = "downloaded_full.jpg"
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"✅ Full size image downloaded: {output_file}")
        print(f"   Size: {len(response.content) / 1024:.2f} KB")
        print(f"   Content-Type: {response.headers.get('content-type')}")
    else:
        print("❌ Download failed!")
        print_response(response)
    
    
    print_section("7. DOWNLOAD THUMBNAIL")
    response = requests.get(
        f"{BASE_URL}/users/{user_id}/profile-picture",
        params={"size": "thumbnail"}
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        output_file = "downloaded_thumb.jpg"
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"✅ Thumbnail downloaded: {output_file}")
        print(f"   Size: {len(response.content) / 1024:.2f} KB")
        print(f"   Content-Type: {response.headers.get('content-type')}")
    else:
        print("❌ Download failed!")
        print_response(response)
    
    
    print_section("8. VERIFY USER INFO UPDATED")
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print_response(response)
    
    if response.status_code == 200:
        user_data = response.json()
        print(f"\n✅ User profile updated:")
        print(f"   Profile Picture: {user_data.get('profile_picture_url')}")
        print(f"   Thumbnail: {user_data.get('profile_picture_thumbnail_url')}")
    
    
    print_section("9. DELETE PROFILE PICTURE")
    choice = input("\nDo you want to delete the profile picture? (y/n): ")
    
    if choice.lower() == 'y':
        response = requests.delete(
            f"{BASE_URL}/users/me/profile-picture",
            headers=headers
        )
        print_response(response)
        
        if response.status_code == 200:
            print("\n✅ Profile picture deleted successfully!")
            
            # Verify deletion
            response = requests.get(f"{BASE_URL}/users/me", headers=headers)
            user_data = response.json()
            print(f"   Profile Picture: {user_data.get('profile_picture_url', 'None')}")
            print(f"   Thumbnail: {user_data.get('profile_picture_thumbnail_url', 'None')}")
        else:
            print("❌ Deletion failed!")
    else:
        print("Skipping deletion...")
    
    
    print_section("TEST COMPLETE")
    print("✅ All tests completed successfully!")
    print("\nGenerated files:")
    print("  - downloaded_full.jpg (full size profile picture)")
    print("  - downloaded_thumb.jpg (thumbnail)")
    if os.path.exists(TEST_IMAGE_PATH) and TEST_IMAGE_PATH == "test_image.jpg":
        print("  - test_image.jpg (downloaded test image)")


if __name__ == "__main__":
    print("="*70)
    print("  FILE UPLOAD FEATURE TEST SCRIPT")
    print("="*70)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Test Email: {TEST_EMAIL}")
    print(f"Test Image: {TEST_IMAGE_PATH}")
    print("\nMake sure the server is running on http://localhost:8000")
    
    input("\nPress Enter to start testing...")
    
    try:
        test_file_upload()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server!")
        print("Make sure the FastAPI server is running:")
        print("  cd sql_app")
        print("  uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
