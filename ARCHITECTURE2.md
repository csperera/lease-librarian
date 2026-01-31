# Lease Librarian v1.0 beta - System Architecture Documentation

## Table of Contents
1. [High-Level System Architecture](#high-level-system-architecture)
2. [Data Flow - Lease Upload](#data-flow-lease-upload)
3. [Data Flow - Chat Query (RAG)](#data-flow-chat-query-rag)
4. [Module Deep Dive](#module-deep-dive)
5. [Technology Stack](#technology-stack)
6. [Key Architectural Concepts](#key-architectural-concepts)

---

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND LAYER                             │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  React Dashboard (lease-digitizer-final.html)               │    │
│  │  - Tailwind CSS styling                                     │    │
│  │  - Three-panel layout (Library, Chat, Details)              │    │
│  │  - Fetch API for HTTP requests                              │    │
│  └─────────────────────────────────────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP (Port 8001)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           API LAYER                                 │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  FastAPI Router (src/api/main.py)                           │    │
│  │                                                             │    │
│  │  Endpoints:                                                 │    │
│  │  - POST   /api/v1/leases/batch    (upload)                  │    │
│  │  - GET    /api/v1/leases          (list all)                │    │
│  │  - GET    /api/v1/leases/{id}     (get details)             │    │
│  │  - POST   /api/v1/chat            (chat query)              │    │
│  │  - GET    /api/v1/health          (health check)            │    │
│  └─────────────────────────────────────────────────────────────┘    │
└───────────────────┬──────────────────┬──────────────────┬───────────┘
                    │                  │                  │
                    ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER                               │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  Lease Storage   │  │  Vector Store    │  │   AI Agents      │   │
│  │                  │  │                  │  │                  │   │
│  │  - JSON file     │  │  - FAISS index   │  │  1. Classifier   │   │
│  │  - CRUD ops      │  │  - Embeddings    │  │  2. Extractor    │   │
│  │  - Type safe     │  │  - Similarity    │  │  3. Librarian    │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
└───────────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                              │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  OpenAI API                                                 │    │
│  │  - GPT-4 for extraction and chat                            │    │
│  │  - text-embedding-ada-002 for vectors                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow - Lease Upload

```
USER                 API              CLASSIFIER         EXTRACTOR         STORAGE         VECTOR STORE      OPENAI
 │                    │                    │                  │                │                 │             │
 │  POST /leases      │                    │                  │                │                 │             │
 ├───────────────────>│                    │                  │                │                 │             │
 │                    │                    │                  │                │                 │             │
 │                    │  classify()        │                  │                │                 │             │
 │                    ├───────────────────>│                  │                │                 │             │
 │                    │                    │  validate format │                │                 │             │
 │                    │                    │──────────────────│                │                 │             │
 │                    │  ✓ is lease        │                  │                │                 │             │
 │                    │<───────────────────┤                  │                │                 │             │
 │                    │                    │                  │                │                 │             │
 │                    │  extract_data()    │                  │                │                 │             │
 │                    ├────────────────────────────────────────>               │                 │             │
 │                    │                    │                  │  GPT-4 prompt  │                 │             │
 │                    │                    │                  ├────────────────────────────────────────────────>
 │                    │                    │                  │                │                 │  structured │
 │                    │                    │                  │<────────────────────────────────────────────────┤
 │                    │                    │                  │  Pydantic      │                 │      JSON   │
 │                    │                    │                  │  validate()    │                 │             │
 │                    │                    │                  │────────────────│                 │             │
 │                    │  Lease object      │                  │                │                 │             │
 │                    │<────────────────────────────────────────               │                 │             │
 │                    │                    │                  │                │                 │             │
 │                    │  add_lease()       │                  │                │                 │             │
 │                    ├────────────────────────────────────────────────────────>                 │             │
 │                    │                    │                  │  write JSON    │                 │             │
 │                    │                    │                  │                │─────────────────│             │
 │                    │  ✓ lease_id        │                  │                │                 │             │
 │                    │<────────────────────────────────────────────────────────┤                 │             │
 │                    │                    │                  │                │                 │             │
 │                    │  add_to_vector()   │                  │                │                 │             │
 │                    ├────────────────────────────────────────────────────────────────────────>│             │
 │                    │                    │                  │                │  embed text     │             │
 │                    │                    │                  │                │                 ├────────────>│
 │                    │                    │                  │                │  vectors        │             │
 │                    │                    │                  │                │                 │<────────────┤
 │                    │                    │                  │                │  FAISS.add()    │             │
 │                    │                    │                  │                │                 │─────────────│
 │                    │  ✓ indexed         │                  │                │                 │             │
 │                    │<────────────────────────────────────────────────────────────────────────┤             │
 │                    │                    │                  │                │                 │             │
 │  200 OK + ID       │                    │                  │                │                 │             │
 │<───────────────────┤                    │                  │                │                 │             │
 │                    │                    │                  │                │                 │             │
```

**Key Steps:**
1. **Classification**: Validates document is a lease
2. **Extraction**: LLM parses unstructured text → structured JSON
3. **Validation**: Pydantic ensures data quality
4. **Storage**: Write to lease_store.json
5. **Vectorization**: Convert to embeddings and add to FAISS index

---

## Data Flow - Chat Query (RAG)

```
USER               API            LIBRARIAN       VECTOR STORE      STORAGE        OPENAI
 │                  │                  │                 │              │             │
 │  "Which leases   │                  │                 │              │             │
 │   expire in      │                  │                 │              │             │
 │   2025?"         │                  │                 │              │             │
 ├─────────────────>│                  │                 │              │             │
 │                  │                  │                 │              │             │
 │                  │  chat()          │                 │              │             │
 │                  ├─────────────────>│                 │              │             │
 │                  │                  │  embed query    │              │             │
 │                  │                  ├─────────────────────────────────────────────>│
 │                  │                  │  query vector   │              │             │
 │                  │                  │<─────────────────────────────────────────────┤
 │                  │                  │                 │              │             │
 │                  │                  │  similarity()   │              │             │
 │                  │                  ├────────────────>│              │             │
 │                  │                  │  FAISS search   │              │             │
 │                  │                  │                 │──────────────│             │
 │                  │                  │  top K IDs      │              │             │
 │                  │                  │<────────────────┤              │             │
 │                  │                  │                 │              │             │
 │                  │                  │  get_details()  │              │             │
 │                  │                  ├──────────────────────────────>│             │
 │                  │                  │  lease data     │              │             │
 │                  │                  │<──────────────────────────────┤             │
 │                  │                  │                 │              │             │
 │                  │                  │  build context  │              │             │
 │                  │                  │─────────────────│              │             │
 │                  │                  │                 │              │             │
 │                  │                  │  GPT-4 prompt:  │              │             │
 │                  │                  │  - Question     │              │             │
 │                  │                  │  - Context      │              │             │
 │                  │                  │  - History      │              │             │
 │                  │                  ├─────────────────────────────────────────────>│
 │                  │                  │                 │              │  NL answer  │
 │                  │                  │<─────────────────────────────────────────────┤
 │                  │                  │                 │              │             │
 │                  │  response +      │                 │              │             │
 │                  │  sources         │                 │              │             │
 │                  │<─────────────────┤                 │              │             │
 │                  │                  │                 │              │             │
 │  Answer with     │                  │                 │              │             │
 │  source leases   │                  │                 │              │             │
 │<─────────────────┤                  │                 │              │             │
 │                  │                  │                 │              │             │
```

**Key Steps (RAG Pattern):**
1. **Embed Query**: Convert user question to vector
2. **Retrieve**: FAISS finds semantically similar leases
3. **Augment**: Build context from relevant lease data
4. **Generate**: GPT-4 answers using context
5. **Attribute**: Return sources with answer

---

## Module Deep Dive

### Project Structure

```
lease-digitizer/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── document_classifier.py       # Agent 1: Classification
│   │   ├── lease_extractor.py           # Agent 2: Extraction
│   │   └── lease_librarian.py           # Agent 3: Chat
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py                      # FastAPI routes
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── lease.py                     # Pydantic models
│   │
│   └── storage/
│       ├── __init__.py
│       ├── lease_storage.py             # JSON persistence
│       ├── lease_vector_store.py        # FAISS vector DB
│       └── lease_store.json             # Data file
│
├── run_api.py                           # API server entry point
├── upload_demo_leases.py                # Batch upload script
├── demo_leases_batch.json               # Demo data
├── lease-digitizer-final.html           # Frontend
└── demo-lease.pdf                       # Sample PDF
```

### Module 1: `schemas/lease.py` - Data Models

**Purpose**: Type-safe data structures using Pydantic

**Key Classes**:
```python
class Lease(BaseModel):
    """Main lease model - validates ALL lease data"""
    id: str
    document_id: str
    tenant: str
    landlord: str
    property_address: str
    lease_type: str
    rentable_square_feet: int
    annual_rent: float
    lease_rate_per_sf: float
    lease_commencement_date: str
    lease_expiration_date: str
    lease_term_months: int
    parking_spaces: int
    renewal_options: str
    lease_summary: Optional[str]
    created_at: str
```

**Why Pydantic?**
- Automatic validation (e.g., `annual_rent` must be float)
- Type coercion (converts "123" → 123)
- JSON serialization/deserialization
- Clear error messages when validation fails

---

### Module 2: `storage/lease_storage.py` - Data Persistence

**Purpose**: CRUD operations for lease data

**Key Methods**:
```python
class LeaseStorage:
    def __init__(self, storage_path: str):
        """Initialize with path to lease_store.json"""
        
    def add_lease(self, lease: Lease) -> str:
        """Add new lease, returns lease_id"""
        
    def get_lease(self, lease_id: str) -> Optional[Lease]:
        """Retrieve lease by ID"""
        
    def get_all_leases(self) -> List[Lease]:
        """Get all leases for list view"""
        
    def _load_data(self) -> dict:
        """Load from JSON file"""
        
    def _save_data(self, data: dict):
        """Write to JSON file"""
```

**Storage Format** (lease_store.json):
```json
{
  "leases": {
    "GS-11P-LDC00100": {
      "id": "GS-11P-LDC00100",
      "tenant": "General Services Administration",
      "landlord": "Sentinel Square III, LLC",
      ...
    }
  }
}
```

**Why JSON?**
- Simple, human-readable
- Easy to inspect/debug
- No database setup needed
- Production would use PostgreSQL

---

### Module 3: `storage/lease_vector_store.py` - Vector Database

**Purpose**: Semantic search using FAISS

**Key Methods**:
```python
class LeaseVectorStore:
    def __init__(self):
        """Initialize FAISS index and embeddings"""
        self.embeddings = OpenAIEmbeddings()
        self.index = None
        self.lease_ids = []
        
    def add_lease(self, lease: Lease):
        """Convert lease to embedding, add to FAISS"""
        text = self._lease_to_text(lease)
        vector = self.embeddings.embed_query(text)
        self.index.add(vector)
        
    def similarity_search(self, query: str, k: int = 3):
        """Find top K most similar leases"""
        query_vector = self.embeddings.embed_query(query)
        distances, indices = self.index.search(query_vector, k)
        return [self.lease_ids[i] for i in indices]
```

**How it works**:
1. **Text Representation**: Lease → "Tenant: GSA, Address: 45 L Street, Rate: $49/SF..."
2. **Embedding**: Text → 1536-dimensional vector (OpenAI)
3. **Indexing**: Vector added to FAISS index
4. **Search**: Query vector compared to all lease vectors using cosine similarity

**Why FAISS?**
- Fast: Searches millions of vectors in milliseconds
- Memory efficient: Optimized for high-dimensional vectors
- Battle-tested: Used by Facebook, Meta

---

### Module 4: `agents/document_classifier.py` - Agent 1

**Purpose**: Validate document is a commercial lease

**Key Methods**:
```python
class DocumentClassifier:
    def classify_document(self, content: str) -> ClassificationResult:
        """
        Determines if document is a lease
        Returns: confidence score + document type
        """
```

**How it works**:
- Uses regex/heuristics to look for lease indicators
- Keywords: "Lessor", "Lessee", "Premises", "Rent"
- Returns confidence: 0.0 - 1.0

**Why separate classifier?**
- Fail fast: Don't waste LLM calls on non-leases
- Quality gate: Ensures only valid docs reach extraction
- Extensible: Can add more document types later

---

### Module 5: `agents/lease_extractor.py` - Agent 2

**Purpose**: Extract structured data from unstructured lease text

**Key Methods**:
```python
class LeaseExtractorAgent:
    def extract_lease(self, content: str) -> Lease:
        """
        Uses GPT-4 to extract 15+ fields
        Returns: Validated Lease object
        """
        
    def _build_extraction_prompt(self, content: str) -> str:
        """Creates prompt with examples and schema"""
```

**Extraction Prompt**:
```
You are a commercial real estate expert extracting lease data.

Extract the following fields:
- tenant (organization name)
- landlord (organization name)
- property_address (full street address)
- rentable_square_feet (integer)
- annual_rent (float)
...

Respond ONLY with valid JSON matching this schema.

LEASE TEXT:
{content}
```

**LLM Response** (structured JSON):
```json
{
  "tenant": "General Services Administration",
  "landlord": "Sentinel Square III, LLC",
  "property_address": "45 L Street, NE, Washington, DC 20002",
  "rentable_square_feet": 85000,
  "annual_rent": 4165000.00,
  ...
}
```

**Then**: Pydantic validates before storage

**Why LLM extraction?**
- Handles unstructured data
- Adapts to different lease formats
- Extracts nuanced information (not just regex)
- Can handle tables, lists, legal language

---

### Module 6: `agents/lease_librarian.py` - Agent 3

**Purpose**: Natural language chat interface using RAG

**Key Methods**:
```python
class LeaseLibrarian:
    def __init__(self, vector_store, storage):
        """Initialize with access to vectors and data"""
        
    def chat(self, message: str, conversation_id: str):
        """
        Answer questions about lease portfolio
        Uses RAG pattern
        """
        # 1. Retrieve relevant leases
        lease_ids = self.vector_store.similarity_search(message)
        leases = [self.storage.get_lease(id) for id in lease_ids]
        
        # 2. Build context
        context = self._build_context(leases)
        
        # 3. Generate answer
        prompt = f"""
        Context: {context}
        Question: {message}
        Answer:
        """
        response = self.llm.invoke(prompt)
        
        return response, lease_ids  # Answer + sources
```

**RAG Pattern Explained**:

**WITHOUT RAG** (naive approach):
```
User: "Which leases expire in 2025?"
GPT-4: "I don't have access to your lease data."
```

**WITH RAG** (what we built):
```
User: "Which leases expire in 2025?"

Step 1 - RETRIEVE:
Vector search finds leases about expiration dates

Step 2 - AUGMENT:
Build context:
"Lease GS-11P-LDC00200 expires May 31, 2025
 Lease GS-11P-LDC00800 expires Oct 31, 2025
 ..."

Step 3 - GENERATE:
GPT-4: "Based on your portfolio, 2 leases expire in 2025:
1. GS-11P-LDC00200 (Dept of Commerce) - May 31, 2025
2. GS-11P-LDC00800 (Dept of Energy) - Oct 31, 2025"
```

**Why RAG?**
- Grounds responses in actual data
- Provides source attribution
- Reduces hallucinations
- Works with private/recent data not in training

---

### Module 7: `api/main.py` - API Router

**Purpose**: HTTP endpoints connecting frontend to backend

**Key Endpoints**:

```python
@app.post("/api/v1/leases/batch")
async def upload_leases(request: BatchUploadRequest):
    """
    Upload multiple leases
    Calls: Classifier → Extractor → Storage → VectorStore
    Returns: List of created lease IDs
    """
    
@app.get("/api/v1/leases")
async def list_leases():
    """
    Get all leases for library view
    Returns: Simplified lease previews
    """
    
@app.get("/api/v1/leases/{lease_id}")
async def get_lease(lease_id: str):
    """
    Get full lease details
    Returns: Complete Lease object
    """
    
@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """
    Chat with Lease Librarian
    Calls: LeaseLibrarian.chat() with RAG
    Returns: Answer + source lease IDs
    """
```

**Service Initialization**:
```python
# On startup, create all services
services = {
    "storage": LeaseStorage("src/storage/lease_store.json"),
    "vector_store": LeaseVectorStore(),
    "extractor": LeaseExtractorAgent(),
    "librarian": LeaseLibrarian(vector_store, storage)
}
```

**Why FastAPI?**
- Auto-generated docs (Swagger UI)
- Async support for performance
- Type hints → automatic validation
- Modern Python framework

---

## Technology Stack

### Frontend
- **React 18**: Component-based UI
- **Tailwind CSS**: Utility-first styling
- **Babel Standalone**: In-browser JSX compilation
- **Fetch API**: HTTP client

### Backend
- **Python 3.11**: Modern Python with type hints
- **FastAPI**: High-performance API framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### AI/ML
- **OpenAI GPT-4**: LLM for extraction and chat
- **OpenAI Embeddings**: text-embedding-ada-002
- **LangChain**: Agent orchestration framework
- **FAISS**: Vector similarity search

### Storage
- **JSON**: Simple file-based storage
- **FAISS Index**: In-memory vector database

---

## Key Architectural Concepts

### 1. Multi-Agent Architecture

**Concept**: Instead of one monolithic AI, use specialized agents for specific tasks

**Benefits**:
- **Separation of Concerns**: Each agent has one job
- **Independent Testing**: Can test/improve agents separately
- **Flexibility**: Can swap/upgrade agents independently
- **Clarity**: Code is easier to understand

**Our Agents**:
1. **Classifier**: "Is this a lease?" (Quality gate)
2. **Extractor**: "Extract the data" (LLM + Pydantic)
3. **Librarian**: "Answer questions" (RAG pattern)

---

### 2. RAG (Retrieval Augmented Generation)

**Problem**: GPT-4 doesn't know about your specific leases

**Naive Solution**: Fine-tune a model on your leases
- Expensive
- Requires lots of data
- Hard to update

**RAG Solution**: Give GPT-4 the relevant info on-demand
1. **Retrieve**: Find relevant leases (vector search)
2. **Augment**: Add leases to prompt as context
3. **Generate**: GPT-4 answers using that context

**Why it works**:
- No fine-tuning needed
- Always up-to-date (uses latest data)
- Source attribution (know which leases were used)
- Cost-effective

---

### 3. Vector Embeddings

**Concept**: Convert text to numbers that capture meaning

**How it works**:
```
"45 L Street, $49/SF, GSA lease" 
    → OpenAI Embeddings API 
    → [0.234, -0.567, 0.123, ... ] (1536 numbers)
```

**Key Property**: Similar text → similar vectors

```
"Which leases expire in 2025?" → [0.2, -0.5, 0.1, ...]
"Lease expires May 31, 2025"   → [0.3, -0.4, 0.2, ...]  ← SIMILAR!
"Pizza delivery"               → [0.9, 0.1, -0.8, ...]  ← DIFFERENT!
```

**FAISS**: Finds most similar vectors in milliseconds

---

### 4. Type Safety with Pydantic

**Problem**: LLMs return unstructured text, errors happen

**Solution**: Pydantic validates data at runtime

**Example**:
```python
# LLM returns this JSON:
{
  "annual_rent": "not a number",  # ERROR!
  "parking_spaces": -5             # Doesn't make sense!
}

# Pydantic catches it:
ValidationError: 
  - annual_rent: value is not a valid float
  - parking_spaces: ensure this value is greater than 0
```

**Benefits**:
- Catch errors before they reach storage
- Clear error messages
- Type hints throughout codebase
- Self-documenting code

---

### 5. RESTful API Design

**Principle**: Clean separation between frontend and backend

**Benefits**:
- Can build mobile app using same API
- Can integrate with other systems
- Frontend and backend teams can work independently
- Easy to version and maintain

**Our API**:
```
GET    /api/v1/leases          → List all
GET    /api/v1/leases/{id}     → Get one
POST   /api/v1/leases/batch    → Create many
POST   /api/v1/chat            → Ask question
```

---

## Deep Dive: How a Chat Query Works

Let's trace: **"Which leases expire in 2025?"**

### Step 1: User sends message
```javascript
// Frontend (React)
fetch('http://localhost:8001/api/v1/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: "Which leases expire in 2025?",
    conversation_id: "abc123"
  })
})
```

### Step 2: API receives request
```python
# src/api/main.py
@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    response = services["librarian"].chat(
        request.message,
        request.conversation_id
    )
    return response
```

### Step 3: Librarian embeds query
```python
# src/agents/lease_librarian.py
query_vector = self.embeddings.embed_query(
    "Which leases expire in 2025?"
)
# Returns: [0.234, -0.567, 0.123, ... ] (1536 dims)
```

### Step 4: Vector search finds similar leases
```python
# src/storage/lease_vector_store.py
lease_ids = self.similarity_search(query_vector, k=3)
# Returns: ["GS-11P-LDC00200", "GS-11P-LDC00800", ...]
```

**How FAISS works**:
- Compares query vector to all lease vectors
- Uses cosine similarity: `sim = dot(A, B) / (||A|| * ||B||)`
- Returns top K most similar

### Step 5: Retrieve full lease data
```python
# src/storage/lease_storage.py
leases = [self.storage.get_lease(id) for id in lease_ids]
# Returns: Full Lease objects with all fields
```

### Step 6: Build context
```python
context = """
Lease GS-11P-LDC00200:
- Tenant: Department of Commerce
- Expires: 2025-05-31
- Address: 1800 F Street, NW

Lease GS-11P-LDC00800:
- Tenant: Department of Energy
- Expires: 2025-10-31
- Address: 400 7th Street, SW
"""
```

### Step 7: Generate answer with GPT-4
```python
prompt = f"""
You are a commercial real estate assistant.

Context (relevant leases):
{context}

Question: {message}

Answer the question based ONLY on the provided context.
Cite specific lease IDs in your response.
"""

response = self.llm.invoke(prompt)
```

### Step 8: GPT-4 response
```
Based on your portfolio, 2 leases expire in 2025:

1. GS-11P-LDC00200 (Department of Commerce)
   - Expires: May 31, 2025
   - Location: 1800 F Street, NW, Washington, DC

2. GS-11P-LDC00800 (Department of Energy)
   - Expires: October 31, 2025
   - Location: 400 7th Street, SW, Washington, DC
```

### Step 9: Return to frontend
```python
return {
    "response": response,
    "sources": ["GS-11P-LDC00200", "GS-11P-LDC00800"],
    "conversation_id": "abc123"
}
```

### Step 10: Display in UI
```javascript
// React displays:
// - Response text in chat bubble
// - "Sources: GS-11P-LDC00200, GS-11P-LDC00800" below
```

---

## Production Considerations

### What would change in production?

**Storage**:
- JSON → PostgreSQL or MongoDB
- Proper indexing on lease_id, tenant, expiration_date
- Database migrations

**Vector Store**:
- FAISS in-memory → Pinecone, Weaviate, or Qdrant
- Persistent vector storage
- Distributed search for scale

**Security**:
- API authentication (JWT tokens)
- Rate limiting
- Input validation and sanitization
- HTTPS/SSL

**Observability**:
- Logging (structured logs)
- Monitoring (Prometheus, Grafana)
- Error tracking (Sentry)
- LLM call tracking (token usage, costs)

**Deployment**:
- Docker containers
- Kubernetes orchestration
- Load balancing
- CI/CD pipeline

**Data Quality**:
- Confidence scores on extractions
- Human-in-the-loop review for low confidence
- Feedback loop to improve prompts

---

## Summary: Why This Architecture?

**✅ Scalable**
- Async API handles concurrent requests
- Vector search enables fast retrieval
- Stateless design allows horizontal scaling

**✅ Maintainable**
- Clear separation of concerns
- Type safety catches bugs early
- Modular agents can be improved independently

**✅ Extensible**
- Easy to add new document types (Agent 1)
- Easy to add new extraction fields (Agent 2)
- Easy to add new chat features (Agent 3)

**✅ Production-Ready Patterns**
- RESTful API design
- Data validation with Pydantic
- Error handling throughout
- Standard project structure

**✅ AI Best Practices**
- RAG for grounded responses
- Embeddings for semantic search
- Structured output from LLMs
- Source attribution

---

## Next Steps for Learning

**To deeply understand the code**:

1. **Read in this order**:
   - `schemas/lease.py` (data models)
   - `storage/lease_storage.py` (persistence)
   - `agents/lease_extractor.py` (LLM extraction)
   - `storage/lease_vector_store.py` (vector search)
   - `agents/lease_librarian.py` (RAG chat)
   - `api/main.py` (HTTP endpoints)

2. **Experiments to try**:
   - Add a new field to Lease schema
   - Change the extraction prompt
   - Adjust vector search K parameter
   - Add a new API endpoint

3. **Questions to answer**:
   - What happens if Pydantic validation fails?
   - How does FAISS determine similarity?
   - What's in the LLM prompt for extraction?
   - How does conversation history work in chat?

---

