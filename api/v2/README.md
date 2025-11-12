# V2 API - LangChain Agent Pipeline Architecture

## Overview

V2 uses a specialized agent pipeline with LangChain for enhanced control over placeholder extraction, validation, and conversational filling. This architecture provides more flexibility and better validation capabilities.

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
│        Placeholder Service              │
│     (Orchestration Layer)               │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         Agent Pipeline                  │
│  ┌────────────────────────────────┐    │
│  │   1. Value Extractor Agent     │    │
│  │   (Extract from conversation)  │    │
│  └────────────┬───────────────────┘    │
│               ▼                         │
│  ┌────────────────────────────────┐    │
│  │   2. Hybrid Validator          │    │
│  │   (Rules + LLM Confidence)     │    │
│  └────────────┬───────────────────┘    │
│               ▼                         │
│  ┌────────────────────────────────┐    │
│  │   3. Response Generator        │    │
│  │   (Natural responses)          │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ OpenAI   │   │ MongoDB  │   │  docx    │
│ LLM API  │   │ Database │   │ Files    │
└──────────┘   └──────────┘   └──────────┘
```

## Key Components

### 1. Parser (app/langchain/parser.py)
**Purpose**: Intelligent placeholder detection with context analysis

**Tools Used**:
- `PlaceholderDetectorTool` - Detects placeholder patterns
- `ContextAnalyzerTool` - Analyzes surrounding context

**Features**:
- Context-aware name extraction for blank placeholders
- Generates helpful question hints
- No type inference (treats all as TEXT for flexibility)

### 2. Agent Pipeline (app/langchain/)

#### 2.1 Value Extractor Agent
```python
ValueExtractor.extract(user_message, placeholder)
→ ExtractionResult(value, confidence, needs_clarification)
```
**Capabilities**:
- Extracts structured values from natural language
- Handles patterns: "my name is X", "it's Y", etc.
- Fallback regex patterns for robust extraction
- Returns confidence scores

#### 2.2 Hybrid Validator
```python
HybridValidator.validate(value, type, context)
→ ValidationResult(is_valid, confidence, message)
```
**Validation Strategy**:
- **Rule-Based** (40-50% weight): Format validation, pattern matching
- **LLM-Based** (50-60% weight): Contextual understanding
- **Combined Score**: Weighted average determines validity
- **Threshold**: 0.5 (lenient acceptance)

**Type Validators**:
- Email: Regex pattern validation
- Phone: Digit extraction and length check
- Date: Date parsing with reasonable range check
- Number: Numeric conversion validation
- Address: Flexible pattern matching (accepts state codes)
- Text: Minimal validation (accepts single chars)

#### 2.3 Response Generator
```python
ResponseGenerator.generate_response(state, placeholder, result)
→ Natural language response
```
**States**:
- `ACCEPTED` - Value validated, ask next question
- `NEEDS_CLARIFICATION` - Unclear input, re-ask
- `INVALID` - Validation failed, show guidance
- `COMPLETED` - All placeholders filled

**Features**:
- Clean, direct responses (no "✓ Got it" confirmations)
- No progress indicators (cleaner UX)
- Context-aware question generation

### 3. Filler (app/langchain/filler.py)
**Purpose**: Orchestrate the 3-agent pipeline

**Process Flow**:
```python
User Message → Value Extractor → Hybrid Validator → Response Generator
                     ↓                  ↓                    ↓
                confidence        is_valid           natural response
```

## Agent Pipeline Flow

```
┌──────────────────┐
│  User Message    │
└────────┬─────────┘
         ▼
    ╔════════════════════╗
    ║ Value Extractor    ║
    ║ - Extract value    ║
    ║ - Check clarity    ║
    ║ - Confidence score ║
    ╚═════════┬══════════╝
              ▼
         extracted?
              │
     ┌────────┴────────┐
     │                 │
    YES               NO
     │                 │
     ▼                 ▼
╔════════════════╗  ╔═══════════════════╗
║ Hybrid         ║  ║ Ask Clarification ║
║ Validator      ║  ╚═══════════════════╝
║ - Rules 40%    ║
║ - LLM 60%      ║
║ - Combined     ║
╚═════┬══════════╝
      ▼
   valid?
      │
  ┌───┴───┐
  │       │
 YES     NO
  │       │
  ▼       ▼
SAVE   RETRY
```

## Advantages

- ✅ No type inference (avoids misclassification)
- ✅ Lenient validation (better UX)
- ✅ Context-aware placeholder naming
- ✅ Hybrid validation (rules + LLM wisdom)
- ✅ Clean responses (no unnecessary confirmations)
- ✅ More control over agent behavior
- ✅ Extensible architecture

## Configuration

```yaml
openai:
  api_key: "sk-..."
  model: "gpt-4o-mini"  # Used across all agents
```

**Temperature Settings**:
- ValueExtractor: 0.1 (consistent extraction)
- HybridValidator: 0.0 (deterministic validation)
- ResponseGenerator: 0.7 (natural responses)

## Session Management

V2 uses `session_id` for tracking conversations:
- Each session mapped to a document
- Conversation history persisted in MongoDB
- Full context available for all agents



## Comparison with V1

| Feature | V1 | V2 |
|---------|----|----|
| Architecture | OpenAI Function Calling | LangChain Agent Pipeline |
| Type Inference | Yes (can misclassify) | No (all TEXT) |
| Validation | Basic | Hybrid (Rules + LLM) |
| Responses | Verbose | Clean & Direct |
| Control | Limited | Full Control |
| Extensibility | Moderate | High |
| Context Handling | OpenAI Managed | Explicit Pipeline |


