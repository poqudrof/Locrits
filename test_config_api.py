#!/usr/bin/env python3
"""
Test script for configuration API endpoints
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_get_config():
    """Test getting current configuration"""
    print("🔍 Testing GET /api/config...")

    try:
        response = requests.get(f"{BASE_URL}/api/config", timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ GET config successful")
                config = data.get('config', {})
                print(f"  Ollama config: {config.get('ollama', {})}")
                return True
            else:
                print(f"❌ GET config failed: {data.get('error')}")
                return False
        else:
            print(f"❌ GET config HTTP error: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ GET config connection error: {e}")
        return False

def test_test_ollama():
    """Test Ollama connection test with custom URL"""
    print("\n🔍 Testing POST /config/test-ollama...")

    test_data = {
        "ollama_url": "http://localhost:11434"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/config/test-ollama",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Test Ollama successful")
                print(f"  Tested URL: {data.get('tested_url')}")
                print(f"  Models found: {data.get('total_models', 0)}")
                return True
            else:
                print(f"❌ Test Ollama failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Test Ollama HTTP error: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Test Ollama connection error: {e}")
        return False

def test_save_config():
    """Test saving configuration"""
    print("\n🔍 Testing POST /api/config/save...")

    save_data = {
        "ollama_base_url": "http://localhost:11434",
        "ollama_default_model": "llama3.1:8b",
        "ollama_timeout": 30
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/config/save",
            json=save_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Save config successful")
                print(f"  Message: {data.get('message')}")
                return True
            else:
                print(f"❌ Save config failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Save config HTTP error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error details: {error_data}")
            except:
                print(f"  Raw response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Save config connection error: {e}")
        return False

def test_cors():
    """Test CORS headers"""
    print("\n🔍 Testing CORS headers...")

    try:
        # Test preflight request
        response = requests.options(
            f"{BASE_URL}/config/test-ollama",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type"
            },
            timeout=5
        )

        cors_headers = {}
        for header, value in response.headers.items():
            if header.lower().startswith('access-control'):
                cors_headers[header] = value

        if cors_headers:
            print("✅ CORS headers present")
            for header, value in cors_headers.items():
                print(f"  {header}: {value}")
            return True
        else:
            print("❌ No CORS headers found")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ CORS test connection error: {e}")
        return False

def check_backend():
    """Check if backend is running"""
    print("🔍 Checking backend status...")

    try:
        response = requests.get(f"{BASE_URL}/api/v1/ping", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is running: {data.get('message')}")
            return True
        else:
            print("❌ Backend not responding correctly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Backend not responding")
        return False

if __name__ == "__main__":
    print("🧪 Configuration API Test Suite")
    print("=" * 50)

    if not check_backend():
        print("\n💡 Please start the backend first:")
        print("   python web_app.py")
        sys.exit(1)

    print("\n" + "=" * 50)

    tests = [
        test_cors,
        test_test_ollama,
        test_get_config,
        test_save_config
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 50)
    print("📊 Test Results:")

    passed = sum(results)
    total = len(results)

    print(f"✅ Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! Frontend integration should work.")
    else:
        print("⚠️ Some tests failed. Check backend logs and restart if needed.")

    print("\n💡 Frontend usage:")
    print("  - GET /api/config - Load current config")
    print("  - POST /config/test-ollama - Test Ollama with custom URL")
    print("  - POST /api/config/save - Save configuration to YAML")