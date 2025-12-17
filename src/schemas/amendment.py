"""
Lease Digitizer - Amendment Schema Module

This module defines Pydantic models for lease amendment data.
Amendments modify existing lease terms and require tracking of:
- Which provisions are being modified
- The original vs. amended values
- Effective dates of changes
- References to the original lease
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AmendmentType(str, Enum):
    """Types of lease amendments."""
    RENT_MODIFICATION = "rent_modification"
    TERM_EXTENSION = "term_extension"
    TERM_REDUCTION = "term_reduction"
    SPACE_EXPANSION = "space_expansion"
    SPACE_REDUCTION = "space_reduction"
    ASSIGNMENT = "assignment"
    SUBLEASE_CONSENT = "sublease_consent"
    USE_CHANGE = "use_change"
    OTHER = "other"


class ModifiedProvision(BaseModel):
    """
    Details of a single provision being modified by an amendment.
    
    Attributes:
        provision_name: Name/title of the modified provision
        section_reference: Reference to section in original lease
        original_value: Value before amendment
        amended_value: Value after amendment
        effective_date: When the change takes effect
        notes: Additional notes about the modification
    """
    provision_name: str = Field(..., description="Name of modified provision")
    section_reference: Optional[str] = Field(default=None, description="Section reference")
    original_value: Optional[Any] = Field(default=None, description="Original value")
    amended_value: Optional[Any] = Field(default=None, description="Amended value")
    effective_date: Optional[date] = Field(default=None, description="Effective date")
    notes: Optional[str] = Field(default=None, description="Modification notes")


class Amendment(BaseModel):
    """
    Complete lease amendment data structure.
    
    Captures all relevant information from a lease amendment document,
    including references to the original lease and detailed tracking
    of all modified provisions.
    
    Attributes:
        document_id: Unique identifier for this amendment
        amendment_number: Sequential amendment number (1st, 2nd, etc.)
        amendment_date: Date amendment was executed
        effective_date: Date changes take effect
        
        original_lease_reference: Reference to base lease
        original_lease_date: Date of original lease
        property_reference: Property identifier/address
        
        landlord_name: Current landlord name
        tenant_name: Current tenant name
        
        amendment_types: Categories of changes made
        modified_provisions: Detailed provision changes
        
        new_expiration_date: If term is extended
        additional_rent: Any additional rent amounts
        rent_credit: Any rent credits given
        
        consideration: Consideration for amendment
        
        confidence_score: Extraction confidence (0-1)
        extraction_notes: Notes about extraction quality
    """
    
    # Document identification
    document_id: str = Field(..., description="Unique document identifier")
    amendment_number: Optional[int] = Field(default=None, ge=1, description="Amendment number")
    amendment_date: Optional[date] = Field(default=None, description="Amendment execution date")
    effective_date: Optional[date] = Field(default=None, description="Effective date of changes")
    
    # Reference to original lease
    original_lease_reference: Optional[str] = Field(default=None, description="Original lease reference")
    original_lease_date: Optional[date] = Field(default=None, description="Original lease date")
    property_reference: Optional[str] = Field(default=None, description="Property reference")
    
    # Parties (may differ from original if assigned)
    landlord_name: Optional[str] = Field(default=None, description="Current landlord")
    tenant_name: Optional[str] = Field(default=None, description="Current tenant")
    
    # Amendment details
    amendment_types: list[AmendmentType] = Field(default_factory=list, description="Types of changes")
    modified_provisions: list[ModifiedProvision] = Field(
        default_factory=list, description="Modified provisions"
    )
    
    # Common modifications
    new_expiration_date: Optional[date] = Field(default=None, description="New expiration date")
    additional_rent: Optional[Decimal] = Field(default=None, description="Additional rent")
    rent_credit: Optional[Decimal] = Field(default=None, description="Rent credit amount")
    
    # Consideration
    consideration: Optional[str] = Field(default=None, description="Amendment consideration")
    
    # Full text excerpts
    recitals: Optional[str] = Field(default=None, description="Recitals/background section")
    
    # Extraction metadata
    confidence_score: float = Field(default=0.0, ge=0, le=1, description="Extraction confidence")
    extraction_notes: list[str] = Field(default_factory=list, description="Extraction notes")
    
    def get_modifications_by_type(self, provision_name: str) -> list[ModifiedProvision]:
        """
        Get all modifications for a specific provision type.
        
        Args:
            provision_name: Name of the provision to filter by
            
        Returns:
            List of modifications matching the provision name
        """
        return [m for m in self.modified_provisions if m.provision_name == provision_name]


# TODO: Add method to apply amendment to base Lease object
# TODO: Add validation for amendment sequence (dates should be after original)
# TODO: Add support for tracking multiple amendments on same lease
