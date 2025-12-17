"""
Lease Digitizer - Lease Extractor Agent

An LLMChain-based agent that extracts structured data from commercial
real estate leases using Pydantic models for validation. This agent
uses a multi-pass extraction strategy to capture all lease data points.

Key Features:
- Structured output with Pydantic validation
- Multi-pass extraction for complex documents
- Confidence scoring for each extracted field
- Handling of missing or ambiguous data
- Support for various lease formats
"""

import time
from typing import Optional, Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.config import get_settings
from src.schemas.amendment import Amendment
from src.schemas.lease import Lease


class ExtractionMetadata(BaseModel):
    """
    Metadata about the extraction process.
    
    Attributes:
        total_fields: Total number of fields attempted
        extracted_fields: Number of fields successfully extracted
        missing_fields: Fields that could not be extracted
        low_confidence_fields: Fields with confidence below threshold
        processing_time_seconds: Time taken for extraction
    """
    total_fields: int = Field(default=0, description="Total fields")
    extracted_fields: int = Field(default=0, description="Extracted fields")
    missing_fields: list[str] = Field(default_factory=list, description="Missing fields")
    low_confidence_fields: list[str] = Field(default_factory=list, description="Low confidence") 
    processing_time_seconds: float = Field(default=0.0, description="Processing time")


class ExtractionResult(BaseModel):
    """
    Complete extraction result with data and metadata.
    
    Attributes:
        lease: Extracted lease data (if base lease)
        amendment: Extracted amendment data (if amendment)
        metadata: Extraction process metadata
        raw_response: Raw LLM response for debugging
    """
    lease: Optional[Lease] = Field(default=None, description="Extracted lease")
    amendment: Optional[Amendment] = Field(default=None, description="Extracted amendment")
    metadata: ExtractionMetadata = Field(
        default_factory=ExtractionMetadata, description="Extraction metadata"
    )
    raw_response: Optional[str] = Field(default=None, description="Raw LLM response")


# Primary extraction prompt for base leases
LEASE_EXTRACTION_PROMPT = PromptTemplate.from_template("""
You are an expert commercial real estate analyst specializing in lease abstraction.
Extract all available information from the following lease document.

IMPORTANT GUIDELINES:
1. Extract data exactly as it appears in the document
2. For fields that are not present OR incomplete, use null (do not create partial objects)
3. Never use the string "null" - either provide a real value or omit the field

IMPORTANT RULES FOR NESTED OBJECTS:
- If you don't have complete information for a nested object (like address), omit the entire object
- NEVER create partial nested objects with null values
- Example: If landlord address is unknown, use "address": null (not a partial address object)
- Example: If you only know the property address city but not street, omit the entire property_address
4. Include confidence notes for ambiguous extractions
5. Normalize dates to YYYY-MM-DD format
6. Normalize currency to numeric values without symbols
7. Extract party names exactly as written (including legal entity types)
- For lease_type: if unknown, use "net" as default
- For property_use_type: if unknown, use "office" as default

{format_instructions}

LEASE DOCUMENT:
---
{document_text}
---

Extract all lease information following the schema above.
""")


# Secondary extraction prompt for amendments
AMENDMENT_EXTRACTION_PROMPT = PromptTemplate.from_template("""
You are an expert commercial real estate analyst specializing in lease amendments.
Extract all available information from the following amendment document.

IMPORTANT GUIDELINES:
1. Identify all modified provisions explicitly
2. Track both original and amended values when provided
3. Note the effective date for each modification
4. Reference the base lease being amended
5. Use null for fields that are not present

{format_instructions}

AMENDMENT DOCUMENT:
---
{document_text}
---

Extract all amendment information following the schema above.
""")


class LeaseExtractorAgent:
    """
    LCEL-based agent for extracting structured lease data.
    
    Uses Pydantic output parsing to ensure extracted data conforms
    to the defined schemas with validation.
    
    Example:
        >>> extractor = LeaseExtractorAgent()
        >>> result = extractor.extract_lease(document_text, "doc-123")
        >>> print(f"Tenant: {result.lease.tenant.legal_name}")
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        verbose: bool = False,
    ) -> None:
        """
        Initialize the Lease Extractor agent.
        
        Args:
            model_name: OpenAI model to use (defaults to settings)
            temperature: LLM temperature (0 = deterministic)
            verbose: Enable verbose chain output
        """
        self.settings = get_settings()
        self.model_name = model_name or self.settings.openai_model
        self.temperature = temperature
        self.verbose = verbose
        
        self._llm: Optional[ChatOpenAI] = None
        self._lease_chain: Optional[RunnableSequence] = None
        self._amendment_chain: Optional[RunnableSequence] = None
        
        # Output parsers
        self._lease_parser = PydanticOutputParser(pydantic_object=Lease)
        self._amendment_parser = PydanticOutputParser(pydantic_object=Amendment)
    
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
    
    def _build_lease_chain(self) -> RunnableSequence:
        """
        Build the LCEL chain for lease extraction.
        
        Returns:
            Configured runnable chain for base lease extraction
        """
        prompt = LEASE_EXTRACTION_PROMPT.partial(
            format_instructions=self._lease_parser.get_format_instructions()
        )
        
        # LCEL: prompt | llm | parser
        return prompt | self.llm | self._lease_parser
    
    def _build_amendment_chain(self) -> RunnableSequence:
        """
        Build the LCEL chain for amendment extraction.
        
        Returns:
            Configured runnable chain for amendment extraction
        """
        prompt = AMENDMENT_EXTRACTION_PROMPT.partial(
            format_instructions=self._amendment_parser.get_format_instructions()
        )
        
        # LCEL: prompt | llm | parser
        return prompt | self.llm | self._amendment_parser
    
    @property
    def lease_chain(self) -> RunnableSequence:
        """Get or create the lease extraction chain."""
        if self._lease_chain is None:
            self._lease_chain = self._build_lease_chain()
        return self._lease_chain
    
    @property
    def amendment_chain(self) -> RunnableSequence:
        """Get or create the amendment extraction chain."""
        if self._amendment_chain is None:
            self._amendment_chain = self._build_amendment_chain()
        return self._amendment_chain
    
    def _preprocess_document(self, document_text: str) -> str:
        """
        Preprocess document text for extraction.
        
        Args:
            document_text: Raw document text
            
        Returns:
            Cleaned and normalized document text
        """
        # Remove excessive whitespace
        text = " ".join(document_text.split())
        
        # Truncate if too long (GPT-4 context limit)
        MAX_CHARS = 100000  # ~25k tokens
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS]
        
        return text.strip()
    
    def _calculate_extraction_confidence(self, lease: Lease) -> float:
        """
        Calculate overall extraction confidence based on extracted fields.
        
        Args:
            lease: Extracted lease data
            
        Returns:
            Confidence score between 0 and 1
        """
        # Critical fields (must have for valid lease)
        critical_fields = [
            'tenant', 'landlord', 'property_address',
            'commencement_date', 'expiration_date',
            'base_rent_monthly', 'rentable_square_feet'
        ]
        
        # Count how many critical fields are populated
        populated_critical = sum(
            1 for field in critical_fields 
            if getattr(lease, field, None) is not None
        )
        
        # Base confidence from critical fields
        confidence = populated_critical / len(critical_fields)
        
        # Boost if optional fields also populated
        optional_fields = ['security_deposit', 'operating_expenses', 'renewal_options']
        populated_optional = sum(
            1 for field in optional_fields 
            if getattr(lease, field, None) is not None
        )
        
        # Add bonus up to 0.2 for optional fields
        bonus = min(0.2, populated_optional * 0.05)
        
        return min(1.0, confidence + bonus)
    
    def extract_lease(
        self,
        document_text: str,
        document_id: str,
    ) -> ExtractionResult:
        """
        Extract structured data from a base lease document.
        
        Args:
            document_text: Full text content of the lease
            document_id: Unique identifier for the document
            
        Returns:
            ExtractionResult with lease data and metadata
            
        Raises:
            ValueError: If document_text is empty
        """
        # Start timing
        start_time = time.time()
        
        # STEP 1: Validate input
        if not document_text or not document_text.strip():
            raise ValueError("Document text cannot be empty")
        
        if not document_id:
            raise ValueError("Document ID is required")
        
        # STEP 2: Preprocess
        cleaned_text = self._preprocess_document(document_text)
        
        # STEP 3: Run extraction chain
        try:
            # Invoke the chain
            response = self.lease_chain.invoke({
                "document_text": cleaned_text
            })
            
            # Extract the parsed lease from response
            # LangChain with output_parser might return the parsed object in different keys
            if isinstance(response, Lease):
                lease = response
                raw_response_text = str(response)
            elif isinstance(response, dict) and "text" in response:
                lease = response["text"]
                raw_response_text = str(response.get("text", ""))
            elif isinstance(response, dict) and "output" in response:
                lease = response["output"]
                raw_response_text = str(response.get("output", ""))
            else:
                # Fallback: try to get the parsed result directly
                lease = response
                raw_response_text = str(response)
            
            # Ensure we got a Lease object
            if not isinstance(lease, Lease):
                raise ValueError(f"Expected Lease object, got {type(lease)}")
            
        except Exception as e:
            # If extraction fails, return empty result with error
            return ExtractionResult(
                lease=None,
                metadata=ExtractionMetadata(
                    total_fields=0,
                    extracted_fields=0,
                    missing_fields=["extraction_failed"],
                    processing_time_seconds=time.time() - start_time
                ),
                raw_response=f"Error: {str(e)}"
            )
        
        # STEP 4: Post-process lease object
        lease.document_id = document_id
        
        # STEP 5: Calculate confidence
        confidence = self._calculate_extraction_confidence(lease)
        lease.confidence_score = confidence
        
        # STEP 6: Build metadata
        total_fields = len(Lease.model_fields)
        
        extracted_fields = sum(
            1 for field in Lease.model_fields.keys()
            if getattr(lease, field, None) is not None
        )
        
        critical_fields = [
            'tenant', 'landlord', 'property_address',
            'commencement_date', 'expiration_date', 'base_rent_monthly'
        ]
        missing_fields = [
            field for field in critical_fields
            if getattr(lease, field, None) is None
        ]
        
        low_confidence: list[str] = []
        if confidence < 0.7:
            low_confidence = missing_fields
        
        metadata = ExtractionMetadata(
            total_fields=total_fields,
            extracted_fields=extracted_fields,
            missing_fields=missing_fields,
            low_confidence_fields=low_confidence,
            processing_time_seconds=time.time() - start_time
        )
        
        # STEP 7: Return result
        return ExtractionResult(
            lease=lease,
            amendment=None,
            metadata=metadata,
            raw_response=raw_response_text
        )
    
    def extract_amendment(
        self,
        document_text: str,
        document_id: str,
        base_lease_id: Optional[str] = None,
    ) -> ExtractionResult:
        """
        Extract structured data from an amendment document.
        
        Args:
            document_text: Full text content of the amendment
            document_id: Unique identifier for the document
            base_lease_id: Optional ID of the base lease being amended
            
        Returns:
            ExtractionResult with amendment data and metadata
        """
        if not document_text or not document_text.strip():
            raise ValueError("Document text cannot be empty")
        
        # TODO: Implement amendment extraction logic
        raise NotImplementedError("Amendment extraction not yet implemented")
    
    async def extract_lease_async(
        self,
        document_text: str,
        document_id: str,
    ) -> ExtractionResult:
        """
        Async version of extract_lease.
        
        Args:
            document_text: Full text content of the lease
            document_id: Unique identifier for the document
            
        Returns:
            ExtractionResult with lease data and metadata
        """
        # TODO: Implement async extraction
        raise NotImplementedError("Async extraction not yet implemented")
    
    def extract_with_multipass(
        self,
        document_text: str,
        document_id: str,
        passes: int = 3,
    ) -> ExtractionResult:
        """
        Extract data using multiple passes for improved accuracy.
        
        Each pass focuses on different aspects of the document,
        with later passes filling in gaps from earlier passes.
        
        Args:
            document_text: Full text content of the document
            document_id: Unique identifier for the document
            passes: Number of extraction passes
            
        Returns:
            ExtractionResult with merged data from all passes
        """
        # TODO: Implement multi-pass extraction
        # Pass 1: Core terms (parties, property, dates)
        # Pass 2: Financial terms (rent, escalations, deposits)
        # Pass 3: Options and clauses
        raise NotImplementedError("Multi-pass extraction not yet implemented")


# TODO: Add support for custom extraction prompts per client
# TODO: Add extraction templates for common lease formats
# TODO: Add field-level confidence scoring
# TODO: Add extraction validation against industry standards
# TODO: Add support for extracting exhibits and schedules
