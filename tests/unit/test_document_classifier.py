"""
Lease Digitizer - Unit Tests for Document Classifier

Tests for the DocumentClassifierAgent ReAct agent implementation.
"""

import pytest

from src.agents.document_classifier import (
    ClassificationResult,
    DocumentClassifierAgent,
    DocumentType,
)


class TestDocumentType:
    """Tests for DocumentType enum."""
    
    def test_document_types_exist(self) -> None:
        """Verify all expected document types are defined."""
        assert DocumentType.BASE_LEASE == "base_lease"
        assert DocumentType.AMENDMENT == "amendment"
        assert DocumentType.SUBLEASE == "sublease"
        assert DocumentType.ASSIGNMENT == "assignment"
        assert DocumentType.OTHER == "other"
    
    def test_document_type_is_string_enum(self) -> None:
        """Verify DocumentType is a string enum."""
        assert str(DocumentType.BASE_LEASE) == "DocumentType.BASE_LEASE"
        assert DocumentType.BASE_LEASE.value == "base_lease"


class TestClassificationResult:
    """Tests for ClassificationResult schema."""
    
    def test_classification_result_creation(self) -> None:
        """Test creating a ClassificationResult."""
        result = ClassificationResult(
            document_id="test-123",
            document_type=DocumentType.BASE_LEASE,
            confidence=0.95,
            reasoning="Document contains standard lease provisions.",
            key_indicators=["LEASE AGREEMENT", "LANDLORD AND TENANT"],
        )
        
        assert result.document_id == "test-123"
        assert result.document_type == DocumentType.BASE_LEASE
        assert result.confidence == 0.95
        assert len(result.key_indicators) == 2
    
    def test_classification_result_validation(self) -> None:
        """Test validation of ClassificationResult fields."""
        # Confidence must be between 0 and 1
        with pytest.raises(ValueError):
            ClassificationResult(
                document_id="test",
                document_type=DocumentType.BASE_LEASE,
                confidence=1.5,  # Invalid
                reasoning="Test",
            )


class TestDocumentClassifierAgent:
    """Tests for DocumentClassifierAgent."""
    
    @pytest.fixture
    def classifier(self) -> DocumentClassifierAgent:
        """Create a DocumentClassifierAgent for testing."""
        # Note: This will fail without valid API key
        # Tests should mock the LLM calls
        return DocumentClassifierAgent(verbose=False)
    
    def test_agent_initialization(self, classifier: DocumentClassifierAgent) -> None:
        """Test agent initializes correctly."""
        assert classifier.model_name is not None
        assert classifier.temperature == 0.0
    
    def test_empty_document_raises_error(self, classifier: DocumentClassifierAgent) -> None:
        """Test that empty document text raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            classifier.classify("", "test-id")
    
    def test_whitespace_only_raises_error(self, classifier: DocumentClassifierAgent) -> None:
        """Test that whitespace-only text raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            classifier.classify("   \n\t   ", "test-id")
    
    @pytest.mark.skip(reason="Requires LLM implementation")
    def test_classify_base_lease(self, classifier: DocumentClassifierAgent) -> None:
        """Test classification of a base lease document."""
        # TODO: Implement when LLM mocking is available
        document_text = """
        COMMERCIAL LEASE AGREEMENT
        
        This Lease Agreement is entered into between ABC Properties LLC ("Landlord")
        and XYZ Corporation ("Tenant").
        
        ARTICLE 1. PREMISES
        Landlord leases to Tenant the premises located at 123 Main Street...
        """
        
        result = classifier.classify(document_text, "lease-001")
        
        assert result.document_type == DocumentType.BASE_LEASE
        assert result.confidence > 0.8
    
    @pytest.mark.skip(reason="Requires LLM implementation")
    def test_classify_amendment(self, classifier: DocumentClassifierAgent) -> None:
        """Test classification of an amendment document."""
        # TODO: Implement when LLM mocking is available
        document_text = """
        FIRST AMENDMENT TO LEASE
        
        This Amendment modifies that certain Lease Agreement dated January 1, 2020
        between ABC Properties LLC and XYZ Corporation.
        
        WHEREAS, Landlord and Tenant desire to modify certain terms...
        """
        
        result = classifier.classify(document_text, "amend-001")
        
        assert result.document_type == DocumentType.AMENDMENT
        assert result.confidence > 0.8


# TODO: Add integration tests with mock LLM
# TODO: Add tests for batch classification
# TODO: Add tests for edge cases (corrupted documents, mixed content)
# TODO: Add performance benchmarks
