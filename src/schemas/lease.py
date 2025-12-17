"""
Lease Digitizer - Lease Schema Module

This module defines Pydantic models for structured lease data extraction.
These schemas enforce data validation and provide a standardized format
for lease information across the application.

The models follow commercial real estate industry standards and capture
all essential lease data points including:
- Party information (landlord, tenant, guarantors)
- Property details (address, square footage, use type)
- Term information (dates, options, renewals)
- Financial terms (rent, escalations, deposits)
- Key clauses and provisions
"""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class LeaseType(str, Enum):
    """Types of commercial leases."""
    GROSS = "gross"
    MODIFIED_GROSS = "modified_gross"
    NET = "net"
    DOUBLE_NET = "double_net"
    TRIPLE_NET = "triple_net"
    ABSOLUTE_NET = "absolute_net"


class PropertyUseType(str, Enum):
    """Permitted property use categories."""
    OFFICE = "office"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    WAREHOUSE = "warehouse"
    MIXED_USE = "mixed_use"
    RESTAURANT = "restaurant"
    MEDICAL = "medical"
    OTHER = "other"


class EscalationType(str, Enum):
    """Types of rent escalation provisions."""
    FIXED_PERCENTAGE = "fixed_percentage"
    CPI = "cpi"
    FIXED_AMOUNT = "fixed_amount"
    MARKET_RATE = "market_rate"
    NONE = "none"


class Address(BaseModel):
    """
    Property address with full details.
    
    Attributes:
        street_address: Street address including suite/unit number
        city: City name
        state: State or province (2-letter code preferred)
        zip_code: ZIP or postal code
        country: Country code (defaults to US)
    """
    street_address: str = Field(..., min_length=1, description="Street address")
    city: str = Field(..., min_length=1, description="City")
    state: str = Field(..., min_length=2, max_length=50, description="State/Province")
    zip_code: str = Field(..., min_length=1, description="ZIP/Postal code")
    country: str = Field(default="US", description="Country code")
    
    @field_validator("state")
    @classmethod
    def normalize_state(cls, v: str) -> str:
        """Normalize state to uppercase."""
        return v.upper().strip()


class Party(BaseModel):
    """
    Lease party (landlord, tenant, or guarantor) information.
    
    Attributes:
        legal_name: Full legal name of the party
        entity_type: Type of entity (individual, corporation, LLC, etc.)
        address: Party's address
        contact_name: Primary contact person
        contact_email: Contact email address
        contact_phone: Contact phone number
    """
    legal_name: str = Field(..., min_length=1, description="Legal entity name")
    entity_type: Optional[str] = Field(default=None, description="Entity type")
    address: Optional[Address] = Field(default=None, description="Party address")
    contact_name: Optional[str] = Field(default=None, description="Contact person")
    contact_email: Optional[str] = Field(default=None, description="Contact email")
    contact_phone: Optional[str] = Field(default=None, description="Contact phone")


class RentEscalation(BaseModel):
    """
    Rent escalation schedule details.
    
    Attributes:
        escalation_type: Type of escalation (CPI, fixed, etc.)
        effective_date: When escalation takes effect
        percentage: Percentage increase (if applicable)
        fixed_amount: Fixed increase amount (if applicable)
        frequency_months: How often escalation occurs
    """
    escalation_type: EscalationType = Field(..., description="Type of escalation")
    effective_date: Optional[date] = Field(default=None, description="Effective date")
    percentage: Optional[Decimal] = Field(default=None, ge=0, description="Percentage increase")
    fixed_amount: Optional[Decimal] = Field(default=None, ge=0, description="Fixed amount increase")
    frequency_months: int = Field(default=12, ge=1, description="Escalation frequency in months")


class RenewalOption(BaseModel):
    """
    Lease renewal option details.
    
    Attributes:
        option_number: Sequence number of the option
        term_months: Duration of renewal term in months
        notice_days: Days notice required to exercise
        rent_determination: How rent is determined (market, fixed increase, etc.)
    """
    option_number: int = Field(..., ge=1, description="Option sequence number")
    term_months: int = Field(..., ge=1, description="Renewal term in months")
    notice_days: int = Field(default=180, ge=0, description="Notice days required")
    rent_determination: Optional[str] = Field(default=None, description="Rent determination method")


class TerminationRight(BaseModel):
    """
    Early termination right details.
    
    Attributes:
        party: Which party has the right (landlord/tenant)
        earliest_date: Earliest date right can be exercised
        notice_days: Days notice required
        termination_fee: Fee required to terminate
        conditions: Any conditions or restrictions
    """
    party: str = Field(..., description="Party with termination right")
    earliest_date: Optional[date] = Field(default=None, description="Earliest termination date")
    notice_days: int = Field(default=180, ge=0, description="Notice days required")
    termination_fee: Optional[Decimal] = Field(default=None, ge=0, description="Termination fee")
    conditions: Optional[str] = Field(default=None, description="Termination conditions")


class OperatingExpenses(BaseModel):
    """
    Operating expense (CAM) details.
    
    Attributes:
        base_year: Base year for expense calculations
        base_amount: Base year expense amount
        tenant_share_percentage: Tenant's pro-rata share
        cap_percentage: Annual cap on increases (if any)
        exclusions: Excluded expense categories
    """
    base_year: Optional[int] = Field(default=None, ge=1900, description="Base year")
    base_amount: Optional[Decimal] = Field(default=None, ge=0, description="Base year amount")
    tenant_share_percentage: Optional[Decimal] = Field(
        default=None, ge=0, le=100, description="Tenant's share percentage"
    )
    cap_percentage: Optional[Decimal] = Field(default=None, ge=0, description="Annual cap percentage")
    exclusions: Optional[list[str]] = Field(default=None, description="Excluded expenses")


class Lease(BaseModel):
    """
    Complete commercial lease data structure.
    
    This is the primary output schema for the Lease Extractor agent.
    It captures all essential data points from a commercial real estate lease.
    
    Attributes:
        document_id: Unique identifier for the document
        lease_type: Type of lease (gross, net, etc.)
        execution_date: Date lease was signed
        
        landlord: Landlord party information
        tenant: Tenant party information
        guarantors: List of guarantor parties
        
        property_address: Leased premises address
        rentable_square_feet: Total rentable area
        usable_square_feet: Total usable area
        property_use_type: Permitted use category
        
        commencement_date: Lease start date
        expiration_date: Lease end date
        term_months: Total lease term in months
        
        base_rent_monthly: Monthly base rent amount
        base_rent_annual: Annual base rent amount
        rent_per_sqft: Rent per square foot
        rent_escalations: Scheduled rent increases
        
        security_deposit: Security deposit amount
        operating_expenses: CAM/operating expense terms
        
        renewal_options: Available renewal options
        termination_rights: Early termination provisions
        
        assignment_allowed: Whether assignment is permitted
        subletting_allowed: Whether subletting is permitted
        
        extracted_clauses: Key clauses extracted from lease
        confidence_score: Extraction confidence (0-1)
        extraction_notes: Notes about extraction quality
    """
    
    # Document identification
    document_id: str = Field(..., description="Unique document identifier")
    lease_type: Optional[LeaseType] = Field(default=None, description="Type of lease")
    execution_date: Optional[date] = Field(default=None, description="Lease execution date")
    
    # Parties
    landlord: Optional[Party] = Field(default=None, description="Landlord information")
    tenant: Optional[Party] = Field(default=None, description="Tenant information")
    guarantors: list[Party] = Field(default_factory=list, description="Guarantors")
    
    # Property
    property_address: Optional[Address] = Field(default=None, description="Property address")
    rentable_square_feet: Optional[Decimal] = Field(default=None, ge=0, description="RSF")
    usable_square_feet: Optional[Decimal] = Field(default=None, ge=0, description="USF")
    property_use_type: Optional[PropertyUseType] = Field(default=None, description="Use type")
    
    # Term
    commencement_date: Optional[date] = Field(default=None, description="Lease start date")
    expiration_date: Optional[date] = Field(default=None, description="Lease end date")
    term_months: Optional[int] = Field(default=None, ge=1, description="Term in months")
    
    # Financial - Rent
    base_rent_monthly: Optional[Decimal] = Field(default=None, ge=0, description="Monthly rent")
    base_rent_annual: Optional[Decimal] = Field(default=None, ge=0, description="Annual rent")
    rent_per_sqft: Optional[Decimal] = Field(default=None, ge=0, description="Rent per SF")
    rent_escalations: list[RentEscalation] = Field(default_factory=list, description="Escalations")
    
    # Financial - Other
    security_deposit: Optional[Decimal] = Field(default=None, ge=0, description="Security deposit")
    operating_expenses: Optional[OperatingExpenses] = Field(default=None, description="CAM terms")
    
    # Options and Rights
    renewal_options: list[RenewalOption] = Field(default_factory=list, description="Renewal options")
    termination_rights: list[TerminationRight] = Field(default_factory=list, description="Termination rights")
    
    # Assignments and Subletting
    assignment_allowed: Optional[bool] = Field(default=None, description="Assignment permitted")
    subletting_allowed: Optional[bool] = Field(default=None, description="Subletting permitted")
    
    # Extraction metadata
    extracted_clauses: dict[str, str] = Field(default_factory=dict, description="Key clauses")
    confidence_score: float = Field(default=0.0, ge=0, le=1, description="Extraction confidence")
    extraction_notes: list[str] = Field(default_factory=list, description="Extraction notes")


# TODO: Add validation for date ranges (commencement before expiration)
# TODO: Add computed properties for derived values (term in years, annual rent)
# TODO: Add serialization methods for different output formats (JSON, CSV)
# TODO: Add comparison methods for conflict detection
