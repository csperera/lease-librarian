# Lease Digitizer - System Architecture

## Overview

This document describes the high-level architecture of the Lease Digitizer system, a LangChain-powered multi-agent pipeline for processing commercial real estate leases.

---

## System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                     External Systems                             │
├─────────────────────────────────────────────────────────────────┤
│  • PDF Documents (Input)                                         │
│  • OpenAI API (LLM Provider)                                     │
│  • LangSmith (Observability - Optional)                          │
│  • Streamlit (Dashboard Interface)                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Document Ingestion Layer

**Purpose:** Load and preprocess PDF documents for analysis.

**Components:**
- `PDFParserTool` - Extracts text from PDF files
- `DocumentLoader` - Batch loads documents from directories
- `TextProcessor` - Cleans and normalizes extracted text

**Data Flow:**
```
PDF Files → PDFParserTool → TextProcessor → Cleaned Text
```

---

### 2. Agent Layer

**Purpose:** Intelligent document processing using LangChain agents.

| Agent | Pattern | Responsibility |
|-------|---------|----------------|
| Document Classifier | ReAct | Classify documents (base lease vs amendment) |
| Lease Extractor | LLMChain + Pydantic | Extract structured data from leases |
| Conflict Detector | Agent + Memory | Identify contradictions between documents |

**Processing Pipeline:**
```
Document → Classifier → Extractor → Conflict Detector → Results
```

---

### 3. Data Layer

**Purpose:** Structured storage and validation of extracted data.

**Schemas (Pydantic Models):**
- `Lease` - Complete lease data structure (50+ fields)
- `Amendment` - Modification tracking with before/after values
- `Conflict` - Detected contradictions with evidence

**Storage:**
- SQLite for persistent storage (TODO)
- ChromaDB for vector embeddings (TODO)

---

### 4. Presentation Layer

**Purpose:** User interface for document management and visualization.

**Components:**
- Streamlit Dashboard (`src/dashboard/app.py`)
- Document upload and processing UI
- Conflict alerts and resolution workflow
- Analytics and reporting

---

## Data Flow Diagram

```
┌──────────┐     ┌────────────┐     ┌─────────────┐     ┌──────────────┐
│   PDF    │────▶│ PDF Parser │────▶│  Classifier │────▶│   Extractor  │
│  Files   │     │   Tool     │     │    Agent    │     │    Agent     │
└──────────┘     └────────────┘     └─────────────┘     └──────────────┘
                                                                │
                                                                ▼
┌──────────┐     ┌────────────┐     ┌─────────────┐     ┌──────────────┐
│Dashboard │◀────│   Report   │◀────│   Conflict  │◀────│   Schemas    │
│    UI    │     │ Generator  │     │   Detector  │     │  (Pydantic)  │
└──────────┘     └────────────┘     └─────────────┘     └──────────────┘
```

---

## Technology Stack

| Category | Technology | Version |
|----------|------------|---------|
| Framework | LangChain | 0.1+ |
| LLM | OpenAI GPT-4 | Latest |
| Validation | Pydantic | 2.5+ |
| PDF Processing | pypdf, pdfplumber | Latest |
| Dashboard | Streamlit | 1.29+ |
| Database | SQLite | 3.x |
| Vector Store | ChromaDB | 0.4+ |

---

## Security Considerations

- API keys stored in environment variables (never in code)
- `.env` file excluded from version control
- Document data encrypted at rest (TODO)
- Role-based access control for dashboard (TODO)

---

## Scalability Notes

**Current Design:** Single-process, synchronous execution

**Future Enhancements:**
- Async processing with `asyncio`
- Batch processing with worker pools
- Queue-based architecture (Celery/Redis)
- Horizontal scaling via containerization

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| ReAct for Classification | Provides reasoning transparency for document type decisions |
| Pydantic for Schemas | Type safety and automatic validation of extracted data |
| Memory for Conflict Detection | Enables cross-document comparison without reprocessing |
| Streamlit for Dashboard | Rapid prototyping with Python-native UI |

---

## References

- [LangChain Documentation](https://python.langchain.com/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/)
- [Streamlit Documentation](https://docs.streamlit.io/)
