"""
Lease Digitizer - Document Classifier Agent

A ReAct (Reasoning + Acting) agent that classifies commercial real estate
documents into categories: base leases, amendments, or other document types.

This agent uses chain-of-thought reasoning to analyze document content
and make classification decisions with high confidence. It employs
multiple analysis strategies and can request additional context when
uncertain.

Key Features:
- ReAct pattern for transparent reasoning
- Multi-step analysis with tool use
- Confidence scoring for classifications
- Support for ambiguous document handling
"""

from enum import Enum
from typing import Optional, Any

from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.config import get_settings


class DocumentType(str, Enum):
    """Supported document types for classification."""
    BASE_LEASE = "base_lease"
    AMENDMENT = "amendment"
    SUBLEASE = "sublease"
    ASSIGNMENT = "assignment"
    ESTOPPEL = "estoppel"
    SNDA = "snda"  # Subordination, Non-Disturbance, Attornment
    COMMENCEMENT_LETTER = "commencement_letter"
    OTHER = "other"
    UNKNOWN = "unknown"


class ClassificationResult(BaseModel):
    """
    Result of document classification.
    
    Attributes:
        document_id: Unique document identifier
        document_type: Classified document type
        confidence: Classification confidence (0-1)
        reasoning: Explanation of classification decision
        key_indicators: Phrases/patterns that led to classification
        related_documents: IDs of related documents (e.g., base lease for amendment)
        needs_review: Flag if human review is recommended
    """
    document_id: str = Field(..., description="Document identifier")
    document_type: DocumentType = Field(..., description="Classified type")
    confidence: float = Field(..., ge=0, le=1, description="Classification confidence")
    reasoning: str = Field(..., description="Classification reasoning")
    key_indicators: list[str] = Field(default_factory=list, description="Key indicators")
    related_documents: list[str] = Field(default_factory=list, description="Related doc IDs")
    needs_review: bool = Field(default=False, description="Needs human review")


# ReAct prompt template for document classification
CLASSIFIER_PROMPT = PromptTemplate.from_template("""
You are an expert commercial real estate document analyst. Your task is to 
classify lease documents accurately using careful reasoning.

You have access to the following tools:
{tools}

Use the following format:

Question: the document classification task
Thought: reason about what you need to analyze
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now have enough information to classify this document
Final Answer: the classification with confidence and reasoning

Document Types:
- base_lease: Original lease agreement between landlord and tenant
- amendment: Modification to an existing lease
- sublease: Agreement allowing tenant to sublet to third party
- assignment: Transfer of lease from one party to another
- estoppel: Certificate confirming lease terms
- snda: Subordination, Non-Disturbance, Attornment agreement
- commencement_letter: Confirms lease commencement date
- other: Other document type

Question: {input}

{agent_scratchpad}
""")


class DocumentClassifierAgent:
    """
    ReAct agent for classifying commercial real estate documents.
    
    This agent analyzes document content using a reasoning + acting
    pattern to classify documents with high accuracy.
    
    Example:
        >>> classifier = DocumentClassifierAgent()
        >>> result = classifier.classify(document_text, document_id)
        >>> print(f"Type: {result.document_type}, Confidence: {result.confidence}")
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        verbose: bool = False,
    ) -> None:
        """
        Initialize the Document Classifier agent.
        
        Args:
            model_name: OpenAI model to use (defaults to settings)
            temperature: LLM temperature (0 = deterministic)
            verbose: Enable verbose agent output
        """
        self.settings = get_settings()
        self.model_name = model_name or self.settings.openai_model
        self.temperature = temperature
        self.verbose = verbose
        
        self._llm: Optional[ChatOpenAI] = None
        self._agent: Optional[Any] = None  # LangGraph compiled agent
    
    @property
    def llm(self) -> ChatOpenAI:
        """Get or create the LLM instance."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=self.settings.openai_api_key.get_secret_value(),
            )
        return self._llm
    
    def _create_tools(self) -> list[Tool]:
        """
        Create tools available to the ReAct agent.
        
        Returns:
            List of LangChain tools for document analysis
        """
        # TODO: Implement actual tool functions
        
        tools = [
            Tool(
                name="analyze_header",
                description="Analyze the document header/title to identify document type indicators",
                func=self._analyze_header,
            ),
            Tool(
                name="find_parties",
                description="Find and extract party names (landlord, tenant) from the document",
                func=self._find_parties,
            ),
            Tool(
                name="check_amendment_references",
                description="Check if document references a prior lease or amendment",
                func=self._check_amendment_references,
            ),
            Tool(
                name="analyze_recitals",
                description="Analyze the recitals/whereas clauses for context",
                func=self._analyze_recitals,
            ),
            Tool(
                name="check_signature_block",
                description="Analyze signature block structure and parties",
                func=self._check_signature_block,
            ),
        ]
        
        return tools
    
    def _analyze_header(self, document_text: str) -> str:
        """Analyze document header for classification indicators."""
        # TODO: Implement header analysis
        # Look for keywords like "LEASE AGREEMENT", "AMENDMENT", "SUBLEASE", etc.
        raise NotImplementedError("Header analysis not yet implemented")
    
    def _find_parties(self, document_text: str) -> str:
        """Extract party information from document."""
        # TODO: Implement party extraction
        # Look for LANDLORD:, TENANT:, SUBLANDLORD:, SUBTENANT:, etc.
        raise NotImplementedError("Party extraction not yet implemented")
    
    def _check_amendment_references(self, document_text: str) -> str:
        """Check for references to prior leases or amendments."""
        # TODO: Implement reference checking
        # Look for "that certain lease dated", "as amended by", etc.
        raise NotImplementedError("Amendment reference check not yet implemented")
    
    def _analyze_recitals(self, document_text: str) -> str:
        """Analyze recitals/whereas clauses."""
        # TODO: Implement recitals analysis
        # Look for WHEREAS clauses that provide context
        raise NotImplementedError("Recitals analysis not yet implemented")
    
    def _check_signature_block(self, document_text: str) -> str:
        """Analyze signature block structure."""
        # TODO: Implement signature block analysis
        # Identify parties and their roles from signatures
        raise NotImplementedError("Signature block analysis not yet implemented")
    
    def _build_agent(self) -> Any:
        """
        Build the ReAct agent using LangGraph.
        
        Returns:
            Compiled LangGraph agent for document classification
        """
        tools = self._create_tools()
        
        # LangGraph's create_react_agent returns a compiled runnable
        return create_react_agent(
            model=self.llm,
            tools=tools,
        )
    
    @property
    def agent(self) -> Any:
        """Get or create the agent."""
        if self._agent is None:
            self._agent = self._build_agent()
        return self._agent
    
    def classify(
        self,
        document_text: str,
        document_id: str,
        filename: Optional[str] = None,
    ) -> ClassificationResult:
        """
        Classify a document using the ReAct agent.
        
        Args:
            document_text: Full text content of the document
            document_id: Unique identifier for the document
            filename: Optional filename for additional context
            
        Returns:
            ClassificationResult with type, confidence, and reasoning
            
        Raises:
            ValueError: If document_text is empty
        """
        if not document_text or not document_text.strip():
            raise ValueError("Document text cannot be empty")
        
        # TODO: Implement full classification logic
        # 1. Run agent with document text
        # 2. Parse agent output into ClassificationResult
        # 3. Apply confidence thresholds
        # 4. Flag for review if confidence is low
        
        raise NotImplementedError("Document classification not yet implemented")
    
    async def classify_async(
        self,
        document_text: str,
        document_id: str,
        filename: Optional[str] = None,
    ) -> ClassificationResult:
        """
        Async version of classify.
        
        Args:
            document_text: Full text content of the document
            document_id: Unique identifier for the document
            filename: Optional filename for additional context
            
        Returns:
            ClassificationResult with type, confidence, and reasoning
        """
        # TODO: Implement async classification
        raise NotImplementedError("Async classification not yet implemented")
    
    def classify_batch(
        self,
        documents: list[tuple[str, str]],
    ) -> list[ClassificationResult]:
        """
        Classify multiple documents.
        
        Args:
            documents: List of (document_text, document_id) tuples
            
        Returns:
            List of ClassificationResult for each document
        """
        # TODO: Implement batch classification with parallel processing
        return [
            self.classify(text, doc_id)
            for text, doc_id in documents
        ]


# TODO: Add support for document pre-processing (OCR, cleaning)
# TODO: Add caching for frequently seen document patterns
# TODO: Add feedback loop for improving classification accuracy
# TODO: Add metrics collection for monitoring classification performance
