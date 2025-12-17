"""
Lease Digitizer - Unit Tests for Conflict Detector

Tests for the ConflictDetectorAgent with memory implementation.
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from src.agents.conflict_detector import (
    ConflictDetectorAgent,
    DocumentMemory,
)
from src.schemas.amendment import Amendment, AmendmentType, ModifiedProvision
from src.schemas.conflict import (
    Conflict,
    ConflictCategory,
    ConflictEvidence,
    ConflictReport,
    ConflictSeverity,
    DocumentReference,
)
from src.schemas.lease import Lease, Party


class TestDocumentMemory:
    """Tests for DocumentMemory storage."""
    
    @pytest.fixture
    def memory(self) -> DocumentMemory:
        """Create a fresh DocumentMemory."""
        return DocumentMemory()
    
    def test_add_lease(self, memory: DocumentMemory) -> None:
        """Test adding a lease to memory."""
        lease = Lease(
            document_id="lease-001",
            tenant=Party(legal_name="Test Tenant"),
        )
        
        memory.add_lease(lease)
        
        assert "lease-001" in memory.leases
        assert memory.leases["lease-001"].tenant.legal_name == "Test Tenant"
    
    def test_add_amendment(self, memory: DocumentMemory) -> None:
        """Test adding an amendment linked to a lease."""
        lease = Lease(document_id="lease-001")
        memory.add_lease(lease)
        
        amendment = Amendment(
            document_id="amend-001",
            amendment_number=1,
        )
        memory.add_amendment(amendment, "lease-001")
        
        assert "amend-001" in memory.amendments
        assert "amend-001" in memory.relationships["lease-001"]
    
    def test_get_lease_with_amendments(self, memory: DocumentMemory) -> None:
        """Test retrieving a lease with all amendments."""
        lease = Lease(document_id="lease-001")
        memory.add_lease(lease)
        
        for i in range(3):
            amendment = Amendment(document_id=f"amend-{i+1}")
            memory.add_amendment(amendment, "lease-001")
        
        retrieved_lease, amendments = memory.get_lease_with_amendments("lease-001")
        
        assert retrieved_lease is not None
        assert len(amendments) == 3
    
    def test_clear_memory(self, memory: DocumentMemory) -> None:
        """Test clearing all memory."""
        lease = Lease(document_id="lease-001")
        memory.add_lease(lease)
        
        memory.clear()
        
        assert len(memory.leases) == 0
        assert len(memory.amendments) == 0
        assert len(memory.relationships) == 0


class TestConflictSchemas:
    """Tests for conflict-related schemas."""
    
    def test_conflict_creation(self) -> None:
        """Test creating a Conflict object."""
        evidence = ConflictEvidence(
            source_a=DocumentReference(
                document_id="lease-001",
                document_type="lease",
                excerpt="Base Rent: $10,000/month",
            ),
            source_b=DocumentReference(
                document_id="amend-001",
                document_type="amendment",
                excerpt="Original Rent: $10,500/month",
            ),
            value_a="$10,000",
            value_b="$10,500",
            explanation="Amendment references incorrect original rent amount.",
        )
        
        conflict = Conflict(
            conflict_id="conflict-001",
            category=ConflictCategory.RENT_CONFLICT,
            severity=ConflictSeverity.HIGH,
            field_name="base_rent_monthly",
            description="Rent amount mismatch between base lease and amendment.",
            evidence=evidence,
        )
        
        assert conflict.severity == ConflictSeverity.HIGH
        assert conflict.category == ConflictCategory.RENT_CONFLICT
        assert conflict.is_resolved is False
    
    def test_conflict_report(self) -> None:
        """Test ConflictReport aggregation."""
        report = ConflictReport(
            report_id="report-001",
            base_lease_id="lease-001",
            amendment_ids=["amend-001", "amend-002"],
            conflicts=[
                Conflict(
                    conflict_id="c1",
                    category=ConflictCategory.RENT_CONFLICT,
                    severity=ConflictSeverity.CRITICAL,
                    field_name="rent",
                    description="Test",
                    evidence=ConflictEvidence(
                        source_a=DocumentReference(document_id="a", document_type="lease"),
                        source_b=DocumentReference(document_id="b", document_type="amendment"),
                        explanation="Test",
                    ),
                ),
                Conflict(
                    conflict_id="c2",
                    category=ConflictCategory.TERM_CONFLICT,
                    severity=ConflictSeverity.MEDIUM,
                    field_name="term",
                    description="Test",
                    evidence=ConflictEvidence(
                        source_a=DocumentReference(document_id="a", document_type="lease"),
                        source_b=DocumentReference(document_id="b", document_type="amendment"),
                        explanation="Test",
                    ),
                ),
            ],
        )
        
        assert report.total_conflicts == 2
        assert len(report.critical_conflicts) == 1
        assert len(report.get_conflicts_by_category(ConflictCategory.RENT_CONFLICT)) == 1


class TestConflictDetectorAgent:
    """Tests for ConflictDetectorAgent."""
    
    @pytest.fixture
    def detector(self) -> ConflictDetectorAgent:
        """Create a ConflictDetectorAgent for testing."""
        return ConflictDetectorAgent(verbose=False)
    
    def test_agent_initialization(self, detector: ConflictDetectorAgent) -> None:
        """Test agent initializes correctly."""
        assert detector.model_name is not None
        assert detector.document_memory is not None
    
    def test_add_and_retrieve_documents(self, detector: ConflictDetectorAgent) -> None:
        """Test adding documents via agent."""
        lease = Lease(document_id="lease-001")
        detector.add_lease(lease)
        
        amendment = Amendment(document_id="amend-001")
        detector.add_amendment(amendment, "lease-001")
        
        retrieved_lease, amendments = detector.document_memory.get_lease_with_amendments("lease-001")
        
        assert retrieved_lease is not None
        assert len(amendments) == 1
    
    def test_missing_lease_raises_error(self, detector: ConflictDetectorAgent) -> None:
        """Test that detecting conflicts on missing lease raises error."""
        with pytest.raises(ValueError, match="not found in memory"):
            detector.detect_conflicts("nonexistent-lease")
    
    def test_get_conflict_summary(self, detector: ConflictDetectorAgent) -> None:
        """Test conflict summary generation."""
        report = ConflictReport(
            report_id="test",
            base_lease_id="lease-001",
            conflicts=[
                Conflict(
                    conflict_id="c1",
                    category=ConflictCategory.RENT_CONFLICT,
                    severity=ConflictSeverity.CRITICAL,
                    field_name="rent",
                    description="Test",
                    evidence=ConflictEvidence(
                        source_a=DocumentReference(document_id="a", document_type="lease"),
                        source_b=DocumentReference(document_id="b", document_type="amendment"),
                        explanation="Test",
                    ),
                ),
            ],
        )
        
        summary = detector.get_conflict_summary(report)
        
        assert summary["total"] == 1
        assert "critical" in summary["by_severity"]
        assert summary["by_severity"]["critical"] == 1
    
    def test_clear_memory(self, detector: ConflictDetectorAgent) -> None:
        """Test clearing agent memory."""
        lease = Lease(document_id="lease-001")
        detector.add_lease(lease)
        
        detector.clear_memory()
        
        assert len(detector.document_memory.leases) == 0


# TODO: Add integration tests with mock LLM for conflict detection
# TODO: Add tests for specific conflict types
# TODO: Add tests for conflict resolution workflow
# TODO: Add performance tests for large document sets
