#!/usr/bin/env python3
"""
Test Setup Verification Script
Verifies that all dependencies and configurations are ready for fullstack testing
"""

import os
import sys
import subprocess
from typing import List, Tuple


class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def check_python_version() -> Tuple[bool, str]:
    """Check Python version"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    return False, f"Python {version.major}.{version.minor} (requires 3.8+)"


def check_module(module_name: str) -> Tuple[bool, str]:
    """Check if a Python module is installed"""
    try:
        __import__(module_name)
        return True, f"{module_name} installed"
    except ImportError:
        return False, f"{module_name} not found"


def check_firebase_config() -> Tuple[bool, str]:
    """Check if Firebase configuration exists"""
    env_file = ".env"
    if not os.path.exists(env_file):
        return False, f"{env_file} not found"

    required_vars = [
        "FIREBASE_PROJECT_ID",
        "FIREBASE_API_KEY",
    ]

    with open(env_file, 'r') as f:
        content = f.read()

    missing = [var for var in required_vars if var not in content]

    if missing:
        return False, f"Missing vars: {', '.join(missing)}"

    return True, "Firebase config found in .env"


def check_firebase_service() -> Tuple[bool, str]:
    """Check if unified Firebase service is accessible"""
    try:
        sys.path.insert(0, os.path.abspath('.'))
        from src.services.unified_firebase_service import unified_firebase_service

        status = unified_firebase_service.get_status()
        if status.get('configured'):
            client_type = status.get('client_type', 'unknown')
            return True, f"Firebase service configured ({client_type})"
        else:
            return False, "Firebase service not configured"
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"


def check_node_installed() -> Tuple[bool, str]:
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, f"Node.js {version}"
        return False, "Node.js not working"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "Node.js not found"


def check_npm_installed() -> Tuple[bool, str]:
    """Check if npm is installed"""
    try:
        result = subprocess.run(
            ['npm', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, f"npm {version}"
        return False, "npm not working"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "npm not found"


def check_platform_dependencies() -> Tuple[bool, str]:
    """Check if platform dependencies are installed"""
    node_modules = "platform/node_modules"
    if os.path.exists(node_modules):
        return True, "Platform dependencies installed"
    return False, "Run 'npm install' in platform/"


def check_playwright() -> Tuple[bool, str]:
    """Check if Playwright is installed"""
    playwright_path = "platform/node_modules/@playwright/test"
    if os.path.exists(playwright_path):
        return True, "Playwright installed"
    return False, "Run 'npx playwright install' in platform/"


def check_firebase_emulators() -> Tuple[bool, str]:
    """Check if Firebase emulators are available"""
    try:
        result = subprocess.run(
            ['firebase', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, f"Firebase CLI {version}"
        return False, "Firebase CLI not working"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "Firebase CLI not found (optional)"


def print_check(name: str, passed: bool, message: str):
    """Print a check result"""
    status = f"{Colors.GREEN}✓{Colors.NC}" if passed else f"{Colors.RED}✗{Colors.NC}"
    color = Colors.GREEN if passed else Colors.RED
    print(f"{status} {name:.<40} {color}{message}{Colors.NC}")


def main():
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}Locrits Fullstack Test Setup Verification{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}\n")

    checks: List[Tuple[str, Tuple[bool, str]]] = []

    print(f"{Colors.YELLOW}Python Environment{Colors.NC}")
    print("-" * 60)
    checks.append(("Python Version", check_python_version()))
    checks.append(("pytest", check_module("pytest")))
    checks.append(("pytest-asyncio", check_module("pytest_asyncio")))
    checks.append(("Firebase Admin SDK", check_module("firebase_admin")))
    print()

    print(f"{Colors.YELLOW}Firebase Configuration{Colors.NC}")
    print("-" * 60)
    checks.append(("Firebase Config (.env)", check_firebase_config()))
    checks.append(("Firebase Service", check_firebase_service()))
    print()

    print(f"{Colors.YELLOW}Node.js Environment{Colors.NC}")
    print("-" * 60)
    checks.append(("Node.js", check_node_installed()))
    checks.append(("npm", check_npm_installed()))
    checks.append(("Platform Dependencies", check_platform_dependencies()))
    checks.append(("Playwright", check_playwright()))
    print()

    print(f"{Colors.YELLOW}Optional Tools{Colors.NC}")
    print("-" * 60)
    checks.append(("Firebase CLI (Emulators)", check_firebase_emulators()))
    print()

    # Print all checks
    for name, (passed, message) in checks:
        print_check(name, passed, message)

    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    passed_count = sum(1 for _, (passed, _) in checks if passed)
    total_count = len(checks)

    if passed_count == total_count:
        print(f"{Colors.GREEN}✓ All checks passed! ({passed_count}/{total_count}){Colors.NC}")
        print(f"{Colors.GREEN}You're ready to run the fullstack tests!{Colors.NC}")
        print(f"\n{Colors.BLUE}Run tests with:{Colors.NC}")
        print(f"  ./run_fullstack_tests.sh")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠ {passed_count}/{total_count} checks passed{Colors.NC}")
        print(f"\n{Colors.YELLOW}Fix the failed checks above to run tests.{Colors.NC}")

        # Print installation commands for missing items
        print(f"\n{Colors.BLUE}Quick fixes:{Colors.NC}")

        for name, (passed, _) in checks:
            if not passed:
                if name == "pytest":
                    print(f"  pip install pytest")
                elif name == "pytest-asyncio":
                    print(f"  pip install pytest-asyncio")
                elif name == "Firebase Admin SDK":
                    print(f"  pip install firebase-admin")
                elif name == "Platform Dependencies":
                    print(f"  cd platform && npm install")
                elif name == "Playwright":
                    print(f"  cd platform && npx playwright install")
                elif name == "Firebase CLI (Emulators)":
                    print(f"  npm install -g firebase-tools")

        return 1


if __name__ == "__main__":
    sys.exit(main())
