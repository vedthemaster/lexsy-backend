# Lexy Backend - Document Placeholder Filling System

## Project Brief

This backend system provides an intelligent document processing solution that extracts placeholders from uploaded Word documents (`.docx`) and guides users through a conversational interface to fill them. The system leverages OpenAI's Assistant API with function calling capabilities to intelligently identify placeholders and manage user interactions.

### Key Features

- **Document Upload & Processing**: Upload `.docx` files and automatically extract placeholders
- **AI-Powered Placeholder Detection**: Uses OpenAI Assistant API to identify placeholders with context and regex patterns
- **Conversational Interface**: Interactive chat-based system to fill placeholders one by one
- **Document Generation**: Generate filled documents with all placeholder values replaced

## Architecture & Technology Stack

- **Framework**: FastAPI (Python)
- **Database**: MongoDB (using Motor for async operations)
- **AI Integration**: OpenAI Assistant API with Function Calling
- **Document Processing**: python-docx for Word document manipulation
- **API Server**: Uvicorn

## Project Structure

```
Backend/
├── api/                    # API route handlers
│   ├── document.py        # Document upload and generation endpoints
│   └── placeholder.py     # Placeholder filling session endpoints
├── app/
│   └── openai/            # OpenAI integration
│       ├── parser.py      # Placeholder extraction using Assistant API
│       └── filler.py      # Conversational filling using Assistant API
├── services/              # Business logic layer
│   ├── document_service.py
│   ├── document_generator_service.py
│   └── placeholder_service.py
├── repository/            # Data access layer
│   ├── database.py
│   └── document_repository.py
├── models/               # Data models
│   └── models.py
├── config/               # Configuration management
│   └── config.py
├── uploads/              # File storage
│   └── generated/       # Generated documents
├── server.py            # FastAPI application setup
└── main.py              # Application entry point
```

## Logic & Flow

### 1. Document Upload Flow

```
User uploads .docx file
    ↓
Validate file type (.docx only)
    ↓
Save file to uploads/ directory
    ↓
Create OpenAI thread and upload document
    ↓
Assistant API analyzes document
    ↓
extract_placeholders function is called
    ↓
Extract placeholders with name, placeholder text, and regex
    ↓
Store document and placeholders in MongoDB
    ↓
Return document_id to user
```

### 2. Placeholder Filling Flow

```
User starts filling session with document_id
    ↓
Create OpenAI thread with document context
    ↓
Send initial message with placeholder list
    ↓
Assistant asks for first placeholder value
    ↓
User provides value
    ↓
Assistant calls save_placeholder function
    ↓
Backend saves value to database
    ↓
Assistant moves to next placeholder
    ↓
Repeat until all placeholders filled
    ↓
Return completion status
```

### 3. Document Generation Flow

```
User requests document generation
    ↓
Validate all placeholders are filled
    ↓
Load original document
    ↓
Replace placeholders using regex patterns:
    - Unique regex: Replace ALL occurrences
    - Duplicate regex: Replace FIRST occurrence per placeholder
    ↓
Save filled document to uploads/generated/
    ↓
Return downloadable file
```

## OpenAI Assistant API Function Calling

This project leverages OpenAI's Assistant API with **function calling** (also known as tool calling) to enable the AI assistant to interact with the backend system. Function calling allows the assistant to request specific actions from the backend, which are then executed and the results are returned to the assistant.

### How Function Calling Works

1. **Assistant Configuration**: Two OpenAI Assistants are configured:
   - **Parser Assistant**: Used during document upload to extract placeholders
   - **Filler Assistant**: Used during conversational filling sessions

2. **Function Definitions**: Each assistant has access to specific functions:
   - The Parser Assistant can call `extract_placeholders`
   - The Filler Assistant can call `save_placeholder`

3. **Execution Flow**:
   ```
   User/System sends message to Assistant
        ↓
   Assistant processes message and decides to call function
        ↓
   Run status becomes "requires_action"
        ↓
   Backend extracts function call details
        ↓
   Backend executes the function (save to DB, extract data, etc.)
        ↓
   Backend submits function results back to Assistant
        ↓
   Assistant continues conversation with function results
        ↓
   Run completes and returns response to user
   ```

4. **Polling Mechanism**: The backend uses a polling loop (`_wait_for_run_completion`) to:
   - Check run status periodically
   - Detect when function calls are required
   - Execute backend logic
   - Submit results back to the assistant
   - Continue until the run completes

### Function Implementations

#### 1. `extract_placeholders`

**Purpose**: Extracts all placeholders from a document with their context, location, and regex patterns for replacement.

**When Called**: During document upload/processing phase by the Parser Assistant.

**Function Schema**:
```json
{
  "name": "extract_placeholders",
  "description": "Extract all placeholders from a document with their context/name, location/regex pattern for replacement",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "placeholders": {
        "type": "array",
        "description": "List of all placeholders found in the document",
        "items": {
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "description": "The context or semantic name of the placeholder (e.g., 'name', 'email', 'address', 'company_name')"
            },
            "placeholder": {
              "type": "string",
              "description": "The actual placeholder text found in the document (e.g., '{{name}}', '[EMAIL]', '<address>')"
            },
            "regex": {
              "type": "string",
              "description": "Regex pattern to find and replace this placeholder in the document"
            }
          },
          "additionalProperties": false,
          "required": [
            "name",
            "placeholder",
            "regex"
          ]
        }
      }
    },
    "additionalProperties": false,
    "required": [
      "placeholders"
    ]
  }
}
```

**Backend Processing** (`app/openai/parser.py`):
- The parser waits for the assistant to call this function
- Extracts the placeholders array from function arguments
- Converts to `PlaceHolder` models and stores in database
- Handles errors if no placeholders found or unexpected function calls

**Example Usage**:
```python
# Assistant analyzes document and calls:
extract_placeholders({
  "placeholders": [
    {
      "name": "company_name",
      "placeholder": "{{COMPANY}}",
      "regex": "\\{\\{COMPANY\\}\\}"
    },
    {
      "name": "investor_name",
      "placeholder": "[INVESTOR]",
      "regex": "\\[INVESTOR\\]"
    }
  ]
})
```

#### 2. `save_placeholder`

**Purpose**: Saves the value provided by the user for a specific placeholder in the document.

**When Called**: During conversational filling sessions by the Filler Assistant, after the user provides a value.

**Function Schema**:
```json
{
  "name": "save_placeholder",
  "description": "Save the value provided by the user for a specific placeholder in the document",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "placeholder_name": {
        "type": "string",
        "description": "The name/context of the placeholder (e.g., 'name', 'email', 'investor_name'). Take if from the given data"
      },
      "value": {
        "type": "string",
        "description": "The value provided by the user for this placeholder"
      }
    },
    "additionalProperties": false,
    "required": [
      "placeholder_name",
      "value"
    ]
  }
}
```

**Backend Processing** (`app/openai/filler.py`):
- Receives `placeholder_name` and `value` from function call
- Retrieves document from database
- Finds matching placeholder by name
- Updates placeholder value in database
- Returns success/failure message to assistant
- Assistant uses this confirmation to continue conversation

**Example Usage**:
```python
# User says: "My company is Acme Corp"
# Assistant calls:
save_placeholder({
  "placeholder_name": "company_name",
  "value": "Acme Corp"
})
# Backend saves to DB and returns: "Successfully saved 'Acme Corp' for placeholder 'company_name'"
# Assistant continues: "Great! Now, what is the investor's name?"
```

## API Endpoints

### Document Endpoints (`/api/documents`)

#### `GET /`
Health check endpoint.

**Response**:
```json
{
  "message": "API is running"
}
```

#### `POST /upload`
Upload a `.docx` document and extract placeholders.

**Request**: Multipart form data with `file` field

**Response**:
```json
{
  "message": "Document uploaded successfully",
  "document_id": "507f1f77bcf86cd799439011",
  "title": "investment_agreement.docx"
}
```

#### `POST /generate`
Generate a filled document with all placeholder values replaced.

**Request Body**:
```json
{
  "document_id": "507f1f77bcf86cd799439011"
}
```

**Response**: Binary file download (`.docx` file)

### Placeholder Endpoints (`/api/placeholders`)

#### `POST /start`
Start a new conversational session for filling placeholders.

**Request Body**:
```json
{
  "document_id": "507f1f77bcf86cd799439011"
}
```

**Response**:
```json
{
  "success": true,
  "thread_id": "thread_abc123",
  "conversation": [
    {
      "role": "assistant",
      "content": "Hello! I'll help you fill in the placeholders. What is the company name?",
      "timestamp": 1234567890
    }
  ],
  "all_filled": false
}
```

#### `POST /continue`
Continue the conversation with a user's response.

**Request Body**:
```json
{
  "document_id": "507f1f77bcf86cd799439011",
  "thread_id": "thread_abc123",
  "message": "Acme Corporation"
}
```

**Response**:
```json
{
  "success": true,
  "conversation": [
    {
      "role": "user",
      "content": "Acme Corporation",
      "timestamp": 1234567891
    },
    {
      "role": "assistant",
      "content": "Thank you! Now, what is the investor's name?",
      "timestamp": 1234567892
    }
  ],
  "all_filled": false,
  "message": "Continue filling placeholders"
}
```

## Configuration

Configuration is managed through `config/config.yml`:

```yaml
database:
  connection_string: "mongodb://localhost:27017"
  name: "lexy_db"

openai:
  api_key: "your-api-key"
  model: "gpt-4"
  parser_assistant_id: "asst_parser123"
  filler_assistant_id: "asst_filler123"
```

## Setup & Installation

1. **Install Dependencies**:
   ```bash
   poetry install
   ```

2. **Configure Environment**:
   - Update `config/config.yml` with your MongoDB connection string
   - Add your OpenAI API key and Assistant IDs

3. **Run the Server**:
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn server:app --reload --port 8000
   ```

## Key Implementation Details

### Placeholder Replacement Logic

The document generator uses intelligent replacement logic:

- **Unique Regex Patterns**: If a regex pattern is used by only one placeholder, it replaces **ALL occurrences** in the document
- **Duplicate Regex Patterns**: If multiple placeholders share the same regex pattern, it replaces only the **FIRST occurrence** per placeholder to avoid conflicts

This ensures accurate replacement even when placeholders appear multiple times or share similar patterns.

### Database Models

- **Document**: Stores document metadata, file path, and list of placeholders
- **PlaceHolder**: Contains name (semantic context), placeholder text, regex pattern, and value (user-provided)

### Error Handling

- File type validation for `.docx` files only
- Validation that all placeholders are filled before document generation
- Proper error messages for missing documents or failed operations
- Graceful handling of OpenAI API errors

## Dependencies

- `fastapi`: Web framework
- `openai`: OpenAI API client
- `motor`: Async MongoDB driver
- `python-docx`: Word document manipulation
- `pydantic`: Data validation
- `uvicorn`: ASGI server
- `pyyaml`: Configuration file parsing

## Future Enhancements

- Support for multiple document formats (PDF, HTML)
- Batch placeholder filling
- Template library management
- User authentication and document ownership
- Version control for filled documents
- Export to multiple formats

