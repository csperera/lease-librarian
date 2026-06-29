# Lease Librarian — ARCHITECTURE_LAYERS.md

Lease Librarian is a production multi-agent commercial lease intelligence platform that ingests unstructured lease PDFs and extracts 50+ structured data points in 15 seconds — automating a process that previously took 4-8 hours of manual abstraction. Built on a three-agent pipeline with RAG-powered natural language querying, it solves a critical mortgage underwriting pain point: lenders need accurate tenant income verification and lease term analysis before approving loans on multi-tenant commercial properties.

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                    LEASE LIBRARIAN — 3-AGENT INTELLIGENCE PIPELINE                   ║
║          "4-8 hours of manual lease abstraction → 15 seconds"                        ║
║          Data flow order: Ingest → Classify → Extract → Validate →                   ║
║                           Store → Query → API → Surface                              ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — LEASE INGESTION                                                           │
│                                                                                      │
│  Entry point for all lease documents into the pipeline                               │
│                                                                                      │
│  IN:   Raw lease PDF or text — base leases, amendments, riders                       │
│  OUT:  Raw document text string passed to Document Classifier                        │
│                                                                                      │
│  How it works:                                                                       │
│  → User uploads PDF via React frontend                                               │
│  → POST /api/v1/leases/batch receives file                                           │
│  → pdfplumber / text extraction converts PDF → raw text string                       │
│  → Batch upload script (upload_demo_leases.py) supports bulk ingestion               │
│                                                                                      │
│  V1 limitation → V2:                                                                 │
│  → V1: manual upload via UI or batch script                                          │
│  → V2: S3 event trigger + Airflow DAG for automated ingestion pipeline               │
└──────────────────────────────────────────────────┬───────────────────────────────────┘
                                                   │  raw document text
                                                   ▼
╔══════════════════════════════════════════════════════════════════════════════════════╗
║  LAYER 2 — AGENT 1: DOCUMENT CLASSIFIER        (src/agents/document_classifier.py)   ║
║                                                                                      ║
║  IN:   Raw document text string                                                      ║
║  OUT:  ClassificationResult { is_lease: bool, confidence: float, doc_type: str }     ║
║                                                                                      ║
║  How it works:                                                                       ║
║  → Regex + heuristics scan for lease keywords: "Lessor" "Lessee" "Premises" "Rent"   ║
║  → Returns confidence score 0.0 – 1.0                                                ║
║  → Below threshold → reject immediately, no LLM call wasted                          ║
║                                                                                      ║
║  V1 limitation → V2:                                                                 ║
║  → V1: regex/heuristics only — brittle for unusual lease formats                     ║
║  → V2: lightweight ML classifier trained on document type corpus                     ║
║        add support for appraisals, loan files, financial statements                  ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
                                                   │  confirmed lease text
                                                   ▼
╔══════════════════════════════════════════════════════════════════════════════════════╗
║  LAYER 3 — AGENT 2: LEASE EXTRACTOR           (src/agents/lease_extractor.py)        ║
║                                                                                      ║
║  IN:   Confirmed lease text (passed by Classifier)                                   ║
║  OUT:  Raw JSON string from GPT-4o-mini containing 15+ structured fields             ║
║                                                                                      ║
║  How it works:                                                                       ║
║  → Builds structured extraction prompt:                                              ║
║       "You are a CRE expert. Extract these fields. Respond ONLY in valid JSON."      ║
║  → Sends to GPT-4o-mini via OpenAI API                                               ║
║  → GPT-4 returns raw JSON string                                                     ║
║  → Handles: base leases · amendments · riders                                        ║
║  → Extracts: rent rolls · escalations · renewal options · guarantees                 ║
║                                                                                      ║
║  Why LLM extraction vs regex?                                                        ║
║  → Adapts to any lease format — no brittle template matching                         ║
║  → Handles nuanced legal language regex cannot parse                                 ║
║                                                                                      ║
║  V1 limitation → V2:                                                                 ║
║  → V1: GPT-4o-mini, single extraction pass                                           ║
║  → V2: Conflict Detector agent cross-references base lease vs amendments             ║
║        catches contradictions in rent, term, renewal options across documents        ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
                                                   │  raw JSON string
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 4 — SCHEMA VALIDATION                                                         │
│                                                                                      │
│  IN:   Raw JSON string from GPT-4o-mini                                              │
│  OUT:  Validated, typed Lease object — or ValidationError                            │
│                                                                                      │
│  Pydantic Models  (src/schemas/lease.py)                                             │
│                                                                                      │
│  class Lease(BaseModel):                                                             │
│    id · document_id · tenant · landlord · property_address · lease_type              │
│    rentable_square_feet (int) · annual_rent (float) · lease_rate_per_sf (float)      │
│    lease_commencement_date · lease_expiration_date · lease_term_months (int)         │
│    parking_spaces (int) · renewal_options · lease_summary · created_at               │
│                                                                                      │
│  How it works:                                                                       │
│  → Pydantic enforces types at runtime: "not a number" → ValidationError              │
│  → Type coercion: converts "123" → 123 automatically where possible                  │
│  → Partial extraction safe — Optional fields don't fail the whole record             │
│  → Clear error messages identify exactly which field failed and why                  │
│                                                                                      │
│  V1 limitation → V2:                                                                 │
│  → V1: basic type validation only                                                    │
│  → V2: add confidence scores per field, range validators                             │
│        (annual_rent > 0, lease_term_months > 0), business rule checks                │
└──────────────────────────────────────────────────┬───────────────────────────────────┘
                                                   │  validated Lease object
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 5 — STORAGE LAYER                                                             │
│                                                                                      │
│  IN:   Validated Lease object                                                        │
│  OUT:  Lease persisted to JSON store + embedded and indexed in FAISS                 │
│                                                                                      │
│  TWO STORES — different purposes, written simultaneously:                            │
│                                                                                      │
│  ┌─────────────────────────────────────┐  ┌──────────────────────────────────────┐   │
│  │  LEASE STORAGE (JSON)               │  │  VECTOR STORE (FAISS)                │   │
│  │  src/storage/lease_storage.py       │  │  src/storage/lease_vector_store.py   │   │
│  │                                     │  │                                      │   │
│  │  lease_store.json                   │  │  In-memory FAISS index               │   │
│  │  { "leases": { "id": {...} } }      │  │  OpenAI text-embedding-ada-002       │   │
│  │                                     │  │  1536-dimensional vectors            │   │
│  │  CRUD: add · get · list             │  │                                      │   │
│  │  Type-safe via Pydantic             │  │  add_lease():                        │   │
│  │  Human-readable · debuggable        │  │  Lease → text repr → embed → FAISS   │   │
│  │                                     │  │                                      │   │
│  │  Production upgrade: PostgreSQL     │  │  Production upgrade: Pinecone        │   │
│  │  with proper indexing               │  │  or Weaviate for persistence         │   │
│  └─────────────────────────────────────┘  └──────────────────────────────────────┘   │
│                                                                                      │
│  Why two stores?                                                                     │
│  → JSON store holds structured business data — all 15+ extracted fields              │
│  → FAISS holds semantic search index — enables natural language queries              │
│  → FAISS retrieves IDs → JSON store retrieves full Lease objects                     │
│                                                                                      │
│  V1 limitation → V2:                                                                 │
│  → V1: JSON file + in-memory FAISS — not persistent across restarts                  │
│  → V2: PostgreSQL + Pinecone/Weaviate with persistent vector storage                 │
└──────────────────────────────────────────────────┬───────────────────────────────────┘
                                                   │  lease stored + indexed
                                                   ▼
╔══════════════════════════════════════════════════════════════════════════════════════╗
║  LAYER 6 — AGENT 3: LEASE LIBRARIAN (RAG)     (src/agents/lease_librarian.py)        ║
║                                                                                      ║
║  IN:   Natural language question + conversation_id                                   ║
║  OUT:  Grounded answer + source lease IDs                                            ║
║                                                                                      ║
║  RAG Pipeline — four steps:                                                          ║
║                                                                                      ║
║  STEP 1 — EMBED QUERY                                                                ║
║  → User question → OpenAI text-embedding-ada-002 → 1536-dim vector                   ║
║                                                                                      ║
║  STEP 2 — RETRIEVE                                                                   ║
║  → FAISS similarity search → top K most semantically similar lease IDs               ║
║  → Cosine similarity: sim = dot(A,B) / (||A|| × ||B||)                               ║
║                                                                                      ║
║  STEP 3 — AUGMENT                                                                    ║
║  → Fetch full Lease objects from LeaseStorage by ID                                  ║
║  → Build context: tenant · expiry · address · rate · terms                           ║
║                                                                                      ║
║  STEP 4 — GENERATE                                                                   ║
║  → Prompt: "Answer ONLY from context. Cite specific lease IDs."                      ║
║  → GPT-4 generates grounded answer with source attribution                           ║
║  → Returns: { response, sources: [lease_ids], conversation_id }                      ║
║                                                                                      ║
║  V1 limitation → V2:                                                                 ║
║  → V1: simple top-K FAISS retrieval                                                  ║
║  → V2: hybrid search (dense + BM25 sparse + RRF fusion) + Cohere reranker            ║
║        conversation memory across sessions, streaming responses (SSE)                ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
                                                   │  answer + source IDs
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 7 — API LAYER                                                                 │
│                                                                                      │
│  IN:   Processed Lease objects, RAG answers, storage results                         │
│  OUT:  JSON HTTP responses to frontend                                               │
│                                                                                      │
│  FastAPI Router  (src/api/main.py)  ·  Uvicorn ASGI  ·  Async endpoints              │
│                                                                                      │
│  POST  /api/v1/leases/batch    →  triggers Layers 1-5 pipeline                       │
│  GET   /api/v1/leases          →  list all leases (library view)                     │
│  GET   /api/v1/leases/{id}     →  get full lease details                             │
│  POST  /api/v1/chat            →  triggers Layer 6 RAG pipeline                      │
│  GET   /api/v1/health          →  health check                                       │
│                                                                                      │
│  On startup: initializes all services — Storage, VectorStore, all three Agents       │
│                                                                                      │
│  V1 limitation → V2:                                                                 │
│  → V1: no authentication, no rate limiting                                           │
│  → V2: JWT tokens + RBAC (AWS Cognito), rate limiting, HTTPS/SSL                     │
│        versioned API, multi-tenant routing per lender organization                   │
└──────────────────────────────────────────────────┬───────────────────────────────────┘
                                                   │  JSON HTTP responses
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 8 — FRONTEND & USER INTERFACE                                                 │
│                                                                                      │
│  IN:   JSON responses from FastAPI                                                   │
│  OUT:  Rendered UI — lease library, extracted data, chat answers with citations      │
│                                                                                      │
│  React Dashboard (lease-digitizer-final.html)  ·  Tailwind CSS  ·  Fetch API         │
│                                                                                      │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────────────┐   │
│  │  LIBRARY PANEL      │  │  CHAT PANEL          │  │  DETAILS PANEL             │   │
│  │                     │  │                      │  │                            │   │
│  │  All uploaded       │  │  Natural language    │  │  Full extracted lease      │   │
│  │  leases listed      │  │  Q&A interface       │  │  data — all 15+ fields     │   │
│  │  with summaries     │  │  with source lease   │  │  with confidence scores    │   │
│  │                     │  │  attribution         │  │                            │   │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────────────┘   │
│                                                                                      │
│  V1 limitation → V2:                                                                 │
│  → V1: single HTML file, in-browser Babel compilation, no auth                       │
│  → V2: proper React build (Vite/Next.js), S3/CloudFront hosting                      │
│        JWT auth, multi-tenant — each lender sees only their leases                   │
└──────────────────────────────────────────────────────────────────────────────────────┘

╔══════════════════════════════════════════════════════════════════════════════════════╗
║  FULL PIPELINE SUMMARY                                                               ║
║                                                                                      ║
║  UPLOAD FLOW:                                                                        ║
║  PDF → Layer 1 (ingest) → Layer 2 (classify) → Layer 3 (extract)                     ║
║      → Layer 4 (validate) → Layer 5 (store + index) → Layer 7 (API) → Layer 8 (UI)   ║
║                                                                                      ║
║  QUERY FLOW:                                                                         ║
║  Question → Layer 8 (UI) → Layer 7 (API) → Layer 6 (RAG)                             ║
║           → Layer 5 (retrieve) → Layer 7 (API) → Layer 8 (UI: answer + citations)    ║
║                                                                                      ║
╠══════════════════════════════════════════════════════════════════════════════════════╣
║  PRODUCTION UPGRADE PATH                                                             ║
║                                                                                      ║
║  V1 (current)          →  V2 (production)                                            ║
║  ─────────────────────────────────────────                                           ║
║  Manual PDF upload     →  S3 event trigger + Airflow DAG                             ║
║  Regex classifier      →  ML document classifier                                     ║
║  GPT-4o-mini           →  Azure OpenAI (regulated environment)                       ║
║  Basic Pydantic        →  Confidence scores per field + business rules               ║
║  JSON file storage     →  PostgreSQL with indexing                                   ║
║  FAISS in-memory       →  Pinecone / Weaviate persistent                             ║
║  Simple FAISS search   →  Hybrid search (dense + BM25 + RRF + Cohere reranker)       ║
║  No auth               →  JWT tokens + RBAC (AWS Cognito)                            ║
║  No monitoring         →  Structured logging + LangSmith + RAGAS evals               ║
║  Single tenant         →  Multi-tenant SaaS per lender organization                  ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

LEGEND
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  ╔══╗  ║    AI processing stage or agent boundary                                    │
│  ┌──┐       Component, service, storage, or UI layer                                 │
│  ──►  │  ▼  Data flow direction                                                      │
│  IN / OUT   What enters and exits each layer                                         │
│  FAISS      In-memory vector similarity search (Facebook AI Similarity Search)       │
│  ada-002    OpenAI text-embedding-ada-002 — 1536-dimensional embeddings              │
│  RAG        Retrieval-Augmented Generation — retrieve → augment → generate           │
│  Pydantic   Python data validation library — enforces types at runtime               │
│  V1 → V2   Current implementation → production upgrade path                          │
└──────────────────────────────────────────────────────────────────────────────────────┘