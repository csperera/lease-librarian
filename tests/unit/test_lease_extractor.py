"""
Lease Digitizer - Unit Tests for Lease Extractor

Tests for the LeaseExtractorAgent LLMChain implementation.
"""

import pytest
from datetime import date
from decimal import Decimal

from src.agents.lease_extractor import (
    ExtractionMetadata,
    ExtractionResult,
    LeaseExtractorAgent,
)
from src.schemas.lease import (
    Address,
    Lease,
    LeaseType,
    Party,
    PropertyUseType,
)


class TestExtractionResult:
    """Tests for ExtractionResult schema."""
    
    def test_extraction_result_with_lease(self) -> None:
        """Test ExtractionResult containing a lease."""
        lease = Lease(
            document_id="lease-001",
            lease_type=LeaseType.TRIPLE_NET,
            tenant=Party(legal_name="Test Tenant LLC"),
            landlord=Party(legal_name="Test Landlord Inc"),
        )
        
        result = ExtractionResult(
            lease=lease,
            metadata=ExtractionMetadata(
                total_fields=50,
                extracted_fields=25,
            ),
        )
        
        assert result.lease is not None
        assert result.lease.document_id == "lease-001"
        assert result.amendment is None
    
    def test_extraction_metadata(self) -> None:
        """Test ExtractionMetadata tracks field statistics."""
        metadata = ExtractionMetadata(
            total_fields=50,
            extracted_fields=40,
            missing_fields=["guarantors", "renewal_options"],
            low_confidence_fields=["base_rent_monthly"],
            processing_time_seconds=2.5,
        )
        
        assert metadata.total_fields == 50
        assert metadata.extracted_fields == 40
        assert len(metadata.missing_fields) == 2
        assert metadata.processing_time_seconds == 2.5


class TestLeaseSchema:
    """Tests for Lease Pydantic schema."""
    
    def test_minimal_lease_creation(self) -> None:
        """Test creating a lease with minimal fields."""
        lease = Lease(document_id="test-001")
        
        assert lease.document_id == "test-001"
        assert lease.tenant is None
        assert lease.guarantors == []
    
    def test_full_lease_creation(self) -> None:
        """Test creating a lease with all fields."""
        lease = Lease(
            document_id="lease-full",
            lease_type=LeaseType.TRIPLE_NET,
            execution_date=date(2024, 1, 15),
            landlord=Party(
                legal_name="Big Landlord Corporation",
                entity_type="Corporation",
            ),
            tenant=Party(
                legal_name="Retail Tenant LLC",
                entity_type="LLC",
            ),
            property_address=Address(
                street_address="123 Main Street, Suite 100",
                city="New York",
                state="NY",
                zip_code="10001",
            ),
            rentable_square_feet=Decimal("5000"),
            property_use_type=PropertyUseType.RETAIL,
            commencement_date=date(2024, 2, 1),
            expiration_date=date(2029, 1, 31),
            term_months=60,
            base_rent_monthly=Decimal("10000"),
            security_deposit=Decimal("30000"),
            confidence_score=0.92,
        )
        
        assert lease.lease_type == LeaseType.TRIPLE_NET
        assert lease.landlord.legal_name == "Big Landlord Corporation"
        assert lease.property_address.city == "New York"
        assert lease.term_months == 60
    
    def test_address_state_normalization(self) -> None:
        """Test that state is normalized to uppercase."""
        address = Address(
            street_address="123 Main St",
            city="Boston",
            state="ma",
            zip_code="02101",
        )
        
        assert address.state == "MA"


class TestLeaseExtractorAgent:
    """Tests for LeaseExtractorAgent."""
    
    @pytest.fixture
    def extractor(self) -> LeaseExtractorAgent:
        """Create a LeaseExtractorAgent for testing."""
        return LeaseExtractorAgent(verbose=False)
    
    def test_agent_initialization(self, extractor: LeaseExtractorAgent) -> None:
        """Test agent initializes correctly."""
        assert extractor.model_name is not None
        assert extractor.temperature == 0.0
    
    def test_empty_document_raises_error(self, extractor: LeaseExtractorAgent) -> None:
        """Test that empty document text raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            extractor.extract_lease("", "test-id")
    
    @pytest.mark.skip(reason="Requires LLM implementation")
    def test_extract_basic_lease_data(self, extractor: LeaseExtractorAgent) -> None:
        """Test extraction of basic lease data."""
        # TODO: Implement when LLM mocking is available
        document_text = """
        LEASE AGREEMENT
        
        Landlord: ABC Properties LLC
        Tenant: XYZ Corporation
        
        Premises: 123 Main Street, New York, NY 10001
        Square Footage: 5,000 RSF
        
        Term: 5 years commencing January 1, 2024
        Base Rent: $50,000 per year ($10,000 per month)
        """
        
        result = extractor.extract_lease(document_text, "test-001")
        
        assert result.lease is not None
        assert result.lease.tenant.legal_name == "XYZ Corporation"


# TODO: Add tests for amendment extraction
# TODO: Add tests for multi-pass extraction
# TODO: Add tests for handling malformed data
# TODO: Add tests for confidence scoring
