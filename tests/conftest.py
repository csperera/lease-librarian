"""
Lease Digitizer - Test Configuration

Pytest configuration and shared fixtures for all tests.
"""

import pytest
from pathlib import Path
from typing import Generator


@pytest.fixture
def sample_lease_text() -> str:
    """Sample base lease text for testing."""
    return """
    COMMERCIAL LEASE AGREEMENT
    
    This Lease Agreement ("Lease") is entered into as of January 15, 2024
    by and between:
    
    LANDLORD: ABC Properties LLC, a Delaware limited liability company
    TENANT: XYZ Corporation, a California corporation
    
    ARTICLE 1. PREMISES
    Landlord hereby leases to Tenant the premises located at:
    123 Main Street, Suite 500
    New York, NY 10001
    
    The Premises contains approximately 10,000 rentable square feet.
    
    ARTICLE 2. TERM
    The initial term shall be five (5) years, commencing on February 1, 2024
    and expiring on January 31, 2029.
    
    ARTICLE 3. BASE RENT
    Tenant shall pay Base Rent of $50,000.00 per month ($600,000.00 annually).
    
    ARTICLE 4. SECURITY DEPOSIT
    Upon execution, Tenant shall deposit $100,000.00 as security.
    """


@pytest.fixture
def sample_amendment_text() -> str:
    """Sample amendment text for testing."""
    return """
    FIRST AMENDMENT TO LEASE
    
    This First Amendment to Lease ("Amendment") is entered into as of 
    June 1, 2025 by and between:
    
    LANDLORD: ABC Properties LLC
    TENANT: XYZ Corporation
    
    RECITALS
    
    WHEREAS, Landlord and Tenant entered into that certain Commercial Lease
    Agreement dated January 15, 2024 (the "Lease") for premises located at
    123 Main Street, Suite 500, New York, NY 10001; and
    
    WHEREAS, the parties desire to modify certain terms of the Lease;
    
    NOW, THEREFORE, the parties agree as follows:
    
    1. BASE RENT MODIFICATION
    Effective July 1, 2025, the monthly Base Rent shall be increased to
    $52,500.00 per month ($630,000.00 annually).
    
    2. All other terms remain unchanged.
    """


@pytest.fixture
def temp_pdf_directory(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory with sample PDF placeholders."""
    pdf_dir = tmp_path / "sample_leases"
    pdf_dir.mkdir()
    
    # Create placeholder files (not actual PDFs for unit tests)
    (pdf_dir / "base_lease_001.pdf").touch()
    (pdf_dir / "amendment_001.pdf").touch()
    
    yield pdf_dir


@pytest.fixture
def mock_settings(monkeypatch) -> None:
    """Mock settings for testing without real API keys."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-for-testing-only")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("ENVIRONMENT", "development")


# TODO: Add fixtures for mock LLM responses
# TODO: Add fixtures for sample Lease/Amendment objects
# TODO: Add fixtures for ConflictReport objects
