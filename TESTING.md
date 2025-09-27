# Locrit Testing Framework - Quick Start

## Overview
Comprehensive Playwright-based testing suite for the Locrit application with 96 tests covering UI, API integration, and configuration validation.

## Quick Setup
```bash
# Install Playwright and browsers
npm install
npm run test:install

# Run all tests
npm test

# Run with UI (interactive mode)
npm run test:ui
```

## Test Categories

### 🎯 E2E Tests (24 tests)
- **Dashboard**: Navigation, stats, theme toggle
- **Locrits Management**: CRUD operations, state management
- **Create Locrit**: Form validation, permissions
- **Settings**: Configuration interface

### 🔗 Integration Tests (72 tests)
- **API Integration**: Frontend-backend communication
- **Config Validation**: Input validation, business rules

## Quick Commands

```bash
# Run specific test suites
npm run test:e2e              # All E2E tests
npm run test:integration      # All integration tests
npm run test:dashboard        # Dashboard tests only
npm run test:api             # API integration tests

# Run by browser
npm run test:chromium        # Chrome tests
npm run test:firefox         # Firefox tests
npm run test:webkit          # Safari tests

# Development
npm run test:headed          # With browser UI
npm run test:debug          # Step-by-step debugging
npm run test:report         # View last test report
```

## Test Structure
```
tests/
├── e2e/
│   ├── dashboard.spec.ts           # Main dashboard functionality
│   ├── locrits-management.spec.ts  # Locrit CRUD operations
│   ├── create-locrit.spec.ts      # Creation workflow
│   └── settings.spec.ts           # Configuration interface
└── integration/
    ├── api-integration.spec.ts     # API communication
    └── config-validation.spec.ts   # Input validation
```

## Coverage Summary
- ✅ **96 total tests** across 6 test files
- ✅ **Cross-browser testing** (Chrome, Firefox, Safari)
- ✅ **UI workflow validation** for all major features
- ✅ **API integration testing** with mocking
- ✅ **Configuration validation** with business rules
- ✅ **Error handling** and edge cases

## Key Features Tested
- 🏠 Dashboard navigation and statistics
- 🤖 Locrit management (create, start, stop, delete)
- ⚙️ Settings and configuration
- 🔐 Permission and access control
- 🌐 API communication and error handling
- ✅ Form validation and input constraints

## Quick Test Run
```bash
# Verify setup works
npm run test:dashboard -- --headed

# See test results
npm run test:report
```

For detailed documentation, see [fullstack-testing.md](./fullstack-testing.md).