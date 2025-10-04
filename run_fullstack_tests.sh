#!/bin/bash
# Fullstack Integration Test Runner
# This script runs both Python backend and React platform tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Locrits Fullstack Integration Test Suite           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we should use Firebase emulators
USE_EMULATORS=${USE_FIREBASE_EMULATOR:-false}

if [ "$USE_EMULATORS" = "true" ]; then
    echo -e "${YELLOW}🔧 Using Firebase Emulators${NC}"
    export FIRESTORE_EMULATOR_HOST="localhost:8080"
    export FIREBASE_AUTH_EMULATOR_HOST="localhost:9099"

    # Check if emulators are running
    if ! nc -z localhost 8080 2>/dev/null; then
        echo -e "${RED}❌ Firebase emulators not running!${NC}"
        echo -e "${YELLOW}Start emulators with: firebase emulators:start${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Firebase emulators detected${NC}"
else
    echo -e "${YELLOW}⚠️  Using production Firebase (not emulators)${NC}"
    echo -e "${YELLOW}   Set USE_FIREBASE_EMULATOR=true to use emulators${NC}"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}1️⃣  Running Python Backend Tests${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found. Installing...${NC}"
    pip install pytest pytest-asyncio
fi

# Run Python tests
echo -e "${YELLOW}Running backend integration tests...${NC}"
export FIREBASE_TEST_USE_ANONYMOUS=true

if python -m pytest src/tests/test_fullstack_locrit_flow.py -v -s --tb=short; then
    echo -e "${GREEN}✓ Backend tests passed!${NC}"
    BACKEND_PASSED=true
else
    echo -e "${RED}✗ Backend tests failed!${NC}"
    BACKEND_PASSED=false
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}2️⃣  Checking Platform Development Server${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if platform dev server is running
if nc -z localhost 5173 2>/dev/null; then
    echo -e "${GREEN}✓ Platform dev server is running${NC}"
    SERVER_RUNNING=true
else
    echo -e "${YELLOW}⚠️  Platform dev server not detected on port 5173${NC}"
    echo -e "${YELLOW}   Starting server...${NC}"

    cd platform

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing platform dependencies...${NC}"
        npm install
    fi

    # Start dev server in background
    npm run dev > /dev/null 2>&1 &
    DEV_SERVER_PID=$!

    echo -e "${YELLOW}Waiting for server to start...${NC}"
    for i in {1..30}; do
        if nc -z localhost 5173 2>/dev/null; then
            echo -e "${GREEN}✓ Platform dev server started (PID: $DEV_SERVER_PID)${NC}"
            SERVER_RUNNING=true
            STARTED_SERVER=true
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""

    if [ "$SERVER_RUNNING" != "true" ]; then
        echo -e "${RED}✗ Failed to start platform dev server${NC}"
        exit 1
    fi

    cd ..
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}3️⃣  Running Platform E2E Tests${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd platform

# Check if Playwright is installed
if [ ! -d "node_modules/@playwright/test" ]; then
    echo -e "${YELLOW}Installing Playwright...${NC}"
    npm install @playwright/test
    npx playwright install
fi

# Run E2E tests
echo -e "${YELLOW}Running platform E2E tests...${NC}"

if npx playwright test e2e/fullstack-locrit-review.spec.ts; then
    echo -e "${GREEN}✓ Platform E2E tests passed!${NC}"
    E2E_PASSED=true
else
    echo -e "${RED}✗ Platform E2E tests failed!${NC}"
    E2E_PASSED=false
fi

cd ..

# Cleanup
if [ "$STARTED_SERVER" = "true" ]; then
    echo ""
    echo -e "${YELLOW}Stopping dev server (PID: $DEV_SERVER_PID)...${NC}"
    kill $DEV_SERVER_PID 2>/dev/null || true
    echo -e "${GREEN}✓ Dev server stopped${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📊 Test Results Summary${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$BACKEND_PASSED" = "true" ]; then
    echo -e "${GREEN}✓ Backend Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Backend Tests: FAILED${NC}"
fi

if [ "$E2E_PASSED" = "true" ]; then
    echo -e "${GREEN}✓ Platform E2E Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Platform E2E Tests: FAILED${NC}"
fi

echo ""

if [ "$BACKEND_PASSED" = "true" ] && [ "$E2E_PASSED" = "true" ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              🎉 ALL TESTS PASSED! 🎉                    ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║              ❌ SOME TESTS FAILED ❌                     ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
