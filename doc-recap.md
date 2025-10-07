# Documentation Recap - Locrits Project

## Core Documentation

### README.md
Main project documentation - Locrit system overview, quick start guide, features (web interface, memory, search, LLM integration), installation instructions, and project structure.

### FEATURES.md
Complete feature list and implementation status - Services architecture (Ollama, Search, Memory with graph/vector storage), communication modes (chat, API server, client mode), UI implementation status, and technical roadmap.

## API Documentation

### API_DOCUMENTATION.md
HTTP API reference - Chat endpoints (`/api/locrits/{name}/chat`), memory features, automatic context management, other endpoints (list, toggle, delete locrits), and cURL examples.

### CHAT_API.md
Chat API detailed guide - Web interface for authenticated users, Public API v1 for inter-Locrit communication, endpoints, authentication strategy, and Python client examples.

### CONVERSATION_API.md
Server-side context management - Conversation ID-based API, endpoints for creating/managing conversations, Python/JavaScript/cURL examples, benefits over manual context management.

## Memory System

### MEMORY.md
Memory system architecture - Kuzu graph database integration, graph schema (User, Message, Session, Concept, Topic, Memory nodes), operations (storage, retrieval, search), integration points with HTTP/WebSocket APIs.

### MEMORY_SERVICE_ABSTRACTION.md
Memory service abstraction layer - Multiple backend implementations (plaintext, Kuzu graph, Basic Memory MCP, LanceDB LangChain, LanceDB MCP, disabled), configuration per Locrit, migration guide, troubleshooting.

### MEMORY_INTEGRATION_GUIDE.md
Modular memory system integration - Graph vs vector memory separation, architecture overview, installation dependencies, LLM tool integration, memory update scheduling.

## Configuration & Setup

### Firebase.md
Firebase/Firestore configuration - Current setup with Admin SDK, advantages, required configuration, security rules, structure (users/{userId}/locrits), auto-login functionality.

### CONFIG_FIREBASE.md
Firebase configuration guide - Client-side setup for distributed locrits, web app configuration, service implementation, security rules for Realtime Database and Firestore, troubleshooting.

### AUTH_FIREBASE.md
Firebase authentication - Auto-login mode vs interactive mode, authentication screen features, integration with LocritManager, session management, security features.

### BUILD_FIREBASE.md
Firebase setup for platform - Detailed configuration guide, collections structure, security rules, storage rules, service examples, migration scripts, index recommendations.

### UI_FIREBASE.md
Firebase quick setup - 5-minute configuration guide, authentication setup, Firestore rules, required indexes, troubleshooting common issues.

### GUIDE_LOCRITS_LOCAUX.md
Local Locrits guide ("Mes Locrits Locaux") - Accessing the screen, displaying locrits from config.yaml, Firestore synchronization, available actions, user interface overview.

### secrets-install.md
Secrets installation for production - Firebase environment variables, deployment platform secrets (Firebase Hosting, Netlify, Vercel), local development setup, security best practices.

## Testing Documentation

### TESTING.md
General testing guide - Test suite overview (backend, frontend, memory, integration), running tests, test categories, troubleshooting, test coverage details.

### TESTING_SUITE.md
Playwright testing framework - 96 tests across 6 files, E2E tests (Dashboard, Locrits Management, Create Locrit, Settings), integration tests (API, config validation), quick setup commands.

### fullstack-testing.md
Fullstack testing comprehensive guide - Playwright-based test suite, UI/API/configuration coverage, test structure, running tests, CI/CD integration, troubleshooting.

### FULLSTACK_TESTING.md
Backend-to-platform testing - Python backend tests (Firebase integration), React platform E2E tests, full integration test suite, Firebase emulators usage, test data cleanup.

### FULLSTACK_TEST_SUMMARY.md
Test suite summary - Backend and platform E2E tests, authentication strategy, Firebase integration, test data management, CI/CD readiness.

### test_memory_progression_README.md
Memory progression test - Progressive information sharing across conversations, fictive character generation with Faker, memory verification, usage instructions.

### testing-progress.md
Test progress tracking - Status summary (completed, failing, needing config.yaml verification), current issues, implementation plan, progress tracking by week.

## Test Results & Status

### TEST_RESULTS.md
Memory test results - Test files created, execution results, issues discovered (server timeout, message endpoint dependency, test dependencies), recommendations.

### TEST_STATUS.md
Test fixes status - 6 fixed issues (UI shared folder, MemoryExplorer TypeScript, LanceDB dependencies, /health endpoint, Kuzu removal, ESLint config), 6 remaining issues.

### TEST_FIXES.md
Test failures list - Summary (8 passed, 6 failed), critical failures (config loading, frontend build TypeScript errors, ESLint, MemoryExplorer types), fix priority order.

### TEST_RESULTS_SUMMARY.md
Final test status - 12 passed / 2 failed (was 8/6), 86% success rate, improvements applied, test categories breakdown, next steps.

### FINAL_TEST_RESULTS.md
API tests & memory monitoring - Test execution results, successful tests (YAML persistence, memory stability), issues (send message timeout, nested event loops), memory leak fix verification.

### QUICKSTART_TESTING.md
Quick start test guide - TL;DR run all tests, what gets tested (backend→Firebase, platform display), individual test commands, troubleshooting, expected output.

## Refactoring & Fixes

### CONVERSATION_REFACTORING.md
Server-side context management - Conversation service implementation, new API endpoints, platform conversation service client, updated App.tsx, architecture diagram, benefits.

### CONVERSATION_STORAGE_FIX.md
Conversation storage bug fix - Problem (asyncio.run() in async functions), issues fixed in chat.py and websocket.py, testing procedures, verification steps.

### FRONTEND_BACKEND_STORAGE_FIX.md
Complete storage fix - Frontend using WebSocket (not REST), root causes (REST API and WebSocket API issues), fixes applied, verification guide, architecture overview.

### KUZU_FIXES_COMPLETE.md
Kuzu segfault fixes - Root causes (race condition, wrong API usage, no thread safety, database corruption), all fixes applied (thread-safe initialization, proper async API, auto-recovery, memory cleanup).

### KUZU_MEMORY_FIX.md
Kuzu memory issues - Problems (segfault causes, resource exhaustion), immediate fixes (connection management, message archival, embeddings disable, memory monitoring, cleanup).

### DISABLE_KUZU.md
Disable Kuzu option - Alternative if Kuzu crashes (downgrade Python, disable Kuzu, use SQLite, disable memory completely), compatibility check.

## Platform & Frontend

### platform/README.md
Platform overview - React-based frontend for Locrit management, features, installation, development workflow.

### frontend-features.md
Frontend React features - Vue d'ensemble, architecture de données, modes de fonctionnement, interface utilisateur (authentication, dashboard, locrits amis, mes locrits locaux, création, paramètres, chat, à propos), état d'implémentation.

### communications.md
Communication flow - Text-based flow (User→Frontend→Backend→Ollama), detailed steps, WebSocket integration, Locrit configuration management (config.yaml storage, editing via UI).

### platform/WEBSOCKET_INTEGRATION.md
WebSocket integration code - handleSendMessage replacement for App.tsx, streaming functionality, fallback HTTP, features (real-time streaming, auto-reconnection, error handling).

### platform/src/FIREBASE_SETUP.md
Firebase setup detailed - Collections structure, security rules, service examples, migration scripts, composite indexes.

### platform/src/FIREBASE_QUICK_SETUP.md
Quick Firebase configuration - Express setup guide, authentication/Firestore activation, security rules, index creation, troubleshooting.

## Technical Specifications

### claude.md
Project context - Locrits as LLM-animated characters, functionality (personality, memory), how they "live" (local chat, online exposure, inter-Locrit communication), advancement stages (L0-L3), code instructions.

### SEGFAULT_FIX.md
Segfault debugging - Kuzu compatibility issues with Python 3.13+, recommended fixes, alternative memory solutions.

### USAGE_EXAMPLES.md
HTTP API usage examples - Quick start, cURL examples, Python code examples, JavaScript/Node.js examples, test results, available endpoints.

## Test Directories

### tests/memory/README.md
Memory test directory - Test files overview (memory progression, storage, WebSocket), running tests, prerequisites, memory services tested, debugging.

### tests/fullstack/README.md
Fullstack test directory - API tests (config, Ollama, Locrit, conversation), storage & memory tests, utilities (CORS debugging), running tests, prerequisites.

---

**Total:** 58 markdown files covering project documentation, API references, memory systems, Firebase configuration, testing frameworks, bug fixes, platform features, and technical specifications.
