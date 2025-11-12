# Lexy Backend

AI-powered document placeholder filling system with conversational interface.

## Features

- Upload `.docx` documents and extract placeholders automatically
- Conversational AI guides users through filling placeholders
- Generate completed documents with filled values
- Two API versions: V1 (OpenAI Function Calling) and V2 (LangChain Agents)


## Quick Start

**1. Install Dependencies:**
```bash
poetry install
```

**2. Configure:**
Update `config/config.yml`:
```yaml
database:
  connection_string: mongodb://localhost:27017
  name: lexy

openai:
  api_key: sk-proj-your-openai-api-key-here
  model: gpt-4o-mini
  parser_assistant_id: asst_your_parser_assistant_id  # Required for V1
  filler_assistant_id: asst_your_filler_assistant_id  # Required for V1
```

**3. Run Server:**
```bash
python main.py
# Server runs on http://localhost:8000
```

## Project Structure

```
Backend/
├── api/
│   ├── v1/              # OpenAI Function Calling API
│   └── v2/              # LangChain Agent-Based API
├── config/              # Configuration
├── uploads/             # File storage
├── server.py            # FastAPI app
└── main.py              # Entry point
```

## API Versions

### V1 - OpenAI Function Calling
- Direct OpenAI Assistant API integration
- Function calling for placeholder extraction and filling
- Stable and proven approach
- See [api/v1/README.md](api/v1/README.md) for details

### V2 - LangChain Agent Pipeline  
- Agent-based architecture with specialized tools
- Hybrid validation (rule-based + LLM)
- Context-aware placeholder detection
- See [api/v2/README.md](api/v2/README.md) for details

## API Endpoints

### V1 Endpoints
- `POST /api/v1/documents/upload` - Upload document
- `POST /api/v1/documents/generate` - Generate filled document
- `POST /api/v1/placeholders/start` - Start conversation session
- `POST /api/v1/placeholders/continue` - Continue conversation

### V2 Endpoints
- `POST /api/v2/documents/upload` - Upload document
- `POST /api/v2/documents/generate` - Generate filled document
- `POST /api/v2/placeholders/start` - Start conversation session
- `POST /api/v2/placeholders/continue` - Continue conversation
- `POST /api/v2/placeholders/status` - Get session status

## Development

```bash
# Install dependencies
poetry install

# Run server with hot reload
python main.py

# Access API docs
http://localhost:8000/docs
```



