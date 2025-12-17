# Lease Digitizer - Examples

This directory contains example files and documentation for using Lease Digitizer.

## Contents

- `sample_leases/` - Directory for PDF lease documents to process

## Quick Start Example

```python
from src import DocumentClassifierAgent, LeaseExtractorAgent, ConflictDetectorAgent
from src.utils import DocumentLoader

# Initialize agents
classifier = DocumentClassifierAgent()
extractor = LeaseExtractorAgent()
conflict_detector = ConflictDetectorAgent()

# Load documents
loader = DocumentLoader()
documents = loader.load_directory("examples/sample_leases")

# Process each document
for path, doc in documents:
    # Classify
    classification = classifier.classify(doc.full_text, doc.metadata.filename)
    print(f"{path}: {classification.document_type}")
    
    # Extract based on type
    if classification.document_type == "base_lease":
        result = extractor.extract_lease(doc.full_text, doc.metadata.filename)
        conflict_detector.add_lease(result.lease)
    elif classification.document_type == "amendment":
        result = extractor.extract_amendment(doc.full_text, doc.metadata.filename)
        conflict_detector.add_amendment(result.amendment, base_lease_id="...")

# Detect conflicts
report = conflict_detector.detect_conflicts("base_lease_id")
print(f"Found {report.total_conflicts} conflicts")
```

## Running the Dashboard

```bash
streamlit run src/dashboard/app.py
```

## Running from CLI

```bash
python -m src.main --input examples/sample_leases --output ./output
```
