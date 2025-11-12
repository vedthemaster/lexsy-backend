# V1 API - OpenAI Function Calling Architecture

## Overview

V1 uses OpenAI's Assistant API with function calling to extract placeholders and manage conversational filling. This approach leverages OpenAI's native capabilities for tool orchestration.

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         FastAPI Endpoints               │
│  /upload  /start  /continue  /generate  │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│          Services Layer                 │
│  ├─ document_service.py                 │
│  ├─ placeholder_service.py              │
│  └─ document_generator_service.py       │
└──────┬──────────────────────────────────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ OpenAI   │   │ MongoDB  │   │  docx    │
│Assistant │   │ Database │   │ Files    │
└──────────┘   └──────────┘   └──────────┘
```

## Key Components

### 1. Parser (app/openai/parser.py)
- **Purpose**: Extract placeholders from uploaded documents
- **Mechanism**: OpenAI Assistant with `extract_placeholders` function
- **Process**:
  1. Upload document to OpenAI
  2. Create thread and run
  3. Assistant analyzes document
  4. Assistant calls `extract_placeholders` function
  5. Backend receives function call and saves to DB

### 2. Filler (app/openai/filler.py)
- **Purpose**: Guide conversational placeholder filling
- **Mechanism**: OpenAI Assistant with `save_placeholder` function
- **Process**:
  1. Create thread with placeholder context
  2. User provides values
  3. Assistant calls `save_placeholder` function
  4. Backend saves values to DB
  5. Assistant asks for next placeholder

## Function Calling

### extract_placeholders
```json
{
  "name": "extract_placeholders",
  "parameters": {
    "placeholders": [
      {
        "name": "company_name",
        "placeholder": "[COMPANY]",
        "regex": "\\[COMPANY\\]"
      }
    ]
  }
}
```

### save_placeholder
```json
{
  "name": "save_placeholder",
  "parameters": {
    "placeholder_name": "company_name",
    "value": "Acme Corp"
  }
}
```

## Advantages

- ✅ Simple integration with OpenAI's tools
- ✅ Native conversation management
- ✅ Built-in context handling
- ✅ Proven and stable

## Flow Diagram

### Upload Flow
```
Document Upload → OpenAI Thread → Assistant Analysis → 
Function Call (extract_placeholders) → Save to DB
```

### Conversation Flow
```
Start Session → Create Thread → User Message → 
Assistant Response → Function Call (save_placeholder) → 
Save to DB → Next Question → Repeat
```

## Configuration

Requires in `config/config.yml`:
```yaml
openai:
  api_key: "sk-..."
  model: "gpt-4o-mini"
  parser_assistant_id: "asst_..."
  filler_assistant_id: "asst_..."
```

## Limitations

- Depends on OpenAI Assistant API availability
- Function calling overhead for each interaction
- Less control over validation logic
- Requires pre-created assistants
