# Fullstack Testing Guide for Locrits Platform

This guide explains how to run the fullstack integration tests that verify the complete flow from Python backend to React platform.

## Overview

The fullstack tests cover:
1. **Backend Tests** (`src/tests/test_fullstack_locrit_flow.py`): Tests pushing Locrits from Python backend to Firebase
2. **Platform E2E Tests** (`platform/e2e/fullstack-locrit-review.spec.ts`): Tests reviewing Locrits in the React platform

## Prerequisites

### Python Backend
- Python 3.8+
- pytest and pytest-asyncio installed
- Firebase credentials configured in `.env`

### React Platform
- Node.js 18+
- Playwright installed
- Firebase project configured

## Test Setup

### 1. Firebase Configuration

The tests use the real Firebase credentials from your configuration:

**Python Backend** (`.env`):
```env
FIREBASE_PROJECT_ID=locrit
FIREBASE_API_KEY=AIzaSyCIhMEWcFKzCeMvkFG2uxvEbmS5m6qUhiI
# ... other Firebase config
```

**React Platform** (`platform/src/firebase/config.ts`):
```typescript
const firebaseConfig = {
  apiKey: "AIzaSyCIhMEWcFKzCeMvkFG2uxvEbmS5m6qUhiI",
  projectId: "locrit",
  // ... other config
};
```

### 2. Test User Account

The tests can use either:
- **Anonymous Authentication** (default, recommended for testing)
- **Email/Password Authentication** (optional)

To use a specific test account, set these environment variables:
```bash
export FIREBASE_TEST_EMAIL="test@example.com"
export FIREBASE_TEST_PASSWORD="testpassword123"
export FIREBASE_TEST_USE_ANONYMOUS="false"
```

For anonymous auth (default):
```bash
export FIREBASE_TEST_USE_ANONYMOUS="true"
```

## Running the Tests

### Python Backend Tests

#### Install Dependencies
```bash
cd /mnt/storage/repos/Locrits
pip install pytest pytest-asyncio
```

#### Run All Backend Tests
```bash
python -m pytest src/tests/test_fullstack_locrit_flow.py -v -s
```

#### Run Specific Test
```bash
python -m pytest src/tests/test_fullstack_locrit_flow.py::TestFullstackLocritFlow::test_03_push_locrit_to_platform -v -s
```

#### Run with Coverage
```bash
pytest src/tests/test_fullstack_locrit_flow.py --cov=src/services --cov-report=html -v
```

### React Platform E2E Tests

#### Install Playwright
```bash
cd platform
npm install
npx playwright install
```

#### Start Development Server
```bash
# Terminal 1: Start the platform
npm run dev
```

#### Run E2E Tests
```bash
# Terminal 2: Run Playwright tests
npm run test:e2e

# Or with UI
npm run test:e2e:ui

# Or run specific test file
npx playwright test e2e/fullstack-locrit-review.spec.ts
```

#### Run in Headed Mode (see browser)
```bash
npx playwright test e2e/fullstack-locrit-review.spec.ts --headed
```

#### Debug Mode
```bash
npx playwright test e2e/fullstack-locrit-review.spec.ts --debug
```

## Test Scenarios

### Backend Tests (Python)

1. **test_01_firebase_service_configured**: Verifies Firebase service is properly set up
2. **test_02_authenticate_user**: Tests Firebase authentication
3. **test_03_push_locrit_to_platform**: Pushes a Locrit from backend to Firebase
4. **test_04_update_locrit_status**: Updates Locrit online/offline status
5. **test_05_log_locrit_activity**: Logs Locrit activity to Firebase
6. **test_06_retrieve_platform_conversations**: Retrieves conversations from platform
7. **test_07_push_multiple_locrits**: Batch push multiple Locrits
8. **test_08_update_existing_locrit**: Updates an existing Locrit (no duplicates)
9. **test_09_verify_locrit_settings_normalization**: Tests settings normalization
10. **test_10_error_handling_no_auth**: Tests error handling without authentication

### Platform E2E Tests (Playwright)

1. **Create Locrit in Firebase**: Simulates backend pushing a Locrit
2. **Display Locrit in UI**: Verifies Locrit appears in platform
3. **Display Correct Details**: Checks Locrit details are shown correctly
4. **Create Conversation**: Tests creating a conversation with the Locrit
5. **Verify Firebase Structure**: Validates data structure in Firestore
6. **Status Updates**: Tests online/offline status updates
7. **Public Platform View**: Verifies Locrit appears in public listings
8. **Activity Logging**: Tests activity logging to Firebase
9. **Review and Analytics**: Tests the review/analytics interface
10. **Conversation Review**: Tests conversation review functionality

## Running Full Integration Test Suite

To run the complete fullstack test suite:

```bash
# Terminal 1: Start platform dev server
cd platform
npm run dev

# Terminal 2: Run backend tests
cd ..
python -m pytest src/tests/test_fullstack_locrit_flow.py -v -s

# Terminal 3: Run platform E2E tests
cd platform
npx playwright test e2e/fullstack-locrit-review.spec.ts --headed

# Or use the convenience script (if created):
./run_fullstack_tests.sh
```

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/fullstack-tests.yml`:

```yaml
name: Fullstack Integration Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
      - name: Run backend tests
        env:
          FIREBASE_TEST_USE_ANONYMOUS: "true"
        run: |
          pytest src/tests/test_fullstack_locrit_flow.py -v

  platform-e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        working-directory: ./platform
        run: npm install
      - name: Install Playwright
        working-directory: ./platform
        run: npx playwright install --with-deps
      - name: Build platform
        working-directory: ./platform
        run: npm run build
      - name: Run E2E tests
        working-directory: ./platform
        run: npx playwright test e2e/fullstack-locrit-review.spec.ts
```

## Troubleshooting

### Backend Tests

**Issue**: `firebase not configured`
- Solution: Check `.env` file has correct Firebase credentials
- Verify `FIREBASE_PROJECT_ID` is set

**Issue**: `User authentication required`
- Solution: Enable anonymous authentication in Firebase Console
- Or set `FIREBASE_TEST_EMAIL` and `FIREBASE_TEST_PASSWORD`

**Issue**: `ModuleNotFoundError`
- Solution: Install dependencies: `pip install -r requirements.txt`

### Platform E2E Tests

**Issue**: `Target closed` or `Navigation timeout`
- Solution: Ensure dev server is running (`npm run dev`)
- Check server is accessible at `http://localhost:5173`

**Issue**: `Element not found`
- Solution: UI selectors may have changed - update test selectors
- Run in headed mode to see what's happening: `--headed`

**Issue**: `Firebase permission denied`
- Solution: Check Firestore security rules allow test operations
- Verify authentication is working

### Common Issues

**Issue**: Tests create too much test data
- Solution: Tests clean up after themselves, but you can manually clean:
  ```bash
  # Delete test Locrits from Firebase Console
  # Filter by name starting with "test-locrit-" or "e2e-test-"
  ```

**Issue**: Tests fail intermittently
- Solution: Increase timeouts in tests
- Check network connectivity to Firebase
- Use Firebase emulators for consistent testing

## Using Firebase Emulators (Optional)

For isolated testing without affecting production data:

### Setup Emulators
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Initialize emulators (if not already done)
firebase init emulators

# Start emulators
firebase emulators:start
```

### Configure Tests for Emulators

**Python Backend**: Update `unified_firebase_service.py`
```python
if os.getenv('USE_FIREBASE_EMULATOR') == 'true':
    os.environ['FIRESTORE_EMULATOR_HOST'] = 'localhost:8080'
```

**Platform**: Uncomment emulator config in `firebase/config.ts`
```typescript
if (import.meta.env.MODE === 'test') {
  connectFirestoreEmulator(db, 'localhost', 8080);
  connectAuthEmulator(auth, 'http://localhost:9099');
}
```

### Run Tests with Emulators
```bash
# Terminal 1: Start emulators
firebase emulators:start

# Terminal 2: Run tests
USE_FIREBASE_EMULATOR=true pytest src/tests/test_fullstack_locrit_flow.py -v
```

## Test Data Cleanup

Tests automatically clean up after themselves, but you can manually verify:

```bash
# List test Locrits in Firebase
# From Firebase Console, filter Firestore collection 'locrits' by:
# - name contains "test-locrit-"
# - name contains "e2e-test-"
# - tags array-contains "test" or "e2e-test"

# Delete old test data (older than 1 day)
```

## Best Practices

1. **Use Anonymous Auth for Tests**: Simpler and cleaner than email/password
2. **Always Clean Up**: Tests should remove created data
3. **Use Unique Names**: Include timestamp in test data names
4. **Test in Isolation**: Don't depend on other tests' data
5. **Use Emulators for CI**: Faster and more reliable than production Firebase
6. **Monitor Test Data**: Regularly check for orphaned test records

## Next Steps

- [ ] Set up GitHub Actions for automated testing
- [ ] Configure Firebase emulators for CI
- [ ] Add performance benchmarks to tests
- [ ] Create additional conversation flow tests
- [ ] Add visual regression testing with Playwright

## Support

For issues or questions:
- Check test logs for detailed error messages
- Review Firebase Console for data verification
- Run tests in debug mode: `--debug` for Playwright, `-vv -s` for pytest
