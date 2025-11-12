# Backend API Versioning Migration

## Overview
The backend has been successfully reorganized to support API versioning. The current logic has been moved to v1, and the structure is ready for v2 implementation using LangChain.

## New Structure

```
Backend/
├── api/
│   ├── __init__.py           # Main router that includes v1 and v2
│   ├── v1/                   # Current OpenAI function calling approach
│   │   ├── __init__.py
│   │   ├── document.py       # Document endpoints
│   │   ├── placeholder.py    # Placeholder endpoints
│   │   ├── models/           # V1 data models
│   │   │   ├── __init__.py
│   │   │   └── models.py
│   │   ├── repository/       # V1 repository layer
│   │   │   ├── __init__.py
│   │   │   └── document_repository.py
│   │   ├── services/         # V1 business logic
│   │   │   ├── __init__.py
│   │   │   ├── document_service.py
│   │   │   ├── document_generator_service.py
│   │   │   └── placeholder_service.py
│   │   └── app/              # V1 OpenAI handlers
│   │       └── openai/
│   │           ├── __init__.py
│   │           ├── filler.py
│   │           └── parser.py
│   └── v2/                   # Future LangChain-based approach
│       ├── __init__.py
│       ├── document.py       # V2 document endpoints (to be implemented)
│       └── placeholder.py    # V2 placeholder endpoints (to be implemented)
├── config/                   # Shared configuration (used by all versions)
│   ├── __init__.py
│   ├── config.py
│   └── config.yml
├── database/                 # Shared database connection (used by all versions)
│   ├── __init__.py
│   └── database.py
├── uploads/                  # Shared uploads directory
│   └── generated/
├── main.py                   # Server entry point
├── server.py                 # FastAPI app initialization
├── poc.py                    # Proof of concept scripts
├── pyproject.toml            # Poetry dependencies
└── README.md
```

## API Routes

### V1 Routes (OpenAI Function Calling)
- `GET /api/v1/documents/` - Health check
- `POST /api/v1/documents/upload` - Upload and process document
- `POST /api/v1/documents/generate` - Generate filled document
- `POST /api/v1/placeholders/start` - Start conversation session
- `POST /api/v1/placeholders/continue` - Continue conversation

### V2 Routes (LangChain - To Be Implemented)
- `GET /api/v2/documents/` - Health check
- `POST /api/v2/documents/upload` - Upload using LangChain
- `POST /api/v2/documents/generate` - Generate using LangChain
- `POST /api/v2/placeholders/start` - Start LangChain session
- `POST /api/v2/placeholders/continue` - Continue LangChain conversation

## Shared Components

The following components remain shared between v1 and v2:
- **config/** - Configuration and settings
- **uploads/** - File storage directory
- **poc.py** - Proof of concept scripts
- **main.py** - Server entry point
- **server.py** - FastAPI app initialization

## Clean Structure

All v1-specific code has been moved into the `api/v1/` directory. The top-level now contains only shared resources and versioned APIs:

### Shared Components (Used by All Versions):
- **config/** - Configuration and settings
- **database/** - MongoDB connection (shared by v1 and v2)
- **uploads/** - File storage directory

### Version-Specific Components:
- **api/v1/** - Complete v1 implementation (OpenAI)
- **api/v2/** - Ready for v2 implementation (LangChain)

### Server Files:
- **main.py** - Server entry point
- **server.py** - FastAPI app initialization
- **pyproject.toml** - Dependencies

## Next Steps for V2

1. Implement LangChain-based document processing in `api/v2/`
2. Create v2-specific services and logic
3. **Shared Resources** you can reuse:
   - `database/` - MongoDB connection is already shared
   - `config/` - Configuration settings
   - `uploads/` - File storage
4. You may choose to:
   - Share v1 models if the data structure remains the same
   - Create v2-specific models in `api/v2/models/` if needed
   - Create v2-specific repositories in `api/v2/repository/` if needed
5. Update `api/v2/document.py` and `api/v2/placeholder.py` with LangChain logic

## Testing

To test the new structure:

```powershell
# Start the server
poetry run python main.py

# Test v1 endpoints
curl http://localhost:8000/api/v1/documents/

# Test v2 endpoints (should return 501 Not Implemented)
curl http://localhost:8000/api/v2/documents/
```

## Frontend Changes Required

The frontend will need to update API endpoints from:
- `/api/documents/*` → `/api/v1/documents/*`
- `/api/placeholders/*` → `/api/v1/placeholders/*`

Or keep using `/api/documents/*` if you update the main router accordingly.
