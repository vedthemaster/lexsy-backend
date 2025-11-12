# ✅ Conversation History Tracking - CONFIRMED WORKING

## How It Works

### 1. **Start Session** (`/api/v2/placeholders/start`)
```python
# Step 1: Generate initial question
initial_message = await self.filler.generate_initial_question(first_placeholder)

# Step 2: Save to conversation history
conversation_msg = ConversationMessage(
    role="assistant",
    content=initial_message,
    timestamp=datetime.now().isoformat()
)
document.conversation_history.append(conversation_msg)

# Step 3: Save to database
await document_repo_ins.save(document)
```

### 2. **Process Each Message** (`/api/v2/placeholders/continue`)
```python
# Step 1: Load document (with existing conversation history from DB)
document = await document_repo_ins.find_by_id(document_id)

# Step 2: Add user message to history
user_msg = ConversationMessage(
    role="user",
    content=message,
    timestamp=datetime.now().isoformat()
)
document.conversation_history.append(user_msg)

# Step 3: Pass FULL conversation history to agents
conversation_history = [
    {"role": msg.role, "content": msg.content}
    for msg in document.conversation_history
]

# Step 4: Process through agent pipeline (agents use history for context)
result = await self.filler.process_message(
    session_id=session_id,
    placeholder=current_placeholder,
    user_message=message,
    conversation_history=conversation_history,  # ← FULL HISTORY PASSED HERE
    progress=progress
)

# Step 5: Add assistant response to history
assistant_msg = ConversationMessage(
    role="assistant",
    content=response,
    timestamp=datetime.now().isoformat(),
    confidence=result.get("confidence")
)
document.conversation_history.append(assistant_msg)

# Step 6: Save everything back to database
await document_repo_ins.save(document)
```

### 3. **Agents Use Conversation History**

#### **ValueExtractor Agent:**
```python
async def extract(
    self,
    user_message: str,
    placeholder: PlaceHolder,
    conversation_history: list = None,  # ← Receives full history
) -> ExtractionResult:
    # Build history context
    history_str = ""
    if conversation_history:
        recent_history = conversation_history[-4:]  # Last 2 exchanges
        history_str = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in recent_history]
        )
    
    # Uses history in prompt for better context
    prompt = f"""...
RECENT CONVERSATION:
{history_str}

USER'S MESSAGE: "{user_message}"
..."""
```

## Test Flow Example

### Request 1: Start Session
```http
POST /api/v2/placeholders/start
{
    "document_id": "673abc123"
}
```

**Response:**
```json
{
    "session_id": "uuid-1234",
    "message": "What is the company's name?"
}
```

**Database State:**
```json
{
    "_id": "673abc123",
    "conversation_history": [
        {
            "role": "assistant",
            "content": "What is the company's name?",
            "timestamp": "2024-11-11T10:00:00"
        }
    ]
}
```

---

### Request 2: User Response
```http
POST /api/v2/placeholders/continue
{
    "session_id": "uuid-1234",
    "user_message": "Acme Corporation"
}
```

**Agent Processing:**
1. Loads document → gets conversation history: `["assistant: What is the company's name?"]`
2. Adds user message → history becomes: `["assistant: What...", "user: Acme Corporation"]`
3. Passes history to ValueExtractor → uses context to extract "Acme Corporation"
4. Validates → passes
5. Generates response → "Got it! Company Name = Acme Corporation. What is the investor name?"
6. Saves assistant response to history
7. Saves entire document to DB

**Database State:**
```json
{
    "_id": "673abc123",
    "conversation_history": [
        {
            "role": "assistant",
            "content": "What is the company's name?",
            "timestamp": "2024-11-11T10:00:00"
        },
        {
            "role": "user",
            "content": "Acme Corporation",
            "timestamp": "2024-11-11T10:00:15"
        },
        {
            "role": "assistant",
            "content": "Got it! Company Name = Acme Corporation...",
            "timestamp": "2024-11-11T10:00:16",
            "confidence": 0.95
        }
    ],
    "placeholders": [
        {
            "name": "Company Name",
            "value": "Acme Corporation",
            ...
        }
    ]
}
```

---

### Request 3: Another User Response
```http
POST /api/v2/placeholders/continue
{
    "session_id": "uuid-1234",
    "user_message": "John Smith"
}
```

**Agent Processing:**
1. Loads document → gets FULL conversation history (3 messages)
2. Adds user message → history becomes 4 messages
3. Passes **ALL 4 messages** to ValueExtractor
4. ValueExtractor sees context: previous placeholder was company name, now asking for investor
5. Extracts "John Smith" with high confidence (context helps!)
6. Continues...

**Database State:**
```json
{
    "_id": "673abc123",
    "conversation_history": [
        // ... 3 previous messages ...
        {
            "role": "user",
            "content": "John Smith",
            "timestamp": "2024-11-11T10:00:30"
        },
        {
            "role": "assistant",
            "content": "Great! Investor Name = John Smith...",
            "timestamp": "2024-11-11T10:00:31",
            "confidence": 0.92
        }
    ],
    "placeholders": [
        {
            "name": "Company Name",
            "value": "Acme Corporation"
        },
        {
            "name": "Investor Name",
            "value": "John Smith"
        }
    ]
}
```

---

## Verify Conversation History

### GET Session Status
```http
POST /api/v2/placeholders/status
{
    "session_id": "uuid-1234"
}
```

**Response:**
```json
{
    "session_id": "uuid-1234",
    "document_id": "673abc123",
    "filled_count": 2,
    "total_count": 11,
    "completed": false,
    "conversation_history": [
        {
            "role": "assistant",
            "content": "What is the company's name?",
            "timestamp": "2024-11-11T10:00:00",
            "confidence": null
        },
        {
            "role": "user",
            "content": "Acme Corporation",
            "timestamp": "2024-11-11T10:00:15",
            "confidence": null
        },
        {
            "role": "assistant",
            "content": "Got it! Company Name = Acme Corporation...",
            "timestamp": "2024-11-11T10:00:16",
            "confidence": 0.95
        },
        {
            "role": "user",
            "content": "John Smith",
            "timestamp": "2024-11-11T10:00:30",
            "confidence": null
        },
        {
            "role": "assistant",
            "content": "Great! Investor Name = John Smith...",
            "timestamp": "2024-11-11T10:00:31",
            "confidence": 0.92
        }
    ]
}
```

---

## Key Benefits

✅ **Persistent Storage**: All messages saved to MongoDB
✅ **Context Awareness**: Agents see previous conversation for better extraction
✅ **Confidence Tracking**: Each response includes confidence score
✅ **Timestamps**: Full audit trail of conversation
✅ **Session Recovery**: Can resume conversation after server restart
✅ **Debug-Friendly**: Can review entire conversation via `/status` endpoint

---

## Implementation Details

### Models (`api/v2/models/models.py`)
```python
class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    confidence: Optional[float] = None

class Document(MongoModel):
    # ... other fields ...
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
```

### Repository (`api/v2/repository/document_repository.py`)
```python
async def save(self, document: Document) -> Document:
    if document.id:
        # Update existing - includes conversation_history automatically
        doc_dict = document.model_dump(by_alias=True, exclude={"id"})
        await self.collection.update_one(
            {"_id": ObjectId(document.id)},
            {"$set": doc_dict}
        )
```

### Service (`api/v2/services/placeholder_service.py`)
- Loads document (with history) from DB
- Appends new messages to `document.conversation_history`
- Passes history to agents
- Saves updated document back to DB

---

## Summary

🎯 **YES, conversation history IS being tracked and saved!**

Every user message and assistant response is:
1. Stored in `document.conversation_history` array
2. Saved to MongoDB
3. Loaded on next request
4. Passed to agents for context-aware processing
5. Accessible via `/status` endpoint

The system maintains full conversational context throughout the entire placeholder filling session! 🚀
