# Test Failures - Fix List

## Summary
- ✅ Passed: 8 tests
- ❌ Failed: 6 tests
- ⏱️ Duration: 12s

---

## 🔴 CRITICAL FAILURES

### 1. Config Loading Failed (Backend)
**Error:** Config loading test failed
**Location:** Line 23
**Priority:** HIGH
**Fix:**
```bash
# Check config.yaml syntax
python -c 'import yaml; yaml.safe_load(open("config.yaml"))'
```
**Action:** Verify YAML syntax in config.yaml, check for indentation errors

---

### 2. Frontend Build Failed - TypeScript Errors
**Error:** 330+ TypeScript errors in ui/shared components
**Location:** Lines 44-375
**Priority:** CRITICAL
**Root Cause:** Shared UI folder (`ui/shared/`) has missing dependencies

**Errors:**
- Cannot find module 'react'
- Cannot find module '@radix-ui/*'
- Cannot find module 'lucide-react'
- Cannot find module 'class-variance-authority'
- Cannot find module 'clsx'
- Cannot find module 'tailwind-merge'

**Fix:**
```bash
# Option 1: Install all deps in ui/shared (create package.json)
cd ui/shared
npm init -y
npm install react @types/react @radix-ui/react-accordion @radix-ui/react-alert-dialog \
  @radix-ui/react-select lucide-react class-variance-authority clsx tailwind-merge

# Option 2: Don't use ui/shared, use symlinks instead
rm -rf ui/shared
ln -s ../../frontend/node_modules frontend/src/components/ui/node_modules
```

**Recommended Solution:** Revert shared UI approach - keep UI components in frontend and platform separately

---

### 3. ESLint Check Failed (Frontend)
**Error:** ESLint check failed
**Location:** Line 38
**Priority:** MEDIUM
**Fix:**
```bash
cd frontend
npm run lint -- --fix
```

---

### 4. MemoryExplorer TypeScript Errors
**Error:** Type errors in MemoryExplorer.tsx
**Location:** Lines 44-46
```
src/pages/MemoryExplorer.tsx(952,51): error TS2345: Argument of type 'RelatedConcept' is not assignable to parameter of type 'string'.
src/pages/MemoryExplorer.tsx(954,25): error TS2322: Type 'RelatedConcept' is not assignable to type 'ReactNode'.
```
**Priority:** MEDIUM
**Fix:**
```typescript
// In MemoryExplorer.tsx around line 952-954
// Change from:
concept.map((item) => item)  // RelatedConcept object

// To:
concept.map((item) => item.name || String(item))  // Convert to string
```

---

## 🟡 MEDIUM FAILURES

### 5. LanceDB LangChain Service Failed
**Error:** LanceDB LangChain service failed
**Location:** Line 391
**Priority:** MEDIUM
**Root Cause:** Missing dependencies or Ollama not running
**Fix:**
```bash
# Check if dependencies are installed
pip list | grep lancedb
pip list | grep langchain

# If missing:
pip install lancedb tantivy langchain-community

# Check if Ollama is running
curl http://localhost:11434
# If not: ollama serve
```

---

### 6. Memory Factory Services Failed
**Error:** Memory factory services failed
**Location:** Line 393
**Priority:** MEDIUM
**Related to:** LanceDB failure, possible import errors
**Fix:**
```python
# Test manually:
python -c "
from src.services.memory.memory_factory import MemoryServiceFactory
services = MemoryServiceFactory.get_available_services()
print(services)
"
```

---

### 7. Health Endpoint Failed (Integration)
**Error:** Health endpoint failed
**Location:** Line 474
**Priority:** LOW
**Fix:**
```bash
# Check if backend has /health endpoint
grep -r "/health" src/

# If missing, add to web_app.py:
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

---

### 8. Memory Endpoint Returns 500
**Error:** Memory endpoint returns 500 status
**Location:** Line 445
**Priority:** MEDIUM
**Fix:**
```bash
# Check backend logs for memory endpoint error
# Test manually:
curl http://localhost:5000/api/locrits/Bob%20Technique/memory/summary
```

---

## ⚠️ WARNINGS (Not Failures)

### W1. MCP Not Available
**Warning:** MCP not available - BasicMemoryAdapter will not work
**Location:** Lines 19, 383, 389
**Priority:** LOW
**Fix:**
```bash
pip install mcp
```

### W2. No Backend Unit Tests
**Warning:** No backend unit tests found
**Location:** Line 17
**Priority:** LOW
**Action:** Create `tests/test_backend.py` (optional)

### W3. No Frontend Test Script
**Warning:** No frontend test script found
**Location:** Line 376
**Priority:** LOW
**Action:** Add test script to frontend/package.json

### W4. Safety Not Installed
**Warning:** Safety not installed
**Location:** Line 486
**Priority:** LOW
**Fix:** `pip install safety`

---

## 🚫 REMOVE KUZU FROM TESTS

### Changes Needed:

1. **Update run_tests.sh** - Remove Kuzu-specific tests:
```bash
# Remove from memory service tests section:
- Remove Kuzu adapter test
- Remove Kuzu from available services check
```

2. **Update test_memory_progression.py** - Remove Kuzu references:
```python
# Remove any Kuzu-specific test cases
# Only test: plaintext_file, lancedb_langchain, lancedb_mcp, basic_memory, disabled
```

3. **Update documentation** - Mark Kuzu as deprecated:
```markdown
# In MEMORY_SERVICE_ABSTRACTION.md
Kuzu: ❌ DEPRECATED - Known to cause segfaults, removed from tests
```

---

## 📋 FIX PRIORITY ORDER

### Immediate (Do First):
1. ✅ **Fix UI shared folder issue** - Revert to separate UI components or fix dependencies
2. ✅ **Fix config.yaml loading** - Check YAML syntax
3. ✅ **Fix MemoryExplorer TypeScript errors** - Type conversion for RelatedConcept

### Next:
4. ⚙️ Install LanceDB dependencies properly
5. ⚙️ Add /health endpoint to backend
6. ⚙️ Fix memory endpoint 500 error
7. ⚙️ Run ESLint --fix

### Optional:
8. 📦 Install MCP package
9. 📦 Install safety for security checks
10. 📝 Add unit tests

---

## 🔧 QUICK FIX SCRIPT

```bash
#!/bin/bash

# 1. Fix UI components issue - Revert shared UI
echo "Reverting shared UI approach..."
rm -rf ui/shared
# Use platform UI components in frontend via proper imports

# 2. Install missing frontend deps
cd frontend
npm install react @types/react @radix-ui/react-select lucide-react \
  class-variance-authority clsx tailwind-merge

# 3. Install Python deps
cd ..
source .venv/bin/activate
pip install lancedb tantivy langchain-community mcp safety

# 4. Fix MemoryExplorer
# Manual: Edit frontend/src/pages/MemoryExplorer.tsx lines 952-954

# 5. Add health endpoint
# Manual: Add to src/web_app.py

# 6. Re-run tests
./run_tests.sh
```

---

## ✅ SUCCESS CRITERIA

Tests should show:
- ✅ All TypeScript builds successfully
- ✅ Backend config loads without errors
- ✅ Memory services initialize (except Kuzu - removed)
- ✅ API endpoints respond correctly
- ✅ No critical ESLint errors

Target: **0 failed tests**, **All passed** 🎯
