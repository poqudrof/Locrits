# Memory Progression Test for Locrits

## Overview

This test validates a Locrit's ability to remember and recall information about a fictive character across multiple conversations.

## Test Flow

The test creates a fictive character using Faker and progressively shares information with the Locrit:

### Conversation 1: Basic Introduction
- **Information Shared:** Name + Age
- **Example:** "Hello! I want to tell you about someone named John Smith. They are 42 years old."

### Conversation 2: Adding Details
- **Information Shared:** Occupation + City
- **Example:** "John Smith works as a Software Engineer and lives in Seattle."
- **Test:** Ask the Locrit to recall what it knows so far

### Conversation 3: Final Details
- **Information Shared:** Hobby + Pet + Favorite Color + Personality
- **Example:** "John Smith loves photography, has a pet dog, favorite color is blue, and has a cheerful personality."
- **Test:** Ask for complete character description

### Memory Verification

1. **Direct Memory Inspection** - Attempts to query the Locrit's memory endpoint directly
2. **Full Recall Test** - Asks the Locrit to describe everything it remembers
3. **Specific Detail Questions** - Asks targeted questions about individual traits

## Requirements

### Prerequisites

1. **Backend Server Running**
   ```bash
   .venv/bin/python -c "from backend.app import run_app; run_app()"
   ```

2. **Locrit Must Be Active**
   - The target Locrit must be running and configured to respond
   - Default Locrit is "Bob Technique" (can be changed)

3. **Dependencies Installed**
   ```bash
   .venv/bin/pip install Faker
   ```

## Usage

### Basic Usage (Default Locrit)
```bash
.venv/bin/python test_memory_progression.py
```

### With Custom Locrit
```bash
.venv/bin/python test_memory_progression.py "Your Locrit Name"
```

## Expected Results

The test will show:
- ✅ Character generation with all traits
- ✅ Conversation creation success
- ✅ Progressive information sharing across 3 conversations
- ✅ Memory verification attempts
- ✅ Recall test results

### Success Criteria

The Locrit should:
1. Remember the character's name throughout all conversations
2. Accumulate information progressively
3. Recall specific details when asked
4. Maintain context within the conversation

### Common Issues

#### Timeout Errors
```
⚠️ Message request timed out - Locrit may not be running
```
**Solution:** Ensure the Locrit is running and configured in the system

#### Connection Errors
```
❌ Cannot connect to server at http://localhost:5000
```
**Solution:** Start the backend server first

#### Locrit Not Found
The conversation will be created but messages won't get responses.
**Solution:** Use a Locrit name that exists and is configured

## Output Interpretation

### Successful Test Output
```
================================================================================
🧪 LOCRIT MEMORY PROGRESSION TEST
================================================================================

📋 Generated Fictive Character:
   Name: John Smith
   Age: 42
   Occupation: Software Engineer
   ...

✅ Conversation created: abc123-def456...

================================================================================
📝 CONVERSATION 1: Basic Introduction
================================================================================

👤 User: Hello! I want to tell you about someone named John Smith...
🤖 Bob Technique: [Response showing acknowledgment]

[Additional conversations follow...]
```

### Test Validation

Review the responses to verify:
1. ✓ Locrit remembers the name in subsequent messages
2. ✓ Locrit references previous information
3. ✓ Locrit can provide complete character summary
4. ✓ Locrit answers specific questions correctly

## Customization

### Change Base URL
Edit in the script:
```python
BASE_URL = "http://localhost:5000"  # Change to your server URL
```

### Change Default Locrit
Edit in the script:
```python
DEFAULT_LOCRIT = "Bob Technique"  # Change to your Locrit name
```

### Adjust Timeouts
If your Locrit takes longer to respond:
```python
timeout=30  # Increase as needed
```

## Generated Character Traits

The test uses Faker to generate:
- **Name:** Random realistic name
- **Age:** Between 25-65 years
- **Occupation:** Random job title
- **City:** Random city name
- **Hobby:** painting, photography, cooking, gardening, or reading
- **Pet:** dog, cat, parrot, fish, or hamster
- **Favorite Color:** Random color name
- **Personality:** cheerful, thoughtful, energetic, calm, or curious

## Integration with CI/CD

This test can be integrated into automated testing:

```bash
# Start server in background
.venv/bin/python -c "from backend.app import run_app; run_app()" &
SERVER_PID=$!

# Wait for server to be ready
sleep 5

# Run test
.venv/bin/python test_memory_progression.py "Test Locrit"

# Cleanup
kill $SERVER_PID
```

## Troubleshooting

### Server Issues
- Ensure Flask app is running on port 5000
- Check firewall settings
- Verify .env configuration

### Locrit Issues
- Verify Locrit name matches exactly (case-sensitive)
- Check Locrit is marked as online
- Review Locrit configuration and settings

### Memory Issues
- If memory endpoint returns 404, it may not be implemented
- Check conversation history endpoint as fallback
- Review server logs for errors
