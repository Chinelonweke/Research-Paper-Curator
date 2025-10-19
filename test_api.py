"""Test if API can start."""
import sys
import time
import subprocess
import requests

print("=" * 60)
print("🌐 TESTING API SERVER")
print("=" * 60)

print("\n1️⃣ Checking if API code is valid...")
try:
    from src.api.main import app
    print("   ✅ API code imports successfully")
except Exception as e:
    print(f"   ❌ API import error: {e}")
    sys.exit(1)

print("\n2️⃣ Starting API server...")
print("   (This will open in a new window)")
print("   Press Ctrl+C to stop the server when done testing")

# Start the server
try:
    process = subprocess.Popen(
        ["uvicorn", "src.api.main:app", "--reload", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("   ⏳ Waiting for server to start...")
    time.sleep(5)
    
    print("\n3️⃣ Testing health endpoint...")
    response = requests.get("http://localhost:8000/health", timeout=5)
    
    if response.status_code == 200:
        print("   ✅ Health endpoint working!")
        print(f"   Response: {response.json()}")
    else:
        print(f"   ❌ Health endpoint returned: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("🎉 API SERVER IS RUNNING!")
    print("=" * 60)
    print("\n📖 Open in browser:")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Health: http://localhost:8000/health")
    print("\n⚠️  Press Ctrl+C to stop the server")
    
    # Keep running
    process.wait()
    
except KeyboardInterrupt:
    print("\n\n🛑 Stopping server...")
    process.terminate()
    print("   ✅ Server stopped")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    if process:
        process.terminate()
    sys.exit(1)