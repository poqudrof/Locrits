#!/usr/bin/env python3
"""
Simple command-line chat client for Locrit HTTP API
Usage: python chat_client.py [locrit_name]
"""

import requests
import sys
import json
from urllib.parse import quote

BASE_URL = "http://localhost:5000"

def get_available_locrits():
    """Get list of available Locrits"""
    try:
        response = requests.get(f"{BASE_URL}/api/locrits")
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'locrits' in data:
                return list(data['locrits']['instances'].keys())
        return []
    except:
        return []

def send_message(locrit_name, message):
    """Send a message to the specified Locrit"""
    try:
        encoded_name = quote(locrit_name)
        payload = {"message": message}

        response = requests.post(
            f"{BASE_URL}/api/locrits/{encoded_name}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return True, data.get('response', '')
            else:
                return False, data.get('error', 'Unknown error')
        else:
            try:
                error_data = response.json()
                return False, error_data.get('error', f'HTTP {response.status_code}')
            except:
                return False, f'HTTP {response.status_code}'

    except requests.exceptions.RequestException as e:
        return False, str(e)

def main():
    """Main chat loop"""
    # Check command line arguments
    if len(sys.argv) > 1:
        locrit_name = sys.argv[1]
    else:
        # Get available Locrits
        locrits = get_available_locrits()
        if not locrits:
            print("❌ No Locrits available or API server not running")
            print("Make sure the Flask server is running on http://localhost:5000")
            return

        print("Available Locrits:")
        for i, name in enumerate(locrits, 1):
            print(f"  {i}. {name}")

        try:
            choice = int(input("\nSelect a Locrit (number): ")) - 1
            if 0 <= choice < len(locrits):
                locrit_name = locrits[choice]
            else:
                print("Invalid selection")
                return
        except (ValueError, KeyboardInterrupt):
            print("\nExiting...")
            return

    print(f"\n🤖 Starting chat with '{locrit_name}'")
    print("Type 'quit' or 'exit' to end the conversation")
    print("=" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break

            if not user_input:
                continue

            print("🤖 Thinking...")
            success, response = send_message(locrit_name, user_input)

            if success:
                print(f"{locrit_name}: {response}")
            else:
                print(f"❌ Error: {response}")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            break

if __name__ == "__main__":
    main()