# Lease Digitizer - Testing Strategy

## Overview

This document outlines the testing approach for the Lease Digitizer system, covering unit tests, integration tests, and end-to-end validation.

---

## Testing Philosophy

1. **Test critical paths first** - Focus on extraction accuracy and conflict detection
2. **Mock expensive operations** - Avoid real API calls in unit tests
3. **Use realistic fixtures** - Test data should mirror production documents
4. **Measure confidence** - Track extraction accuracy over time

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_document_classifier.py
│   ├── test_lease_extractor.py
│   ├── test_conflict_detector.py
│   ├── test_pdf_parser.py
│   └── test_schemas.py
├── integration/             # Integration tests
│   ├── test_pipeline.py
│   └── test_dashboard.py
└── fixtures/                # Test data
    ├── sample_lease.txt
    ├── sample_amendment.txt
    └── expected_outputs/
```

---

## Unit Testing

### Coverage Targets

| Component | Target Coverage |
|-----------|-----------------|
| Schemas (Pydantic) | 95% |
| Utils | 90% |
| Tools | 85% |
| Agents | 80% |

### Document Classifier Tests

```python
class TestDocumentClassifier:
    def test_classify_base_lease(self):
        """Verify base lease classification."""
        pass
    
    def test_classify_amendment(self):
        """Verify amendment classification."""
        pass
    
    def test_empty_document_raises_error(self):
        """Empty input should raise ValueError."""
        pass
    
    def test_confidence_threshold(self):
        """Low confidence should flag for review."""
        pass
```

### Lease Extractor Tests

```python
class TestLeaseExtractor:
    def test_extract_tenant_name(self):
        """Verify tenant extraction."""
        pass
    
    def test_extract_financial_terms(self):
        """Verify rent extraction and formatting."""
        pass
    
    def test_extract_dates(self):
        """Verify date normalization."""
        pass
    
    def test_confidence_scoring(self):
        """Verify confidence calculation logic."""
        pass
    
    def test_missing_fields_tracked(self):
        """Verify missing field detection."""
        pass
```

### Conflict Detector Tests

```python
class TestConflictDetector:
    def test_add_lease_to_memory(self):
        """Verify document memory storage."""
        pass
    
    def test_detect_rent_conflict(self):
        """Verify rent mismatch detection."""
        pass
    
    def test_detect_date_conflict(self):
        """Verify date inconsistency detection."""
        pass
    
    def test_conflict_severity_assignment(self):
        """Verify correct severity levels."""
        pass
```

---

## Integration Testing

### Pipeline Tests

```python
class TestProcessingPipeline:
    def test_full_pipeline_execution(self):
        """
        Test complete flow:
        PDF → Classifier → Extractor → Conflict Detection
        """
        pass
    
    def test_batch_processing(self):
        """Process multiple documents in sequence."""
        pass
    
    def test_error_recovery(self):
        """Pipeline should continue after single doc failure."""
        pass
```

### Dashboard Tests

```python
class TestDashboard:
    def test_page_loads(self):
        """All pages should render without error."""
        pass
    
    def test_file_upload_workflow(self):
        """Upload → Process → Display results."""
        pass
    
    def test_conflict_resolution_workflow(self):
        """View → Resolve → Update status."""
        pass
```

---

## Test Fixtures

### Sample Lease Text

```python
SAMPLE_LEASE = """
COMMERCIAL LEASE AGREEMENT

This Lease Agreement dated January 1, 2024

LANDLORD: ABC Properties LLC
TENANT: XYZ Corporation

PROPERTY: 123 Main Street, Suite 400, Dallas, TX 75201
Rentable Square Feet: 5,000 square feet

TERM: 
Commencement Date: January 1, 2024
Expiration Date: December 31, 2026

RENT:
Base Rent: $10,000.00 per month
"""
```

### Expected Extraction

```python
EXPECTED_LEASE = {
    "tenant": {"legal_name": "XYZ Corporation"},
    "landlord": {"legal_name": "ABC Properties LLC"},
    "property_address": {
        "street_address": "123 Main Street, Suite 400",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75201"
    },
    "rentable_square_feet": 5000,
    "base_rent_monthly": 10000.00,
    "commencement_date": "2024-01-01",
    "expiration_date": "2026-12-31"
}
```

---

## Mocking Strategy

### Mock LLM Responses

```python
@pytest.fixture
def mock_llm():
    """Mock OpenAI API calls."""
    with patch('langchain_openai.ChatOpenAI') as mock:
        mock.return_value.invoke.return_value = MOCK_RESPONSE
        yield mock
```

### Mock Settings

```python
@pytest.fixture
def mock_settings(monkeypatch):
    """Mock environment for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("ENVIRONMENT", "test")
```

---

## Running Tests

### All Tests
```bash
pytest
```

### With Coverage
```bash
pytest --cov=src --cov-report=html
```

### Specific Category
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
```

### Skip API Tests
```bash
pytest -m "not requires_api"
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=src
```

---

## Performance Testing

### Benchmarks

| Operation | Target | Measured |
|-----------|--------|----------|
| PDF parse (10 pages) | < 2s | TBD |
| Classification | < 5s | TBD |
| Extraction | < 30s | TBD |
| Conflict detection | < 10s | TBD |

### Load Testing (Future)

- Process 100 documents concurrently
- Measure memory usage
- Identify bottlenecks

---

## Test Maintenance

### Review Cadence

- **Weekly:** Run full test suite
- **Per PR:** Run affected tests
- **Monthly:** Review coverage metrics
- **Quarterly:** Update fixtures with new document patterns

### Known Limitations

1. Cannot test actual API responses without costs
2. PDF parsing tests require sample files
3. Dashboard tests need Streamlit test runner

---

## Future Enhancements

- [ ] Property-based testing (Hypothesis)
- [ ] Mutation testing
- [ ] Visual regression testing for dashboard
- [ ] A/B testing for extraction prompts
- [ ] Automated accuracy benchmarking
