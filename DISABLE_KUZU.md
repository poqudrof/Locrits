# Option: Disable Kuzu Memory

If Kuzu keeps crashing with segfaults on Python 3.13, you have two options:

## Option 1: Downgrade to Python 3.11 or 3.12

Kuzu 0.11.2 may not be fully compatible with Python 3.13.

```bash
# Create new venv with Python 3.11 or 3.12
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Option 2: Disable Kuzu Memory (Use Simple In-Memory Storage)

Edit `config.yaml`:

```yaml
memory:
  enabled: false  # Disable Kuzu
  use_simple_storage: true  # Use dict-based storage instead
```

## Option 3: Use SQLite Instead

Replace Kuzu with SQLite (more stable, no segfaults):

1. Install SQLite support:
```bash
pip install aiosqlite
```

2. Create `src/services/sqlite_memory_service.py` (simple alternative)

## Quick Fix: Disable Memory Completely

Edit `backend/routes/websocket.py`, `chat.py`, etc. and comment out memory operations:

```python
# Comment these lines:
# await memory_manager.save_message(...)
```

This will let the app run without memory persistence until Kuzu is fixed.

## Check Kuzu Compatibility

```bash
# Check if Kuzu works at all
python -c "import kuzu; db = kuzu.Database('/tmp/test_kuzu'); print('OK')"
```

If this crashes, Kuzu is incompatible with your Python version.
