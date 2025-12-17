
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from src.config import get_settings
from src.schemas.lease import Lease, LeaseType, PropertyUseType

class LeaseVectorStore:
    """
    RAG utility class using FAISS for semantic search over lease data.
    
    Split Strategy:
    Each lease is broken into 3 semantic documents to improve retrieval precision:
    1. Summary Doc: High-level details (parties, address, type)
    2. Financial Doc: Rent, money, escalations, deposits
    3. Dates Doc: Term, commencement, expiration, renewals
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the vector store manager.
        
        Args:
            openai_api_key: Optional API key override. Defaults to settings.
        """
        self.settings = get_settings()
        self.api_key = openai_api_key or self.settings.openai_api_key.get_secret_value()
        
        self.index_path = Path("src/storage/faiss_index")
        self.embeddings = OpenAIEmbeddings(
            model=self.settings.openai_embedding_model,
            api_key=self.api_key
        )
        
        self.vector_store: Optional[FAISS] = None
        self._load_or_create_index()

    def _load_or_create_index(self) -> None:
        """Load existing index from disk or create a new one."""
        if self.index_path.exists() and (self.index_path / "index.faiss").exists():
            try:
                # Allow dangerous deserialization since we trust our own local file
                self.vector_store = FAISS.load_local(
                    folder_path=str(self.index_path),
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Error loading index, creating new one: {e}")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self) -> None:
        """Initialize a fresh FAISS index."""
        # FAISS needs at least one text to initialize if not using from_texts
        # But we can initialize an empty one using the embedding function's dimension if needed
        # Simpler approach: Initialize with a dummy doc if needed, or just allow it to be None
        # until first add. However, LangChain FAISS wrapper usually is created via from_texts.
        # We'll maintain specific state handling for "empty index".
        self.vector_store = None

    def add_lease_to_index(self, lease: Lease, lease_id: str) -> None:
        """
        Generate semantic documents from lease and add to vector store.
        
        Args:
            lease: The Lease object to index.
            lease_id: Unique identifier for the lease.
        """
        # 1. Generate text chunks
        summary_text = self._generate_summary_text(lease)
        financial_text = self._generate_financial_text(lease)
        dates_text = self._generate_dates_text(lease)
        
        # 2. Create Documents with metadata and stable IDs
        docs = [
            Document(
                page_content=summary_text,
                metadata={"lease_id": lease_id, "type": "summary"}
            ),
            Document(
                page_content=financial_text,
                metadata={"lease_id": lease_id, "type": "financial"}
            ),
            Document(
                page_content=dates_text,
                metadata={"lease_id": lease_id, "type": "dates"}
            )
        ]
        
        ids = [f"{lease_id}_summary", f"{lease_id}_financial", f"{lease_id}_dates"]
        
        # 3. Add to index
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(
                documents=docs,
                embedding=self.embeddings,
                ids=ids
            )
        else:
            # Check if IDs exist first to avoid duplicates (FAISS doesn't enforce uniqueness)
            # Simplest is to delete first then add
            try:
                self.delete_lease_from_index(lease_id)
            except:
                pass # Ignore if not found
            
            self.vector_store.add_documents(documents=docs, ids=ids)
            
        self.save_index()

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Semantic search across all leases.
        
        Args:
            query: The search string.
            k: Number of results to return.
            
        Returns:
            List of results with score, lease_id, and matched text snippet.
        """
        if self.vector_store is None:
            return []
            
        # similarity_search_with_score returns L2 distance (lower is better for FAISS default)
        # or cosine distance depending on how it was initialized. 
        # OpenAI embeddings + FAISS usually uses Euclidean distance on normalized vectors (cosine similarity equivalent)
        # Lower score = closer match in default FAISS L2
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "lease_id": doc.metadata.get("lease_id"),
                "doc_type": doc.metadata.get("type"),
                "content": doc.page_content,
                "score": float(score) # FAISS standard: lower is better distance
            })
            
        return formatted_results

    def delete_lease_from_index(self, lease_id: str) -> None:
        """
        Remove a lease's documents from the index.
        
        Args:
            lease_id: ID of the lease to remove.
        """
        if self.vector_store is None:
            return

        ids_to_delete = [
            f"{lease_id}_summary",
            f"{lease_id}_financial",
            f"{lease_id}_dates"
        ]
        
        try:
            # Only delete if they exist; LangChain FAISS delete usage depends on underlying impl
            # Note: delete by ID is supported in newer LangChain FAISS
            self.vector_store.delete(ids_to_delete)
            self.save_index()
        except Exception as e:
            # Valid scenario: IDs might not exist if index was rebuilt or partial
            print(f"Warning during deletion: {e}")

    def save_index(self) -> None:
        """Persist index to disk."""
        if self.vector_store:
            self.index_path.mkdir(parents=True, exist_ok=True)
            self.vector_store.save_local(str(self.index_path))

    def _generate_summary_text(self, lease: Lease) -> str:
        addr = "Unknown Address"
        if lease.property_address:
            addr = f"{lease.property_address.street_address}, {lease.property_address.city}"
            
        tenant = lease.tenant.legal_name if lease.tenant else "Unknown Tenant"
        landlord = lease.landlord.legal_name if lease.landlord else "Unknown Landlord"
        l_type = lease.lease_type.value if lease.lease_type else "commercial"
        
        return (
            f"Lease Summary:\n"
            f"Tenant: {tenant}\n"
            f"Landlord: {landlord}\n"
            f"Property: {addr}\n"
            f"Type: {l_type} lease\n"
        )

    def _generate_financial_text(self, lease: Lease) -> str:
        rent = f"${lease.base_rent_monthly:,.2f}" if lease.base_rent_monthly else "N/A"
        annual = f"${lease.base_rent_annual:,.2f}" if lease.base_rent_annual else "N/A"
        
        escalation_txt = ""
        if lease.rent_escalations:
            esc = lease.rent_escalations[0]
            escalation_txt = f"{esc.escalation_type.value} escalation"
            
        return (
            f"Financial Details:\n"
            f"Monthly Base Rent: {rent}\n"
            f"Annual Rent: {annual}\n"
            f"Rent Structure: {escalation_txt}\n"
        )

    def _generate_dates_text(self, lease: Lease) -> str:
        comm = lease.commencement_date.strftime('%Y-%m-%d') if lease.commencement_date else "N/A"
        exp = lease.expiration_date.strftime('%Y-%m-%d') if lease.expiration_date else "N/A"
        term = f"{lease.term_months} months" if lease.term_months else "N/A"
        
        renewals = "No renewal options"
        if lease.renewal_options:
            renewals = f"{len(lease.renewal_options)} option(s) available"
            
        return (
            f"Term & Dates:\n"
            f"Commencement: {comm}\n"
            f"Expiration: {exp}\n"
            f"Total Term: {term}\n"
            f"Renewals: {renewals}"
        )
