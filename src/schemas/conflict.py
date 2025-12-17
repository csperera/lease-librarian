"""
Lease Digitizer - Conflict Schema Module

This module defines Pydantic models for representing conflicts and
contradictions detected between lease documents. Conflicts can occur
between base leases and amendments, or between multiple amendments.

The Conflict Detector agent uses these schemas to report findings
with detailed evidence and suggested resolutions.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConflictSeverity(str, Enum):
    """Severity levels for detected conflicts."""
    CRITICAL = "critical"      # Fundamental contradiction requiring immediate attention
    HIGH = "high"              # Significant conflict affecting key terms
    MEDIUM = "medium"          # Notable discrepancy requiring review
    LOW = "low"                # Minor inconsistency
    INFO = "info"              # Informational note, not a true conflict


class ConflictCategory(str, Enum):
    """Categories of conflicts between lease documents."""
    TERM_CONFLICT = "term_conflict"                # Conflicting lease term dates
    RENT_CONFLICT = "rent_conflict"                # Conflicting rent amounts
    PARTY_CONFLICT = "party_conflict"              # Conflicting party information
    PROPERTY_CONFLICT = "property_conflict"        # Conflicting property details
    OPTION_CONFLICT = "option_conflict"            # Conflicting options/rights
    CLAUSE_CONFLICT = "clause_conflict"            # Conflicting contractual clauses
    DATE_SEQUENCE = "date_sequence"                # Date ordering issues
    CALCULATION_ERROR = "calculation_error"        # Mathematical inconsistencies
    MISSING_REFERENCE = "missing_reference"        # Amendment references missing doc
    SUPERSEDED_TERMS = "superseded_terms"          # Terms superseded but unclear
    OTHER = "other"


class DocumentReference(BaseModel):
    """
    Reference to a specific location in a document.
    
    Attributes:
        document_id: Document identifier
        document_type: Type of document (lease/amendment)
        document_date: Date of the document
        section: Section or article reference
        page_number: Page number (if known)
        excerpt: Relevant text excerpt
    """
    document_id: str = Field(..., description="Document identifier")
    document_type: str = Field(..., description="Document type (lease/amendment)")
    document_date: Optional[datetime] = Field(default=None, description="Document date")
    section: Optional[str] = Field(default=None, description="Section reference")
    page_number: Optional[int] = Field(default=None, ge=1, description="Page number")
    excerpt: Optional[str] = Field(default=None, description="Relevant text excerpt")


class ConflictEvidence(BaseModel):
    """
    Evidence supporting a detected conflict.
    
    Attributes:
        source_a: First document reference
        source_b: Second document reference (the conflicting source)
        value_a: Value from first document
        value_b: Value from second document
        explanation: Human-readable explanation of the conflict
    """
    source_a: DocumentReference = Field(..., description="First source")
    source_b: DocumentReference = Field(..., description="Second source")
    value_a: Optional[str] = Field(default=None, description="Value from source A")
    value_b: Optional[str] = Field(default=None, description="Value from source B")
    explanation: str = Field(..., description="Explanation of conflict")


class SuggestedResolution(BaseModel):
    """
    Suggested resolution for a conflict.
    
    Attributes:
        resolution_type: Type of resolution (auto/manual/review)
        recommended_value: Recommended value to resolve conflict
        rationale: Why this resolution is recommended
        confidence: Confidence in the suggestion (0-1)
    """
    resolution_type: str = Field(..., description="Resolution type")
    recommended_value: Optional[str] = Field(default=None, description="Recommended value")
    rationale: str = Field(..., description="Resolution rationale")
    confidence: float = Field(default=0.0, ge=0, le=1, description="Resolution confidence")


class Conflict(BaseModel):
    """
    A detected conflict between lease documents.
    
    This is the primary output schema for the Conflict Detector agent.
    Each conflict includes detailed evidence and suggested resolutions.
    
    Attributes:
        conflict_id: Unique conflict identifier
        category: Category of conflict
        severity: Severity level
        
        field_name: Name of the conflicting field
        description: Human-readable description
        
        evidence: Supporting evidence for the conflict
        suggested_resolutions: Possible resolutions
        
        is_resolved: Whether conflict has been resolved
        resolution_notes: Notes about how it was resolved
        
        detected_at: When conflict was detected
        detected_by: Agent/process that detected it
    """
    
    # Identification
    conflict_id: str = Field(..., description="Unique conflict identifier")
    category: ConflictCategory = Field(..., description="Conflict category")
    severity: ConflictSeverity = Field(..., description="Conflict severity")
    
    # Description
    field_name: str = Field(..., description="Field with conflict")
    description: str = Field(..., description="Conflict description")
    
    # Evidence
    evidence: ConflictEvidence = Field(..., description="Conflict evidence")
    suggested_resolutions: list[SuggestedResolution] = Field(
        default_factory=list, description="Suggested resolutions"
    )
    
    # Resolution tracking
    is_resolved: bool = Field(default=False, description="Resolution status")
    resolution_notes: Optional[str] = Field(default=None, description="Resolution notes")
    
    # Metadata
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection time")
    detected_by: str = Field(default="conflict_detector", description="Detecting agent")


class ConflictReport(BaseModel):
    """
    Complete conflict detection report for a set of documents.
    
    Aggregates all conflicts found during analysis of a lease
    and its amendments.
    
    Attributes:
        report_id: Unique report identifier
        generated_at: Report generation timestamp
        
        base_lease_id: Base lease document ID
        amendment_ids: List of amendment document IDs analyzed
        
        conflicts: All detected conflicts
        
        summary_stats: Summary statistics
    """
    
    report_id: str = Field(..., description="Report identifier")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation time")
    
    # Documents analyzed
    base_lease_id: str = Field(..., description="Base lease ID")
    amendment_ids: list[str] = Field(default_factory=list, description="Amendment IDs")
    
    # Conflicts
    conflicts: list[Conflict] = Field(default_factory=list, description="Detected conflicts")
    
    @property
    def total_conflicts(self) -> int:
        """Total number of conflicts detected."""
        return len(self.conflicts)
    
    @property
    def critical_conflicts(self) -> list[Conflict]:
        """Get all critical severity conflicts."""
        return [c for c in self.conflicts if c.severity == ConflictSeverity.CRITICAL]
    
    @property
    def unresolved_conflicts(self) -> list[Conflict]:
        """Get all unresolved conflicts."""
        return [c for c in self.conflicts if not c.is_resolved]
    
    def get_conflicts_by_category(self, category: ConflictCategory) -> list[Conflict]:
        """Get conflicts filtered by category."""
        return [c for c in self.conflicts if c.category == category]
    
    def get_conflicts_by_severity(self, severity: ConflictSeverity) -> list[Conflict]:
        """Get conflicts filtered by severity."""
        return [c for c in self.conflicts if c.severity == severity]


# TODO: Add conflict deduplication logic
# TODO: Add conflict merging for related issues
# TODO: Add export methods for different report formats
# TODO: Add integration with notification systems for critical conflicts
