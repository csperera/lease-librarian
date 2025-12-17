import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from src.schemas.lease import Lease

class LeaseStorage:
    """
    Thread-safe JSON file storage for lease data.
    
    Persists lease extraction results to a local JSON file.
    Provides methods to add, retrieve, list, and delete leases.
    """
    
    def __init__(self, storage_file: str = "src/storage/lease_store.json"):
        """
        Initialize storage manager.
        
        Args:
            storage_file: Path to the JSON storage file.
        """
        self.storage_file = storage_file
        self._lock = threading.Lock()
        self._ensure_storage_exists()
        
    def _ensure_storage_exists(self) -> None:
        """Create storage directory and file if they don't exist."""
        path = Path(self.storage_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if not path.exists():
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file with lock."""
        with self._lock:
            if not os.path.exists(self.storage_file):
                return {}
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}

    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save data to JSON file with lock."""
        with self._lock:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)

    def add_lease(self, lease: Lease, lease_id: str) -> None:
        """
        Add or update a lease in storage.
        
        Args:
            lease: The Lease object to store.
            lease_id: Unique identifier for the lease.
        """
        data = self._load_data()
        
        # Prepare preview data strings
        addr_str = "N/A"
        if lease.property_address:
            addr = lease.property_address
            # Handle both object and dict access just in case
            if hasattr(addr, 'street_address'):
                addr_str = f"{addr.street_address}, {addr.city}, {addr.state}"
            elif isinstance(addr, dict):
                 addr_str = f"{addr.get('street_address')}, {addr.get('city')}, {addr.get('state')}"

        tenant_name = "N/A"
        if lease.tenant:
            tenant_name = lease.tenant.legal_name
            
        landlord_name = "N/A"
        if lease.landlord:
            landlord_name = lease.landlord.legal_name
            
        rent = 0.0
        if lease.base_rent_monthly:
            rent = float(lease.base_rent_monthly)

        lease_entry = {
            "id": lease_id,
            "property_address": addr_str,
            "tenant": tenant_name,
            "landlord": landlord_name,
            "monthly_rent": rent,
            "lease_type": lease.lease_type.value if lease.lease_type else None,
            "extracted_at": datetime.now().isoformat(),
            "full_lease_data": lease.model_dump(mode='json')  # Pydantic v2 serialization
        }
        
        data[lease_id] = lease_entry
        self._save_data(data)

    def get_lease(self, lease_id: str) -> Optional[Lease]:
        """
        Retrieve a full Lease object by ID.
        
        Args:
            lease_id: The lease identifier.
            
        Returns:
            Lease object if found, None otherwise.
        """
        data = self._load_data()
        if lease_id not in data:
            return None
            
        entry = data[lease_id]
        if "full_lease_data" not in entry:
            return None
            
        try:
            return Lease.model_validate(entry["full_lease_data"])
        except Exception as e:
            print(f"Error deserializing lease {lease_id}: {e}")
            return None

    def get_all_leases(self) -> List[Dict[str, Any]]:
        """
        Get a list of all leases with preview data only.
        
        Returns:
            List of dictionaries containing lease metadata.
        """
        data = self._load_data()
        previews = []
        for lid, entry in data.items():
            previews.append({
                "id": entry.get("id", lid),
                "property_address": entry.get("property_address"),
                "tenant": entry.get("tenant"),
                "landlord": entry.get("landlord"),
                "monthly_rent": entry.get("monthly_rent"),
                "lease_type": entry.get("lease_type"),
                "extracted_at": entry.get("extracted_at")
            })
        return previews

    def delete_lease(self, lease_id: str) -> bool:
        """
        Delete a lease from storage.
        
        Returns:
            True if deleted, False if not found.
        """
        data = self._load_data()
        if lease_id in data:
            del data[lease_id]
            self._save_data(data)
            return True
        return False

    def clear_all(self) -> None:
        """Delete all stored leases."""
        self._save_data({})
        
    def lease_exists(self, lease_id: str) -> bool:
        """Check if a lease exists in storage."""
        data = self._load_data()
        return lease_id in data
