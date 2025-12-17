"""
Lease Digitizer - Schema Module

Pydantic models for structured data validation and serialization.
"""

from src.schemas.amendment import Amendment, AmendmentType, ModifiedProvision
from src.schemas.conflict import (
    Conflict,
    ConflictCategory,
    ConflictEvidence,
    ConflictReport,
    ConflictSeverity,
    DocumentReference,
    SuggestedResolution,
)
from src.schemas.lease import (
    Address,
    EscalationType,
    Lease,
    LeaseType,
    OperatingExpenses,
    Party,
    PropertyUseType,
    RenewalOption,
    RentEscalation,
    TerminationRight,
)

__all__ = [
    # Lease schemas
    "Lease",
    "LeaseType",
    "PropertyUseType",
    "EscalationType",
    "Address",
    "Party",
    "RentEscalation",
    "RenewalOption",
    "TerminationRight",
    "OperatingExpenses",
    # Amendment schemas
    "Amendment",
    "AmendmentType",
    "ModifiedProvision",
    # Conflict schemas
    "Conflict",
    "ConflictCategory",
    "ConflictSeverity",
    "ConflictEvidence",
    "ConflictReport",
    "DocumentReference",
    "SuggestedResolution",
]
