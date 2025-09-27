#!/usr/bin/env python3
"""
Debug CORS issues between frontend and backend
"""

import subprocess
import json
import time

def test_cors_preflight():
    """Test CORS preflight request"""
    print("🔍 Testing CORS preflight request...")

    cmd = [
        'curl', '-X', 'OPTIONS',
        '-H', 'Origin: http://localhost:5173',
        '-H', 'Access-Control-Request-Method: POST',
        '-H', 'Access-Control-Request-Headers: content-type',
        '-v', 'http://localhost:5000/config/test-ollama'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        print(f"Status: {result.returncode}")
        print("\n📤 Request Headers:")
        for line in result.stderr.split('\n'):
            if line.startswith('> '):
                print(f"  {line}")

        print("\n📥 Response Headers:")
        cors_headers = {}
        for line in result.stderr.split('\n'):
            if line.startswith('< '):
                print(f"  {line}")
                if 'access-control' in line.lower():
                    parts = line[2:].split(': ', 1)
                    if len(parts) == 2:
                        cors_headers[parts[0]] = parts[1]

        print(f"\n✅ CORS Headers Found: {len(cors_headers)}")
        for header, value in cors_headers.items():
            print(f"  {header}: {value}")

        return cors_headers

    except subprocess.TimeoutExpired:
        print("❌ Request timed out - backend might not be running")
        return {}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

def test_actual_post():
    """Test actual POST request"""
    print("\n🔍 Testing actual POST request...")

    cmd = [
        'curl', '-X', 'POST',
        '-H', 'Origin: http://localhost:5173',
        '-H', 'Content-Type: application/json',
        '-d', '{"ollama_url": "http://localhost:11434"}',
        '-v', 'http://localhost:5000/config/test-ollama'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        print(f"Status: {result.returncode}")

        if result.stdout:
            try:
                response = json.loads(result.stdout)
                print(f"✅ Response: {response.get('success', False)}")
                if response.get('success'):
                    print(f"  Models: {response.get('total_models', 0)}")
                else:
                    print(f"  Error: {response.get('error', 'Unknown')}")
            except json.JSONDecodeError:
                print(f"Response: {result.stdout[:100]}...")

        # Check for CORS headers in response
        print("\n📥 Response CORS Headers:")
        for line in result.stderr.split('\n'):
            if 'access-control' in line.lower() and line.startswith('< '):
                print(f"  {line}")

    except subprocess.TimeoutExpired:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

def check_backend_status():
    """Check if backend is running"""
    print("🔍 Checking backend status...")

    try:
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:5000/api/v1/ping'],
            capture_output=True, text=True, timeout=5
        )

        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                print(f"✅ Backend is running: {response.get('message', 'OK')}")
                return True
            except json.JSONDecodeError:
                print("⚠️ Backend responding but not JSON")
                return True
        else:
            print("❌ Backend not responding")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Backend timeout")
        return False
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False

if __name__ == "__main__":
    print("🧪 CORS Debug Tool")
    print("=" * 50)

    # Check backend first
    if not check_backend_status():
        print("\n💡 Please start the backend first:")
        print("   python web_app.py")
        exit(1)

    print("\n" + "=" * 50)

    # Test preflight
    cors_headers = test_cors_preflight()

    print("\n" + "=" * 50)

    # Test actual request
    test_actual_post()

    print("\n" + "=" * 50)

    # Analysis
    print("📊 Analysis:")

    required_headers = [
        'Access-Control-Allow-Origin',
        'Access-Control-Allow-Methods',
        'Access-Control-Allow-Headers'
    ]

    missing_headers = []
    for header in required_headers:
        if header not in cors_headers:
            missing_headers.append(header)

    if missing_headers:
        print(f"❌ Missing CORS headers: {missing_headers}")
        print("💡 Backend needs to be restarted to apply CORS changes")
    else:
        print("✅ All required CORS headers present")
        print("💡 If browser still shows CORS errors:")
        print("   1. Clear browser cache/hard refresh (Ctrl+Shift+R)")
        print("   2. Check browser dev tools Network tab for exact error")
        print("   3. Ensure frontend is making requests to correct URL")