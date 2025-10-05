#!/bin/bash

###############################################################################
# Locrits Test Suite
# Runs comprehensive tests for backend, frontend, and memory services
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
TEST_START_TIME=$(date +%s)

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((TESTS_FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to run a test and handle errors
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -e "${YELLOW}Running: $test_name${NC}"

    if eval "$test_command"; then
        print_success "$test_name passed"
        return 0
    else
        print_error "$test_name failed"
        return 1
    fi
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d ".venv" ]; then
        print_error "Virtual environment not found. Please run: python -m venv .venv"
        exit 1
    fi
}

# Activate virtual environment
activate_venv() {
    print_info "Activating virtual environment..."
    source .venv/bin/activate
}

###############################################################################
# 1. BACKEND TESTS
###############################################################################

test_backend() {
    print_header "🐍 BACKEND TESTS"

    # Check Python version
    print_info "Checking Python version..."
    python --version

    # Install dependencies if needed
    if [ ! -f ".venv/lib/python*/site-packages/fastapi" ]; then
        print_info "Installing backend dependencies..."
        pip install -r requirements.txt -q
    fi

    # Run Python tests if they exist
    if [ -f "tests/test_backend.py" ]; then
        run_test "Backend unit tests" "python -m pytest tests/test_backend.py -v" || true
    else
        print_warning "No backend unit tests found (tests/test_backend.py)"
    fi

    # Test imports
    run_test "Backend imports" "python -c 'from src.services.memory.memory_factory import MemoryServiceFactory; print(\"✓ Memory factory import successful\")'" || true

    # Test config loading
    run_test "Config loading" 'cd /mnt/storage/repos/Locrits && python -c "import yaml; config = yaml.safe_load(open(\"config.yaml\")); print(f\"✓ Config loaded: {len(config.get(\"locrits\", {}).get(\"instances\", {}))} locrits\")"' || true

    # Syntax check all Python files
    print_info "Checking Python syntax..."
    if find src -name "*.py" -exec python -m py_compile {} + 2>/dev/null; then
        print_success "Python syntax check passed"
    else
        print_error "Python syntax errors found"
    fi
}

###############################################################################
# 2. FRONTEND TESTS
###############################################################################

test_frontend() {
    print_header "⚛️  FRONTEND TESTS"

    cd frontend

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_info "Installing frontend dependencies..."
        npm install
    fi

    # TypeScript type checking
    run_test "TypeScript type check" "npm run type-check 2>/dev/null || npx tsc --noEmit" || true

    # Linting
    run_test "ESLint check" "npm run lint 2>/dev/null || npx eslint src --ext .ts,.tsx --max-warnings 0" || true

    # Build test
    run_test "Frontend build" "npm run build" || true

    # Check if tests exist
    if [ -f "package.json" ] && grep -q "\"test\"" package.json; then
        run_test "Frontend unit tests" "npm test -- --run" || true
    else
        print_warning "No frontend test script found"
    fi

    cd ..
}

###############################################################################
# 3. MEMORY SERVICE TESTS
###############################################################################

test_memory_services() {
    print_header "🧠 MEMORY SERVICE TESTS"

    print_info "NOTE: Kuzu tests removed due to Python 3.13 compatibility issues"

    # Test plaintext memory service
    run_test "Plaintext memory service" "python -c '
import asyncio
from src.services.memory.memory_factory import MemoryServiceFactory

async def test():
    service = MemoryServiceFactory.create_memory_service(
        \"TestBot\", \"plaintext_file\", {\"database_path\": \"data/memory\"}
    )
    if service:
        await service.initialize()
        print(\"✓ Plaintext service initialized\")
        await service.close()
        return True
    return False

asyncio.run(test())
'" || true

    # Test LanceDB LangChain service (if dependencies available)
    if python -c "import lancedb" 2>/dev/null; then
        run_test "LanceDB LangChain service" "python -c '
import asyncio
from src.services.memory.memory_factory import MemoryServiceFactory

async def test():
    service = MemoryServiceFactory.create_memory_service(
        \"TestBot\", \"lancedb_langchain\", {\"database_path\": \"data/memory\"}
    )
    if service:
        print(\"✓ LanceDB LangChain service created\")
        return True
    return False

asyncio.run(test())
'" || true
    else
        print_warning "LanceDB not installed, skipping LanceDB tests"
    fi

    # Test memory factory (excluding Kuzu)
    run_test "Memory factory services" 'python -c "
from src.services.memory.memory_factory import MemoryServiceFactory

services = MemoryServiceFactory.get_available_services()
# Exclude Kuzu from count
non_kuzu_services = {k: v for k, v in services.items() if k != \"kuzu_graph\"}
print(f\"✓ Available memory services: {len(non_kuzu_services)} (excluding Kuzu)\")
for svc_type, info in non_kuzu_services.items():
    print(f\"  - {svc_type}: {info[\"name\"]}\")
"' || true

    # Run memory progression test if it exists
    if [ -f "test_memory_progression_simple.py" ]; then
        run_test "Memory progression test" "python test_memory_progression_simple.py" || true
    else
        print_warning "Memory progression test not found"
    fi
}

###############################################################################
# 4. INTEGRATION TESTS
###############################################################################

test_integration() {
    print_header "🔗 INTEGRATION TESTS"

    # Check if backend server is running
    if curl -s http://localhost:5000/health >/dev/null 2>&1; then
        print_info "Backend server is running"

        # Test API endpoints
        run_test "Health endpoint" "curl -s http://localhost:5000/health | grep -q 'healthy'" || true
        run_test "Locrits API" "curl -s http://localhost:5000/api/locrits | grep -q 'success'" || true

    else
        print_warning "Backend server not running (start with: python src/web_app.py)"
    fi

    # Check if frontend dev server is running
    if curl -s http://localhost:5173 >/dev/null 2>&1; then
        print_success "Frontend dev server is running"
    else
        print_warning "Frontend dev server not running (start with: cd frontend && npm run dev)"
    fi
}

###############################################################################
# 5. DEPENDENCY CHECKS
###############################################################################

test_dependencies() {
    print_header "📦 DEPENDENCY CHECKS"

    # Check Python dependencies
    print_info "Checking Python dependencies..."
    if pip check >/dev/null 2>&1; then
        print_success "Python dependencies are compatible"
    else
        print_warning "Some Python dependency conflicts detected"
        pip check || true
    fi

    # Check for outdated packages
    print_info "Checking for security vulnerabilities..."
    if command -v safety &> /dev/null; then
        run_test "Security check" "safety check" || true
    else
        print_warning "Safety not installed (pip install safety)"
    fi
}

###############################################################################
# MAIN EXECUTION
###############################################################################

main() {
    print_header "🚀 LOCRITS TEST SUITE"
    print_info "Starting comprehensive test suite..."
    print_info "Working directory: $(pwd)"

    # Check virtual environment
    check_venv
    activate_venv

    # Run test suites
    test_backend
    test_frontend
    test_memory_services
    test_integration
    test_dependencies

    # Summary
    TEST_END_TIME=$(date +%s)
    TEST_DURATION=$((TEST_END_TIME - TEST_START_TIME))

    print_header "📊 TEST SUMMARY"
    echo -e "${GREEN}✅ Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}❌ Failed: $TESTS_FAILED${NC}"
    echo -e "${BLUE}⏱️  Duration: ${TEST_DURATION}s${NC}"

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All tests passed!${NC}\n"
        exit 0
    else
        echo -e "\n${RED}⚠️  Some tests failed. Please review the output above.${NC}\n"
        exit 1
    fi
}

# Parse command line arguments
SKIP_BACKEND=false
SKIP_FRONTEND=false
SKIP_MEMORY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backend)
            SKIP_BACKEND=true
            shift
            ;;
        --skip-frontend)
            SKIP_FRONTEND=true
            shift
            ;;
        --skip-memory)
            SKIP_MEMORY=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-backend     Skip backend tests"
            echo "  --skip-frontend    Skip frontend tests"
            echo "  --skip-memory      Skip memory service tests"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                    # Run all tests"
            echo "  ./run_tests.sh --skip-frontend    # Skip frontend tests"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main
