import sys
import os
import time
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.lease_extractor import LeaseExtractorAgent

SAMPLE_LEASE = """
COMMERCIAL LEASE AGREEMENT

This Lease Agreement is made on January 1, 2024

LANDLORD: ABC Properties LLC, a Texas limited liability company
          123 Property Lane, Dallas, TX 75201

TENANT:   XYZ Corporation, a Delaware corporation
          456 Business Drive, Dallas, TX 75202

PREMISES: 123 Main Street, Suite 400, Dallas, Texas 75201
          Rentable Square Feet: 5,000 square feet

LEASE TERM:
Commencement Date: January 1, 2024
Expiration Date: December 31, 2026
Total Term: 36 months (3 years)

RENT:
Base Monthly Rent: $10,000.00
Annual Rent: $120,000.00
Rent per Square Foot: $24.00 per year

RENT ESCALATION:
Annual increase of 3% beginning January 1, 2025

SECURITY DEPOSIT: $20,000.00

LEASE TYPE: Triple Net (NNN)
Tenant responsible for: property taxes, insurance, and common area maintenance

The Tenant shall pay rent on the first day of each calendar month.
"""

def main():
    # Load environment variables
    load_dotenv()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please ensure you have a .env file with your API key.")
        return

    print("🚀 Starting Lease Extraction Test...")
    print("-" * 50)

    try:
        # Initialize agent
        # Use gpt-4o-mini for testing as it's reliable and cost-effective
        # You can remove model_name arg to use the default from settings/env
        extractor = LeaseExtractorAgent(model_name="gpt-4o-mini", verbose=False)
        
        print("Agent initialized. Extracting data from sample lease...")
        start_time = time.time()
        
        # Extract lease
        result = extractor.extract_lease(SAMPLE_LEASE, "test-001")
        
        elapsed_time = time.time() - start_time
        
        if not result.lease:
            print(f"\n❌ Extraction failed. Raw response: {result.raw_response}")
            return

        lease = result.lease
        metadata = result.metadata

        # Print Results
        print("\n✅ EXTRACTION SUCCESSFUL")
        print("=" * 50)
        
        print(f"📄 Document ID:     {lease.document_id}")
        
        # Parties
        tenant_name = lease.tenant.legal_name if lease.tenant else "N/A"
        landlord_name = lease.landlord.legal_name if lease.landlord else "N/A"
        print(f"🏢 Tenant:          {tenant_name}")
        print(f"🏛️  Landlord:        {landlord_name}")
        
        # Property
        address = "N/A"
        if lease.property_address:
            addr = lease.property_address
            address = f"{addr.street_address}, {addr.city}, {addr.state} {addr.zip_code}"
        print(f"📍 Property:        {address}")
        
        sq_ft = f"{lease.rentable_square_feet:,.0f}" if lease.rentable_square_feet else "N/A"
        print(f"📐 Size:            {sq_ft} sq ft")
        
        # Financials
        rent = f"${lease.base_rent_monthly:,.2f}" if lease.base_rent_monthly else "N/A"
        print(f"💰 Monthly Rent:    {rent}")
        
        # Dates
        commence = lease.commencement_date.strftime('%Y-%m-%d') if lease.commencement_date else "N/A"
        expire = lease.expiration_date.strftime('%Y-%m-%d') if lease.expiration_date else "N/A"
        print(f"📅 Term:            {commence} to {expire}")
        
        print("-" * 50)
        
        # Confidence and Metadata
        score = lease.confidence_score * 100 if lease.confidence_score else 0
        print(f"🎯 Confidence:      {score:.1f}%")
        print(f"⏱️  Processing Time: {result.metadata.processing_time_seconds:.2f}s")
        
        if metadata.missing_fields:
            print("\n⚠️  Possible Missing Fields:")
            for field in metadata.missing_fields:
                print(f"  - {field}")
        else:
            print("\n✨ All critical fields extracted!")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
