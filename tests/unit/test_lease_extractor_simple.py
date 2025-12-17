"""
Lease Digitizer - Simple Test for Lease Extractor

A runnable test to verify the LeaseExtractorAgent works with a sample lease.
Run directly with: python tests/unit/test_lease_extractor_simple.py
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


SAMPLE_LEASE = """
COMMERCIAL LEASE AGREEMENT

This Lease Agreement dated January 1, 2024

LANDLORD: ABC Properties LLC, a Texas limited liability company
TENANT: XYZ Corporation, a Delaware corporation

PROPERTY: 123 Main Street, Suite 400, Dallas, TX 75201
Rentable Square Feet: 5,000 square feet

TERM: 
Commencement Date: January 1, 2024
Expiration Date: December 31, 2026
Lease Term: 36 months

RENT:
Base Rent: $10,000.00 per month
Annual Rent: $120,000.00

The Tenant agrees to pay rent on the first day of each month.
"""


def test_lease_extraction():
    """Test the LeaseExtractorAgent with a sample lease document."""
    
    print("=" * 60)
    print("Lease Extractor Test")
    print("=" * 60)
    
    # Check for API key first
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n❌ ERROR: OPENAI_API_KEY environment variable is not set.")
        print("Please set your OpenAI API key:")
        print("  Windows:  set OPENAI_API_KEY=sk-your-key-here")
        print("  Linux/Mac: export OPENAI_API_KEY=sk-your-key-here")
        print("\nOr create a .env file in the project root with:")
        print("  OPENAI_API_KEY=sk-your-key-here")
        return False
    
    print(f"\n✅ API Key found (starts with: {api_key[:10]}...)")
    
    # Import after path setup
    try:
        from src.agents.lease_extractor import LeaseExtractorAgent
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("Make sure you're running from the project root directory.")
        return False
    
    print("\n📄 Sample Lease Text:")
    print("-" * 40)
    print(SAMPLE_LEASE[:200] + "...")
    print("-" * 40)
    
    # Initialize the extractor
    print("\n🔧 Initializing LeaseExtractorAgent...")
    try:
        extractor = LeaseExtractorAgent(verbose=True)
        print("   ✅ Agent initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize agent: {e}")
        return False
    
    # Extract lease data
    print("\n🚀 Extracting lease data...")
    print("   (This may take 10-30 seconds...)")
    
    try:
        result = extractor.extract_lease(
            document_text=SAMPLE_LEASE,
            document_id="test-lease-001"
        )
    except Exception as e:
        print(f"\n❌ Extraction failed with error: {e}")
        return False
    
    # Check results
    print("\n" + "=" * 60)
    print("EXTRACTION RESULTS")
    print("=" * 60)
    
    if result.lease is None:
        print("\n❌ No lease object returned")
        print(f"   Raw response: {result.raw_response}")
        return False
    
    print("\n✅ Lease object extracted successfully!")
    
    # Print extracted data
    lease = result.lease
    
    print("\n📋 Extracted Data:")
    print("-" * 40)
    
    # Tenant info
    if lease.tenant:
        print(f"   Tenant: {lease.tenant.legal_name}")
    else:
        print("   Tenant: Not extracted")
    
    # Landlord info
    if lease.landlord:
        print(f"   Landlord: {lease.landlord.legal_name}")
    else:
        print("   Landlord: Not extracted")
    
    # Property info
    if lease.property_address:
        addr = lease.property_address
        print(f"   Property: {addr.street_address}, {addr.city}, {addr.state} {addr.zip_code}")
    else:
        print("   Property: Not extracted")
    
    # Square footage
    if lease.rentable_square_feet:
        print(f"   Square Feet: {lease.rentable_square_feet:,}")
    else:
        print("   Square Feet: Not extracted")
    
    # Dates
    print(f"   Commencement: {lease.commencement_date}")
    print(f"   Expiration: {lease.expiration_date}")
    print(f"   Term (months): {lease.term_months}")
    
    # Rent
    if lease.base_rent_monthly:
        print(f"   Monthly Rent: ${lease.base_rent_monthly:,.2f}")
    else:
        print("   Monthly Rent: Not extracted")
    
    if lease.base_rent_annual:
        print(f"   Annual Rent: ${lease.base_rent_annual:,.2f}")
    else:
        print("   Annual Rent: Not extracted")
    
    # Metadata
    print("\n📊 Extraction Metadata:")
    print("-" * 40)
    print(f"   Confidence Score: {lease.confidence_score:.2%}")
    print(f"   Total Fields: {result.metadata.total_fields}")
    print(f"   Extracted Fields: {result.metadata.extracted_fields}")
    print(f"   Processing Time: {result.metadata.processing_time_seconds:.2f}s")
    
    if result.metadata.missing_fields:
        print(f"   Missing Fields: {', '.join(result.metadata.missing_fields)}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED SUCCESSFULLY ✅")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("📁 Loaded .env file")
    except ImportError:
        print("ℹ️  python-dotenv not installed, using environment variables directly")
    
    success = test_lease_extraction()
    sys.exit(0 if success else 1)
