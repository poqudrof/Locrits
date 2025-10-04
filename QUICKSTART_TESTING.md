# Fullstack Testing - Quick Start Guide

## TL;DR - Run All Tests

```bash
# 1. Verify setup
python verify_test_setup.py

# 2. Run all tests
./run_fullstack_tests.sh
```

That's it! 🎉

---

## What Gets Tested?

### Backend → Firebase
1. ✅ Push Locrit from Python to Firebase
2. ✅ Update Locrit status
3. ✅ Log activity
4. ✅ Sync data

### Platform Display
1. ✅ Locrit appears in UI
2. ✅ Details display correctly
3. ✅ Can create conversations
4. ✅ Analytics/review works

---

## Files Created

| File | Purpose |
|------|---------|
| `src/tests/test_fullstack_locrit_flow.py` | Python backend tests |
| `platform/e2e/fullstack-locrit-review.spec.ts` | React platform E2E tests |
| `run_fullstack_tests.sh` | Automated test runner |
| `verify_test_setup.py` | Setup verification |
| `FULLSTACK_TESTING.md` | Complete documentation |

---

## Individual Test Commands

### Backend Tests Only
```bash
pytest src/tests/test_fullstack_locrit_flow.py -v -s
```

### Platform E2E Only
```bash
# Terminal 1: Start dev server
cd platform && npm run dev

# Terminal 2: Run E2E tests
cd platform
npx playwright test e2e/fullstack-locrit-review.spec.ts
```

---

## Troubleshooting

### Missing Dependencies?
```bash
python verify_test_setup.py
# Follow the quick fix commands it suggests
```

### Tests Failing?
```bash
# Run in verbose mode
pytest src/tests/test_fullstack_locrit_flow.py -vv -s

# Run Playwright in headed mode (see browser)
cd platform
npx playwright test e2e/fullstack-locrit-review.spec.ts --headed
```

### Clean Up Test Data
```bash
# Check Firebase Console > Firestore
# Look for documents with:
# - name starting with "test-locrit-" or "e2e-test-"
# - tags containing "test" or "e2e-test"
```

---

## Configuration

### Using Firebase Emulators (Optional)
```bash
# Start emulators
firebase emulators:start

# Run tests with emulators
USE_FIREBASE_EMULATOR=true ./run_fullstack_tests.sh
```

### Custom Test Account
```bash
# Set environment variables
export FIREBASE_TEST_EMAIL="test@example.com"
export FIREBASE_TEST_PASSWORD="testpassword123"
export FIREBASE_TEST_USE_ANONYMOUS="false"

# Run tests
./run_fullstack_tests.sh
```

---

## Expected Output

### ✅ Successful Run
```
╔══════════════════════════════════════════════════════════╗
║     Locrits Fullstack Integration Test Suite           ║
╚══════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣  Running Python Backend Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

test_01_firebase_service_configured PASSED
test_02_authenticate_user PASSED
test_03_push_locrit_to_platform PASSED
...

✓ Backend tests passed!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3️⃣  Running Platform E2E Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ✓ should create Locrit in Firebase
  ✓ should display Locrit in platform UI
  ✓ should display correct Locrit details
  ...

✓ Platform E2E tests passed!

╔══════════════════════════════════════════════════════════╗
║              🎉 ALL TESTS PASSED! 🎉                    ║
╚══════════════════════════════════════════════════════════╝
```

---

## What Next?

- ✅ Tests are ready to use
- ✅ Can run in CI/CD (see `FULLSTACK_TESTING.md`)
- ✅ Auto-cleanup test data
- ✅ Comprehensive documentation available

**Happy Testing! 🚀**
