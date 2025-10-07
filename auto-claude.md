# Auto-Claude: Locrits Quick Reference

> **Purpose**: Quick reference guide for starting apps, understanding architecture, and running tests.

## 📱 The 3 Apps at a Glance

1. **Backend (Flask)** - Port 5000 - Core API and services that power everything
2. **Frontend (React)** - Port 5174 - User dashboard for personal Locrit management
3. **Platform (React)** - Port 5173 - Public directory and admin interface

**Backend must be started first**, then start whichever frontend(s) you need.

---

## 🚀 Quick Start - The 3 Apps

### 1️⃣ Backend API (Flask) - **Locrit Engine & API**
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the Flask backend
python backend/web_app.py

# Access at: http://localhost:5000
```

**What it does:**
- RESTful API for Locrit management (CRUD operations)
- WebSocket support for real-time chat
- Conversation and memory storage management
- Firebase authentication integration
- Serves as the main backend for all frontends

**Entry point:** `backend/web_app.py` → imports from `backend/app.py`

---

### 2️⃣ Frontend (React + Vite) - **User Dashboard**
```bash
# Navigate to frontend folder
cd frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev

# Access at: http://localhost:5174
```

**What it does:**
- User-facing React interface for personal Locrit management
- Real-time communication with backend via REST API and WebSocket
- Firebase authentication UI
- Locrit management, chat interface, memory exploration
- Uses shadcn/ui components with Tailwind CSS

**Entry point:** `frontend/src/main.tsx` → `frontend/src/App.tsx`

**Important:** Backend must be running first (port 5000)

---

### 3️⃣ Platform (React + Vite) - **Public & Admin Interface**
```bash
# Navigate to platform folder
cd platform

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev

# Access at: http://localhost:5173
```

**What it does:**
- Public-facing platform for Locrit discovery and interaction
- Admin interface for user and Locrit management
- Public Locrits directory with searchable catalog
- Public chat interface with any Locrit
- Scheduled autonomous conversations between Locrits
- Firebase/Firestore integration for data services
- WebSocket support for real-time updates

**Entry point:** `platform/src/main.tsx` → `platform/src/App.tsx`

**Important:** Backend must be running first (port 5000)



## 📁 Project Structure

```
Locrits/
│
├── backend/                    # 🌐 Flask Backend (Modular Architecture)
│   ├── web_app.py             # Entry point for Flask app
│   ├── app.py                 # Flask factory and app runner
│   ├── config/                # Flask configuration
│   │   └── flask_config.py    # Config classes (Dev, Prod, Test)
│   ├── middleware/            # Authentication middleware
│   │   └── auth.py            # @require_auth decorator
│   └── routes/                # Modular route blueprints
│       ├── auth.py            # Login/logout endpoints
│       ├── dashboard.py       # Dashboard data
│       ├── locrits.py         # Locrit CRUD operations
│       ├── chat.py            # Chat endpoints
│       ├── conversation.py    # Conversation management
│       ├── memory.py          # Memory operations
│       ├── websocket.py       # WebSocket handlers
│       ├── config.py          # App configuration
│       ├── public.py          # Public (no auth) routes
│       └── api/               # Public API endpoints
│
├── frontend/                   # ⚛️ React Frontend (Vite + TypeScript) - User Dashboard
│   ├── package.json           # Dependencies & scripts
│   ├── vite.config.ts         # Vite configuration
│   ├── src/
│   │   ├── main.tsx           # React entry point
│   │   ├── App.tsx            # Main app component with routing
│   │   ├── pages/             # Page components
│   │   │   ├── Dashboard.tsx  # Home dashboard
│   │   │   ├── MyLocrits.tsx  # Locrits list
│   │   │   ├── CreateLocrit.tsx
│   │   │   ├── Chat.tsx       # Chat interface
│   │   │   ├── Settings.tsx   # App settings
│   │   │   ├── MemoryExplorer.tsx
│   │   │   └── Login.tsx      # Authentication
│   │   ├── components/        # Reusable components
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── Navigation.tsx
│   │   │   └── ui/            # shadcn/ui components
│   │   └── lib/               # Utilities & services
│   │       ├── firebase.ts    # Firebase config
│   │       ├── auth.ts        # Auth helpers
│   │       ├── firebaseService.ts
│   │       └── syncService.ts
│   └── public/                # Static assets
│
├── platform/                   # 🌐 Platform Frontend (Vite + TypeScript) - Public/Admin
│   ├── package.json           # Dependencies & scripts
│   ├── vite.config.ts         # Vite configuration
│   ├── src/
│   │   ├── main.tsx           # React entry point
│   │   ├── App.tsx            # Main app component
│   │   ├── components/        # Platform components
│   │   │   ├── Dashboard.tsx           # Admin dashboard
│   │   │   ├── UserManagement.tsx      # User admin
│   │   │   ├── LocritCard.tsx          # Locrit display
│   │   │   ├── LocritSettings.tsx      # Locrit config
│   │   │   ├── PublicLocritsDirectory.tsx  # Public catalog
│   │   │   ├── PublicLocritChat.tsx    # Public chat
│   │   │   ├── ChatInterface.tsx       # Chat UI
│   │   │   ├── ConversationManager.tsx # Conversation control
│   │   │   ├── ScheduledConversation.tsx   # Autonomous conversations
│   │   │   └── ui/                     # shadcn/ui components
│   │   ├── lib/               # Services
│   │   │   ├── locritBackendService.ts  # Backend API
│   │   │   ├── locritWebSocketService.ts # WebSocket
│   │   │   ├── conversationService.ts   # Conversations
│   │   │   └── firebaseService.ts       # Firebase
│   │   ├── firebase/          # Firebase config
│   │   │   ├── config.ts
│   │   │   ├── auth.ts
│   │   │   └── services.ts
│   │   └── types/             # TypeScript types
│   └── e2e/                   # E2E tests
│
├── src/                        # 🔧 Core Services (Shared by Backend)
│   ├── services/              # Core business logic
│   │   ├── locrit_manager.py  # Central Locrit coordinator
│   │   ├── conversation_service.py  # Conversation logic
│   │   ├── memory_service.py        # Memory storage (SQLite)
│   │   ├── kuzu_memory_service.py   # Graph memory (KuzuDB)
│   │   ├── graph_memory_service.py  # Graph operations
│   │   ├── ollama_service.py        # LLM integration
│   │   ├── search_service.py        # DuckDuckGo search
│   │   ├── embedding_service.py     # Vector embeddings
│   │   ├── auth_service.py          # Firebase auth
│   │   ├── config_service.py        # YAML config
│   │   ├── unified_firebase_service.py
│   │   ├── session_service.py
│   │   └── comprehensive_logging_service.py
│   ├── models/                # Data models
│   └── utils/                 # Utility functions
│
├── tests/                      # 🧪 Test Suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests (Playwright)
│   ├── e2e/                   # End-to-end tests (Playwright)
│   ├── fullstack/             # Fullstack API tests (Python)
│   ├── memory/                # Memory service tests
│   └── utils/                 # Test utilities
│
├── config/                     # Configuration files
├── data/                       # SQLite databases, KuzuDB data
├── logs/                       # Application logs
├── static/                     # Static files for Flask
├── templates/                  # Jinja2 templates (if needed)
│
├── config.yaml                 # Main configuration file
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies (Playwright)
├── run_tests.sh                # Test runner script
└── .env                        # Environment variables (not in git)
```

---

## 🔧 App Architecture Details

### Backend Architecture (Flask)

**Modular Blueprint Structure:**
```
Flask App
├── auth routes      → Login, logout, session management
├── dashboard routes → Home page data, statistics
├── locrits routes   → CRUD for Locrits (create, read, update, delete)
├── chat routes      → Chat with Locrits
├── conversation     → Conversation history management
├── memory routes    → Memory operations (store, retrieve, search)
├── websocket        → Real-time WebSocket communication
├── config routes    → App configuration management
└── public API       → Public endpoints (no auth required)
```

**Key Services Used:**
- `LocritManager`: Central coordinator for all Locrits
- `ConversationService`: Manages conversation state and history
- `MemoryService`: SQLite + FAISS vector search
- `KuzuMemoryService`: Graph database for structured memory
- `OllamaService`: LLM integration via Ollama
- `AuthService`: Firebase authentication

**Flow:**
1. Request → Flask route blueprint
2. Middleware checks authentication (`@require_auth`)
3. Route handler calls service layer
4. Service performs business logic
5. Response returned as JSON

---

### Frontend Architecture (React) - User Dashboard

**Component Hierarchy:**
```
App.tsx (Router)
├── Layout (Header + Footer + Navigation)
├── Pages
│   ├── Dashboard        → Shows stats, recent activity
│   ├── MyLocrits        → List all Locrits
│   ├── CreateLocrit     → Form to create new Locrit
│   ├── Chat             → Chat interface with WebSocket
│   ├── Settings         → App configuration
│   ├── MemoryExplorer   → Browse memory graph
│   └── Login            → Firebase authentication
└── Components
    └── ui/              → Reusable shadcn components
```

**State Management:**
- React hooks (useState, useEffect)
- Firebase auth context
- WebSocket for real-time updates

**API Communication:**
- REST API calls to `http://localhost:5000`
- WebSocket connection for chat
- Firebase SDK for authentication

---

### Platform Architecture (React) - Public/Admin

**Component Hierarchy:**
```
App.tsx (Router)
├── Dashboard             → Admin overview
├── UserManagement        → User administration
├── PublicLocritsDirectory → Public catalog with search
├── PublicLocritChat      → Public chat interface
├── LocritCard            → Locrit display component
├── LocritSettings        → Locrit configuration
├── ChatInterface         → Real-time chat UI
├── ConversationManager   → Conversation orchestration
├── ScheduledConversation → Autonomous Locrit interactions
└── Components
    └── ui/               → Reusable shadcn components
```

**Key Services:**
- `locritBackendService`: REST API integration with Flask backend
- `locritWebSocketService`: Real-time WebSocket communication
- `conversationService`: Conversation state management
- `firebaseService`: Firestore data operations

**State Management:**
- React hooks (useState, useEffect, useContext)
- Firebase auth and Firestore real-time listeners
- WebSocket for chat updates

**Data Flow:**
1. Public endpoints → No auth required for directory browsing
2. Authenticated endpoints → Firebase auth for admin features
3. Real-time updates → WebSocket for chat, Firestore for data sync
4. Scheduled conversations → Backend orchestrates autonomous Locrit interactions

---

## 🧪 Tests Structure

### Test Organization

```
tests/
├── unit/                      # Fast, isolated unit tests
│   └── (Python unit tests for services)
│
├── integration/               # Playwright integration tests
│   ├── api-integration.spec.ts
│   └── config-validation.spec.ts
│
├── e2e/                       # Playwright end-to-end tests
│   ├── dashboard.spec.ts      # Dashboard UI tests
│   ├── locrits-management.spec.ts
│   ├── create-locrit.spec.ts
│   └── settings.spec.ts
│
├── fullstack/                 # Python API tests
│   ├── test_chat_api_storage.py
│   ├── test_config_api.py
│   ├── test_conversation_api.py
│   ├── test_locrit_api.py
│   ├── test_websocket_chat_storage.py
│   ├── test_ollama_integration.py
│   └── debug_cors.py
│
├── memory/                    # Memory service tests
│   ├── test_conversation_storage.py
│   ├── test_locrit_root_storage.py
│   ├── test_memory_progression.py
│   └── test_websocket_memory.py
│
└── utils/                     # Test utilities and helpers
```

---

### Running Tests

#### 🔹 All Tests (Comprehensive Suite)
```bash
./run_tests.sh
```
**What it does:**
- Activates virtual environment
- Runs backend Python tests (if present)
- Runs frontend Playwright tests
- Runs memory service tests
- Runs fullstack integration tests
- Generates test report

---

#### 🔹 Backend Python Tests
```bash
source .venv/bin/activate
python -m pytest tests/fullstack/ -v
python -m pytest tests/memory/ -v
```

---

#### 🔹 Frontend E2E Tests (Playwright)
```bash
# In root directory
npm run test              # All Playwright tests
npm run test:ui           # Interactive UI mode
npm run test:headed       # Show browser
npm run test:debug        # Debug mode

# Specific test suites
npm run test:e2e          # Only E2E tests
npm run test:integration  # Only integration tests
npm run test:dashboard    # Just dashboard tests
npm run test:locrits      # Just Locrits management tests
npm run test:create       # Just create Locrit tests
npm run test:settings     # Just settings tests

# Specific browsers
npm run test:chromium
npm run test:firefox
npm run test:webkit

# View test report
npm run test:report
```

---

#### 🔹 Platform Tests (Vitest + Playwright)
```bash
# In platform directory
cd platform

# Unit tests (Vitest)
npm run test              # Run tests in watch mode
npm run test:ui           # Interactive UI
npm run test:run          # Single run
npm run test:coverage     # With coverage

# E2E tests (Playwright)
npm run test:e2e          # Run E2E tests
npm run test:e2e:ui       # Interactive mode

# Type checking
npm run type-check
```

---

#### 🔹 Individual Test Files
```bash
# Python tests
python -m pytest tests/fullstack/test_chat_api_storage.py -v
python -m pytest tests/memory/test_conversation_storage.py -v

# Playwright tests (root)
npx playwright test tests/e2e/dashboard.spec.ts

# Platform E2E tests
cd platform
npx playwright test e2e/auth.spec.ts
npx playwright test e2e/conversations.spec.ts
```

---

### Test Categories

**🟢 Unit Tests** (`tests/unit/`)
- Test individual functions/methods
- No external dependencies
- Fast execution

**🟡 Integration Tests** (`tests/integration/`)
- Test component interactions
- May use test databases
- Medium execution time

**🔴 E2E Tests** (`tests/e2e/`)
- Full user journey testing
- Real browser automation
- Slower execution

**🔵 Fullstack Tests** (`tests/fullstack/`)
- Backend API testing
- Database interactions
- WebSocket testing
- Service integration

**🟣 Memory Tests** (`tests/memory/`)
- Memory service functionality
- Storage persistence
- Graph memory operations
- Conversation history

---

## ⚙️ Environment Configuration

### Required Environment Variables

Create a `.env` file in the root directory:

```bash
# Flask Backend
WEB_PORT=5000
WEB_HOST=localhost
FLASK_DEBUG=true
FLASK_SECRET_KEY=your-secret-key-here

# Firebase (Optional - for authentication)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-client-email

# Ollama (Optional - for LLM features)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### Frontend Configuration

Create `frontend/.env`:

```bash
VITE_API_URL=http://localhost:5000
VITE_NODE_ENV=development
```

### Platform Configuration

Create `platform/.env`:

```bash
VITE_API_URL=http://localhost:5000
VITE_NODE_ENV=development
```

---

## 🔗 Port Reference

| Service | Port | URL |
|---------|------|-----|
| Flask Backend | 5000 | http://localhost:5000 |
| Frontend (User) | 5174 | http://localhost:5174 |
| Platform (Public/Admin) | 5173 | http://localhost:5173 |
| Ollama API | 11434 | http://localhost:11434 |

---

## 🛠️ Common Tasks

### Start Full Stack Development
```bash
# Terminal 1: Backend
source .venv/bin/activate
python backend/web_app.py

# Terminal 2: Frontend (User Dashboard)
cd frontend
npm run dev

# Terminal 3: Platform (Public/Admin) - Optional
cd platform
npm run dev
```

### Run Tests Before Commit
```bash
./run_tests.sh
```

### Debug CORS Issues
```bash
python tests/fullstack/debug_cors.py
```

### Check Backend Health
```bash
curl http://localhost:5000/api/health
```

### View Logs
```bash
tail -f logs/app.log
```

---

## 📊 Key Files Reference

| File | Purpose |
|------|---------|
| `backend/web_app.py` | Flask backend entry point |
| `backend/app.py` | Flask factory and configuration |
| `frontend/src/main.tsx` | Frontend (user) entry point |
| `platform/src/main.tsx` | Platform (public/admin) entry point |
| `config.yaml` | Main configuration file |
| `requirements.txt` | Python dependencies |
| `run_tests.sh` | Test runner script |
| `.env` | Environment variables (not in git) |
| `package.json` | Root Node.js project metadata |
| `frontend/package.json` | Frontend dependencies |
| `platform/package.json` | Platform dependencies |

---

## 🎯 Development Workflow

1. **Start Backend First**
   ```bash
   source .venv/bin/activate
   python backend/web_app.py
   ```

2. **Start Frontend(s)** (in new terminal(s))
   ```bash
   # User Dashboard
   cd frontend
   npm run dev

   # Platform (optional, in another terminal)
   cd platform
   npm run dev
   ```

3. **Make Changes**
   - Backend: Edit files in `backend/` or `src/services/`
   - Frontend: Edit files in `frontend/src/`
   - Platform: Edit files in `platform/src/`

4. **Test Changes**
   ```bash
   ./run_tests.sh
   # or run specific tests
   ```

5. **Commit**
   ```bash
   git add .
   git commit -m "Your message"
   ```

---

## 🆘 Troubleshooting

### Backend won't start
- Check if port 5000 is available: `lsof -i :5000`
- Verify virtual environment: `which python`
- Check dependencies: `pip install -r requirements.txt`

### Frontend can't connect
- Ensure backend is running first on port 5000
- Check CORS configuration in backend
- Verify `VITE_API_URL` in frontend/.env or platform/.env
- Confirm correct port (Frontend: 5174, Platform: 5173)

### Platform-specific issues
- Firestore connection errors: Check Firebase config in `platform/src/firebase/config.ts`
- WebSocket not connecting: Verify backend WebSocket endpoint is accessible
- Public routes 404: Ensure backend public routes are enabled

### Tests failing
- Make sure backend is NOT running during tests
- Check test database is clean
- Verify Playwright browsers installed: `npm run test:install` (root) or `npx playwright install` (platform)

### CORS errors
- Backend allows ports: 3000, 5173, 5174
- Run debug script: `python tests/fullstack/debug_cors.py`

### Port conflicts
- Backend (5000): `lsof -i :5000` then `kill -9 <PID>`
- Frontend (5174): `lsof -i :5174` then `kill -9 <PID>`
- Platform (5173): `lsof -i :5173` then `kill -9 <PID>`

---

## 📚 Additional Documentation

- [README.md](README.md) - General project overview
- [FEATURES.md](FEATURES.md) - Feature roadmap
- [TESTING.md](TESTING.md) - Detailed testing guide
- [FULLSTACK_TESTING.md](FULLSTACK_TESTING.md) - Fullstack test documentation
- [MEMORY.md](MEMORY.md) - Memory system architecture
- [Firebase.md](Firebase.md) - Firebase integration guide

---

**Last Updated:** October 2025
**Version:** 1.0.0
