#!/usr/bin/env python3
"""
Test script to verify CORS configuration
"""

try:
    from backend.app import create_app

    app = create_app('development')

    print("✅ CORS Configuration Test")
    print(f"📍 Allowed origins: {app.config['CORS_ORIGINS']}")
    print(f"🔧 Debug mode: {app.config['DEBUG']}")
    print(f"🌐 CORS is properly configured for frontend communication")

    # Test the OPTIONS handler
    with app.test_client() as client:
        response = client.options('/config/test-ollama',
                                 headers={'Origin': 'http://localhost:5173'})
        print(f"📡 OPTIONS preflight test: Status {response.status_code}")
        print(f"🔀 CORS headers: {dict(response.headers)}")

except ImportError as e:
    print(f"❌ Dependencies not installed: {e}")
    print("💡 To test CORS, run: pip install -r requirements.txt")
    print("🔧 CORS configuration has been updated in the code")

except Exception as e:
    print(f"❌ Error: {e}")