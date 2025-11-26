"""
AI Recruiting Demo - Full Pipeline Test
Quick test script to verify the complete upload -> analysis -> results flow
"""

import requests
import os
import json
from datetime import datetime
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health():
    """Test if server is running"""
    print_section("1. Server Health Check")
    
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is healthy")
            print(f"   Status: {data.get('status')}")
            print(f"   Time: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ Server returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server not reachable at http://localhost:5000")
        print("   Start server with: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_upload(filename='test-cv.pdf'):
    """Test full upload and analysis pipeline"""
    print_section(f"2. Testing Upload: {filename}")
    
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        print(f"   Current directory: {os.getcwd()}")
        return False
    
    file_size = os.path.getsize(filename)
    print(f"📄 File: {filename}")
    print(f"📊 Size: {file_size} bytes ({file_size/1024:.1f} KB)")
    
    url = 'http://localhost:5000/upload'
    
    print(f"\n📤 Uploading to {url}...")
    start_time = datetime.now()
    
    try:
        with open(filename, 'rb') as f:
            files = {'cv_file': (filename, f, 'application/pdf')}
            response = requests.post(url, files=files, timeout=30)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n⏱️  Response Time: {elapsed:.2f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print("\n✅ UPLOAD & ANALYSIS SUCCESSFUL!")
                print(f"   Redirect URL: {data.get('redirect')}")
                print("\n   📝 Note: Open browser and go to http://localhost:5000")
                print("           Upload the CV there to see the full results page.")
                return True
            else:
                print(f"\n❌ Upload failed: {data.get('error')}")
                return False
        else:
            print(f"\n❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout (>30s)")
        return False
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return False

def test_invalid_file():
    """Test validation with invalid file"""
    print_section("3. Testing Validation (Invalid File)")
    
    # Create a fake PDF file
    fake_pdf = 'fake-test.txt'
    with open(fake_pdf, 'w') as f:
        f.write("This is not a PDF")
    
    print(f"📄 Created fake file: {fake_pdf}")
    
    url = 'http://localhost:5000/upload'
    
    try:
        with open(fake_pdf, 'rb') as f:
            files = {'cv_file': (fake_pdf, f, 'text/plain')}
            response = requests.post(url, files=files, timeout=10)
        
        if response.status_code == 400:
            data = response.json()
            print(f"✅ Validation works! File rejected:")
            print(f"   Error: {data.get('error')}")
            result = True
        else:
            print(f"❌ Expected 400, got {response.status_code}")
            result = False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        result = False
    finally:
        # Cleanup
        if os.path.exists(fake_pdf):
            os.remove(fake_pdf)
            print(f"🗑️  Cleaned up {fake_pdf}")
    
    return result

def main():
    """Run all tests"""
    print("\n")
    print("="*60)
    print("    AI RECRUITING DEMO - PIPELINE TEST")
    print("="*60)
    
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check", test_health()))
    
    if not results[0][1]:
        print("\n❌ Server is not running. Skipping further tests.")
        print("\n💡 Start server with: python app.py")
        return
    
    # Test 2: Valid Upload
    results.append(("Valid Upload", test_upload('test-cv.pdf')))
    
    # Test 3: Invalid File
    results.append(("Invalid File Validation", test_invalid_file()))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print(f"{'='*60}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! MVP is ready for demo! 🚀")
        print("\n📝 Next steps:")
        print("   1. Open browser: http://localhost:5000")
        print("   2. Upload a realistic CV (1-2 pages)")
        print("   3. See the beautiful results page!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    print("\n")

if __name__ == '__main__':
    main()

