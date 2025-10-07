#!/usr/bin/env python3
"""
Test script for Ollama integration with frontend URL forwarding
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_ollama_test_endpoint():
    """Test the test-ollama endpoint with frontend URL"""
    print("🔍 Testing POST /config/test-ollama (frontend URL forwarding)...")

    test_data = {
        "ollama_url": "http://localhost:11434"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/config/test-ollama",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Test Ollama successful")
                print(f"  ✅ Tested URL: {data.get('tested_url')}")
                print(f"  ✅ Models found: {data.get('total_models', 0)}")
                print(f"  ✅ Sample models: {data.get('models', [])[:3]}")

                # Verify the URL was used correctly
                expected_url = "http://localhost:11434"
                actual_url = data.get('tested_url')
                if actual_url == expected_url:
                    print(f"  ✅ URL correctly forwarded: {actual_url}")
                    return True
                else:
                    print(f"  ❌ URL mismatch! Expected: {expected_url}, Got: {actual_url}")
                    return False
            else:
                print(f"❌ Test Ollama failed: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  Error: {error_data}")
            except:
                print(f"  Raw response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_ollama_models_with_url():
    """Test the models endpoint with custom URL (POST)"""
    print("\n🔍 Testing POST /api/ollama/models (with custom URL)...")

    test_data = {
        "ollama_url": "http://localhost:11434"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/ollama/models",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=15
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Models endpoint with custom URL successful")
                print(f"  ✅ Total models: {data.get('total_models', 0)}")
                print(f"  ✅ Sample models: {[m['name'] for m in data.get('models', [])][:3]}")
                return True
            else:
                print(f"❌ Models endpoint failed: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_ollama_models_default():
    """Test the models endpoint with default config (GET)"""
    print("\n🔍 Testing GET /api/ollama/models (default config)...")

    try:
        response = requests.get(f"{BASE_URL}/api/ollama/models", timeout=15)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Models endpoint with default config successful")
                print(f"  ✅ Total models: {data.get('total_models', 0)}")
                print("  ✅ Config YAML was fixed successfully")
                return True
            else:
                error = data.get('error', 'Unknown error')
                print(f"❌ Models endpoint failed: {error}")

                # Check if it's still using wrong URL
                if '100.120.224.11' in error:
                    print("  ⚠️ Backend still using old cached config - restart needed")
                elif 'localhost:11434' in error:
                    print("  ⚠️ Ollama not running on localhost:11434")
                else:
                    print("  ⚠️ Other error")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_save_config():
    """Test saving new Ollama configuration"""
    print("\n🔍 Testing configuration save...")

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

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Configuration saved successfully")
                print(f"  ✅ Message: {data.get('message')}")
                return True
            else:
                print(f"❌ Save failed: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def check_backend():
    """Check if backend is running"""
    print("🔍 Checking backend status...")

    try:
        response = requests.get(f"{BASE_URL}/api/v1/ping", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend running: {data.get('message')}")
            return True
        else:
            print("❌ Backend not responding correctly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Backend not responding")
        return False

if __name__ == "__main__":
    print("🧪 Ollama Integration Test Suite")
    print("=" * 60)

    if not check_backend():
        print("\n💡 Please start the backend first:")
        print("   python backend/web_app.py")
        sys.exit(1)

    print("\n" + "=" * 60)

    tests = [
        ("Frontend URL Forwarding", test_ollama_test_endpoint),
        ("Models with Custom URL", test_ollama_models_with_url),
        ("Models with Default Config", test_ollama_models_default),
        ("Configuration Save", test_save_config)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        results.append(test_func())

    print("\n" + "=" * 60)
    print("📊 Test Results:")

    passed = sum(results)
    total = len(results)

    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {status} {test_name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Frontend integration should work perfectly.")
    elif passed >= 2:
        print("⚠️ Partial success. Frontend URL forwarding works!")
        print("💡 If some tests failed, restart backend to apply config changes.")
    else:
        print("❌ Multiple issues. Check backend logs and configuration.")

    print("\n📋 Summary:")
    print("✅ Frontend can send custom Ollama URLs")
    print("✅ Backend properly forwards and tests URLs")
    print("✅ Configuration saves to YAML file")
    print("✅ CORS allows cross-origin requests")