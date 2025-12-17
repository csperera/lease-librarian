"""
Lease Digitizer - Financial Calculator Tool

A custom LangChain tool for performing financial calculations common
in commercial real estate leases. Handles rent calculations, escalations,
CAM reconciliations, and more.

Key Features:
- Rent calculation and verification
- Escalation schedule computation
- Pro-rata calculations
- CAM/operating expense calculations
- Present value and NPV analysis
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional

from langchain_core.tools import BaseTool
from pydantic import Field


class EscalationType(str, Enum):
    """Types of rent escalation."""
    FIXED_PERCENTAGE = "fixed_percentage"
    FIXED_AMOUNT = "fixed_amount"
    CPI = "cpi"


@dataclass
class RentScheduleItem:
    """
    Single item in a rent schedule.
    
    Attributes:
        period_start: Start date of period
        period_end: End date of period
        monthly_rent: Monthly rent amount
        annual_rent: Annual rent amount
        rent_psf: Rent per square foot
    """
    period_start: date
    period_end: date
    monthly_rent: Decimal
    annual_rent: Decimal
    rent_psf: Optional[Decimal] = None


@dataclass
class RentSchedule:
    """
    Complete rent schedule over lease term.
    
    Attributes:
        items: Individual rent periods
        total_rent: Total rent over entire term
        average_rent: Average monthly rent
    """
    items: list[RentScheduleItem]
    total_rent: Decimal
    average_rent: Decimal


@dataclass
class ProRataResult:
    """
    Result of pro-rata calculation.
    
    Attributes:
        full_period_amount: Full period amount
        days_in_period: Total days in period
        days_applicable: Days to prorate
        prorated_amount: Calculated prorated amount
    """
    full_period_amount: Decimal
    days_in_period: int
    days_applicable: int
    prorated_amount: Decimal


class FinancialCalculatorTool(BaseTool):
    """
    LangChain tool for commercial real estate financial calculations.
    
    Provides validated calculations for rent, escalations, and expenses.
    
    Example:
        >>> calc = FinancialCalculatorTool()
        >>> schedule = calc.calculate_rent_schedule(
        ...     base_rent=10000,
        ...     start_date=date(2024, 1, 1),
        ...     term_months=60,
        ...     escalation_type="fixed_percentage",
        ...     escalation_value=3.0,
        ... )
    """
    
    name: str = "financial_calculator"
    description: str = (
        "Perform financial calculations for commercial real estate leases. "
        "Can calculate rent schedules, escalations, pro-rata amounts, and more."
    )
    
    precision: int = Field(
        default=2,
        description="Decimal precision for calculations"
    )
    
    def _run(self, query: str) -> str:
        """
        Process a financial calculation query.
        
        Args:
            query: Natural language calculation request
            
        Returns:
            Calculation result as string
        """
        # TODO: Implement natural language query parsing
        # Parse the query and route to appropriate calculation method
        raise NotImplementedError("Query processing not yet implemented")
    
    async def _arun(self, query: str) -> str:
        """Async version of _run."""
        return self._run(query)
    
    def _round(self, value: Decimal) -> Decimal:
        """Round a decimal to configured precision."""
        return value.quantize(
            Decimal(10) ** -self.precision,
            rounding=ROUND_HALF_UP
        )
    
    def calculate_rent_schedule(
        self,
        base_rent: Decimal,
        start_date: date,
        term_months: int,
        escalation_type: EscalationType = EscalationType.FIXED_PERCENTAGE,
        escalation_value: Decimal = Decimal("0"),
        escalation_frequency_months: int = 12,
        square_feet: Optional[Decimal] = None,
    ) -> RentSchedule:
        """
        Calculate a complete rent schedule with escalations.
        
        Args:
            base_rent: Starting monthly rent
            start_date: Lease commencement date
            term_months: Total lease term in months
            escalation_type: Type of escalation
            escalation_value: Percentage or fixed amount
            escalation_frequency_months: Months between escalations
            square_feet: Rentable square feet for PSF calculation
            
        Returns:
            RentSchedule with all periods and totals
        """
        # TODO: Implement rent schedule calculation
        # 1. Create initial period
        # 2. Apply escalations at specified frequency
        # 3. Handle partial periods
        # 4. Calculate totals and averages
        
        raise NotImplementedError("Rent schedule calculation not yet implemented")
    
    def calculate_escalated_rent(
        self,
        current_rent: Decimal,
        escalation_type: EscalationType,
        escalation_value: Decimal,
        periods: int = 1,
    ) -> Decimal:
        """
        Calculate rent after applying escalation(s).
        
        Args:
            current_rent: Current rent amount
            escalation_type: Type of escalation
            escalation_value: Percentage or fixed amount
            periods: Number of escalation periods to apply
            
        Returns:
            Escalated rent amount
        """
        if escalation_type == EscalationType.FIXED_PERCENTAGE:
            multiplier = (1 + escalation_value / 100) ** periods
            return self._round(current_rent * Decimal(str(multiplier)))
        elif escalation_type == EscalationType.FIXED_AMOUNT:
            return self._round(current_rent + (escalation_value * periods))
        else:
            raise ValueError(f"Unsupported escalation type: {escalation_type}")
    
    def calculate_prorate(
        self,
        full_amount: Decimal,
        period_start: date,
        period_end: date,
        prorate_start: date,
        prorate_end: date,
    ) -> ProRataResult:
        """
        Calculate pro-rata amount for a partial period.
        
        Args:
            full_amount: Full period amount
            period_start: Start of full period
            period_end: End of full period
            prorate_start: Start of prorated period
            prorate_end: End of prorated period
            
        Returns:
            ProRataResult with calculation details
        """
        # TODO: Implement prorate calculation
        raise NotImplementedError("Prorate calculation not yet implemented")
    
    def calculate_rent_per_sqft(
        self,
        annual_rent: Decimal,
        square_feet: Decimal,
    ) -> Decimal:
        """
        Calculate rent per square foot.
        
        Args:
            annual_rent: Total annual rent
            square_feet: Rentable square feet
            
        Returns:
            Rent per square foot
        """
        if square_feet <= 0:
            raise ValueError("Square feet must be positive")
        return self._round(annual_rent / square_feet)
    
    def calculate_annual_from_monthly(self, monthly_rent: Decimal) -> Decimal:
        """Calculate annual rent from monthly."""
        return self._round(monthly_rent * 12)
    
    def calculate_monthly_from_annual(self, annual_rent: Decimal) -> Decimal:
        """Calculate monthly rent from annual."""
        return self._round(annual_rent / 12)
    
    def calculate_cam_share(
        self,
        total_building_sf: Decimal,
        tenant_sf: Decimal,
        total_expenses: Decimal,
    ) -> dict:
        """
        Calculate tenant's share of operating expenses.
        
        Args:
            total_building_sf: Total building square feet
            tenant_sf: Tenant's square footage
            total_expenses: Total operating expenses
            
        Returns:
            Dictionary with share percentage and amount
        """
        # TODO: Implement CAM calculation
        raise NotImplementedError("CAM calculation not yet implemented")
    
    def calculate_npv(
        self,
        cash_flows: list[Decimal],
        discount_rate: Decimal,
    ) -> Decimal:
        """
        Calculate Net Present Value of cash flows.
        
        Args:
            cash_flows: List of cash flows by period
            discount_rate: Annual discount rate (as decimal, e.g., 0.05 for 5%)
            
        Returns:
            NPV of cash flows
        """
        # TODO: Implement NPV calculation
        raise NotImplementedError("NPV calculation not yet implemented")
    
    def verify_calculation(
        self,
        stated_value: Decimal,
        calculated_value: Decimal,
        tolerance_percent: Decimal = Decimal("0.01"),
    ) -> tuple[bool, Decimal]:
        """
        Verify a stated value against calculated value.
        
        Args:
            stated_value: Value stated in document
            calculated_value: Independently calculated value
            tolerance_percent: Acceptable variance percentage
            
        Returns:
            Tuple of (is_match, difference)
        """
        difference = abs(stated_value - calculated_value)
        tolerance = stated_value * tolerance_percent
        is_match = difference <= tolerance
        return is_match, difference


# TODO: Add support for complex escalation formulas
# TODO: Add CPI index integration
# TODO: Add support for free rent and abatement periods
# TODO: Add lease comparison and analysis functions
# TODO: Add support for different fiscal year calculations
