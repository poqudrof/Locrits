# Locrits Testing Guide

## Quick Start

Run the complete test suite:

```bash
./run_tests.sh
```

## Test Suite Overview

The test suite includes:

### 🐍 Backend Tests
- Python syntax validation
- Module import checks
- Config file validation
- Memory service factory tests
- Unit tests (if available)

### ⚛️ Frontend Tests
- TypeScript type checking
- ESLint code quality checks
- Build validation
- Unit tests (if available)

### 🧠 Memory Service Tests
- Plaintext memory service initialization
- LanceDB LangChain service (if dependencies available)
- Memory factory service enumeration
- Memory progression tests

### 🔗 Integration Tests
- Backend API health checks
- Locrits API endpoint validation
- Frontend/Backend connectivity

### 📦 Dependency Checks
- Python package compatibility
- Security vulnerability scanning (with `safety`)

## Usage

### Run All Tests
```bash
./run_tests.sh
```

### Skip Specific Test Suites
```bash
# Skip frontend tests
./run_tests.sh --skip-frontend

# Skip backend tests
./run_tests.sh --skip-backend

# Skip memory tests
./run_tests.sh --skip-memory
```

### Help
```bash
./run_tests.sh --help
```

## Prerequisites

### Backend
- Python 3.11+ with virtual environment at `.venv`
- All dependencies installed: `pip install -r requirements.txt`

### Frontend
- Node.js 18+
- Dependencies installed: `cd frontend && npm install`

### Optional
- `safety` for security checks: `pip install safety`
- Backend server running at `http://localhost:5000` (for integration tests)
- Frontend dev server at `http://localhost:5173` (for integration tests)

## Test Output

The script provides color-coded output:
- 🟢 **Green** - Tests passed
- 🔴 **Red** - Tests failed
- 🟡 **Yellow** - Warnings or skipped tests
- 🔵 **Blue** - Information messages

### Example Output
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 MEMORY SERVICE TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Running: Plaintext memory service
✅ Plaintext memory service passed

Running: Memory factory services
✅ Memory factory services passed
```

### Summary Report
At the end, you'll see:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 TEST SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Passed: 12
❌ Failed: 2
⏱️  Duration: 45s

⚠️  Some tests failed. Please review the output above.
```

## Exit Codes

- `0` - All tests passed
- `1` - Some tests failed

## Adding New Tests

### Backend Unit Tests
Create `tests/test_backend.py`:
```python
import pytest

def test_example():
    assert 1 + 1 == 2
```

### Frontend Tests
Add to `frontend/package.json`:
```json
{
  "scripts": {
    "test": "vitest"
  }
}
```

### Memory Tests
Create custom memory test scripts and they'll be automatically detected.

## Continuous Integration

This script can be integrated into CI/CD pipelines:

### GitHub Actions
```yaml
- name: Run Tests
  run: ./run_tests.sh
```

### GitLab CI
```yaml
test:
  script:
    - ./run_tests.sh
```

## Troubleshooting

### Virtual Environment Not Found
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend Dependencies Missing
```bash
cd frontend
npm install
```

### Permission Denied
```bash
chmod +x run_tests.sh
```

### Memory Service Tests Failing
- Ensure Ollama is running for LanceDB tests: `http://localhost:11434`
- Check `data/memory/` directory has write permissions
- Verify memory service configuration in `config.yaml`

### Integration Tests Skipped
Start the servers before running tests:
```bash
# Terminal 1: Backend
source .venv/bin/activate
python src/web_app.py

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Tests
./run_tests.sh
```

## Test Coverage

To generate test coverage reports:

### Python Coverage
```bash
pip install pytest-cov
pytest --cov=src tests/
```

### Frontend Coverage
```bash
cd frontend
npm run test:coverage  # If configured
```

## Performance Testing

For load testing and performance benchmarks:
```bash
# Install locust
pip install locust

# Run performance tests
locust -f tests/performance_test.py
```

## Security Testing

Additional security checks:
```bash
# Python security
pip install bandit
bandit -r src/

# Dependency vulnerabilities
pip install safety
safety check

# Frontend security
cd frontend
npm audit
```

## Debugging Failed Tests

1. **Check logs**: Review the colored output for specific error messages
2. **Run individually**: Use `--skip-*` flags to isolate failing test suites
3. **Verbose mode**: Edit script to add `-v` or `--verbose` flags to test commands
4. **Manual execution**: Run failing test commands directly for detailed output

## Best Practices

1. **Run tests before committing**: `./run_tests.sh`
2. **Fix warnings**: Even warnings can indicate potential issues
3. **Keep dependencies updated**: Regular `pip list --outdated` checks
4. **Add tests for new features**: Maintain test coverage
5. **Document test failures**: Create issues for reproducible failures

## Related Documentation

- [Memory Service Abstraction](MEMORY_SERVICE_ABSTRACTION.md)
- [Memory Test Progression](test_memory_progression_README.md)
- [Playwright Tests](TESTING.md) - UI/E2E tests
- [Frontend README](frontend/README.md)

## Support

For issues or questions about testing:
1. Check this documentation
2. Review test output carefully
3. Check individual test files for specific requirements
4. Report bugs with full test output
