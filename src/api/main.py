
import logging
import traceback
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agents.lease_extractor import ExtractionResult, LeaseExtractorAgent
from src.rag.chat_agent import LeaseLibrarian
from src.rag.vector_store import LeaseVectorStore
from src.storage.lease_storage import LeaseStorage
from src.schemas.lease import Lease
from src.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api")

# Global instances
services: Dict[str, Any] = {
    "extractor": None,
    "storage": None,
    "vector_store": None,
    "chat_agent": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan manager to handle startup and shutdown events.
    Initializes all agents and services on startup.
    """
    logger.info("Initializing services...")
    try:
        # 1. Initialize Storage
        services["storage"] = LeaseStorage()
        logger.info("LeaseStorage initialized.")

        # 2. Initialize Vector Store
        services["vector_store"] = LeaseVectorStore()
        logger.info("LeaseVectorStore initialized.")

        # 3. Initialize Extractor Agent
        # Use gpt-4o-mini for efficiency as configured in settings/env
        services["extractor"] = LeaseExtractorAgent(verbose=True)
        logger.info("LeaseExtractorAgent initialized.")

        # 4. Initialize Chat Agent (Lease Librarian)
        services["chat_agent"] = LeaseLibrarian(
            vector_store=services["vector_store"],
            lease_storage=services["storage"]
        )
        logger.info("LeaseLibrarian initialized.")

        logger.info("All services started successfully.")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        logger.error(traceback.format_exc())
        raise RuntimeError("Service initialization failed") from e
    
    yield
    
    # Clean up if needed
    logger.info("Shutting down services...")


# Create FastAPI application
app = FastAPI(
    title="Lease Digitizer API",
    description="REST API for the Lease Digitizer Layout Agent System",
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
origins = [
    "http://localhost:3000",  # React dev server
    "http://localhost:8501",  # Streamlit default
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---

class ExtractionRequest(BaseModel):
    """Request model for single lease extraction."""
    document_text: str = Field(..., min_length=1, description="Full text content of the lease document")
    document_id: str = Field(default="unknown", description="Unique identifier for the document")


class BatchExtractionRequest(BaseModel):
    """Request model for batch lease extraction."""
    leases: List[Dict[str, str]] = Field(..., description="List of dicts with 'document_text' and 'filename'")


class BatchExtractionResponse(BaseModel):
    """Response model for batch extraction."""
    processed: int
    failed: int
    lease_ids: List[str]
    errors: List[str]


class ChatRequest(BaseModel):
    """Request model for chat interface."""
    message: str = Field(..., min_length=1, description="User question")
    conversation_id: Optional[str] = Field(default=None, description="Session ID for history")


class ChatResponse(BaseModel):
    """Response model for chat interface."""
    response: str
    sources: List[str]
    conversation_id: str


class PreviewResponse(BaseModel):
    """Response model for lease previews."""
    leases: List[Dict[str, Any]]


class LeaseResponse(BaseModel):
    """Response model for full lease details."""
    lease: Lease


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str


class DeleteResponse(BaseModel):
    """Response model for deletion."""
    deleted: bool


# --- Endpoints ---

@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check API health status."""
    return HealthResponse(status="healthy", version="1.1.0")


@app.post("/api/v1/extract", response_model=ExtractionResult, tags=["Leases"])
async def extract_lease(request: ExtractionRequest):
    """
    Extract structured data from a single lease document.
    """
    if services["extractor"] is None:
        raise HTTPException(503, "Extractor service unavailable")

    try:
        result = services["extractor"].extract_lease(
            document_text=request.document_text,
            document_id=request.document_id
        )
        
        # Determine unique ID for storage
        lease_id = request.document_id
        if lease_id == "unknown":
            lease_id = str(uuid.uuid4())
            if result.lease:
                result.lease.document_id = lease_id

        # Persist if successful
        if result.lease:
            # 1. Save JSON
            services["storage"].add_lease(result.lease, lease_id)
            # 2. Add to Vector Store
            services["vector_store"].add_lease_to_index(result.lease, lease_id)
            
        return result

    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(500, str(e))


@app.post("/api/v1/leases/batch", response_model=BatchExtractionResponse, tags=["Leases"])
async def batch_extract(request: BatchExtractionRequest):
    """
    Process multiple leases in batch. 
    Extracts, stores, and indexes each lease.
    """
    if services["extractor"] is None:
        raise HTTPException(503, "Extractor service unavailable")

    processed = 0
    failed = 0
    lease_ids = []
    errors = []

    for item in request.leases:
        text = item.get("document_text")
        filename = item.get("filename", "unknown")
        
        if not text:
            failed += 1
            errors.append(f"Empty text for {filename}")
            continue
            
        try:
            # Generate ID from filename or uuid
            lease_id = filename if filename != "unknown" else str(uuid.uuid4())
            
            result = services["extractor"].extract_lease(text, lease_id)
            
            if result.lease:
                # Update ID in lease object just in case
                result.lease.document_id = lease_id
                
                # Persist
                services["storage"].add_lease(result.lease, lease_id)
                services["vector_store"].add_lease_to_index(result.lease, lease_id)
                
                processed += 1
                lease_ids.append(lease_id)
            else:
                failed += 1
                errors.append(f"Values extraction failed for {filename}")

        except Exception as e:
            failed += 1
            errors.append(f"Error processing {filename}: {str(e)}")
            logger.error(f"Batch callback error for {filename}: {e}")

    return BatchExtractionResponse(
        processed=processed,
        failed=failed,
        lease_ids=lease_ids,
        errors=errors
    )


@app.get("/api/v1/leases", response_model=PreviewResponse, tags=["Leases"])
async def list_leases():
    """Get list of all stored leases (preview data)."""
    if services["storage"] is None:
        raise HTTPException(503, "Storage service unavailable")
        
    leases = services["storage"].get_all_leases()
    return PreviewResponse(leases=leases)


@app.get("/api/v1/leases/{lease_id}", response_model=LeaseResponse, tags=["Leases"])
async def get_lease(lease_id: str):
    """Get full lease details by ID."""
    if services["storage"] is None:
        raise HTTPException(503, "Storage service unavailable")
        
    lease = services["storage"].get_lease(lease_id)
    if not lease:
        raise HTTPException(404, detail=f"Lease {lease_id} not found")
        
    return LeaseResponse(lease=lease)


@app.delete("/api/v1/leases/{lease_id}", response_model=DeleteResponse, tags=["Leases"])
async def delete_lease(lease_id: str):
    """Delete a lease from storage and vector index."""
    if services["storage"] is None:
        raise HTTPException(503, "Services unavailable")
        
    # Remove from storage
    deleted = services["storage"].delete_lease(lease_id)
    
    # Remove from vector index (best effort)
    if deleted:
        try:
            services["vector_store"].delete_lease_from_index(lease_id)
        except Exception as e:
            logger.warning(f"Failed to remove from vector store: {e}")
            
    return DeleteResponse(deleted=deleted)


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """Chat with the Lease Librarian agent."""
    if services["chat_agent"] is None:
        raise HTTPException(503, "Chat agent unavailable")
        
    try:
        response = services["chat_agent"].chat(
            message=request.message,
            conversation_id=request.conversation_id
        )
        
        return ChatResponse(
            response=response["answer"],
            sources=response["source_documents"],
            conversation_id=response["conversation_id"]
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(500, f"Chat processing failed: {str(e)}")


@app.get("/api/v1/analytics", tags=["Analytics"])
async def get_analytics():
    """Get portfolio-wide analytics."""
    if services["chat_agent"] is None:
         raise HTTPException(503, "Analytics service unavailable")
         
    try:
        # Re-use logic from chat agent or storage
        # Chat agent has a handy helper for this
        return services["chat_agent"].get_portfolio_analytics()
    except Exception as e:
         raise HTTPException(500, str(e))


if __name__ == "__main__":
    import uvicorn
    # Allow running directly for testing
    uvicorn.run(app, host="0.0.0.0", port=8000)
