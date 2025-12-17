# Lease Digitizer - Agent Design Specification

## Overview

This document provides detailed specifications for each LangChain agent in the Lease Digitizer system.

---

## Agent 1: Document Classifier

### Purpose
Classify commercial real estate documents into categories using ReAct reasoning.

### Pattern
**ReAct (Reasoning + Acting)** - Enables transparent chain-of-thought classification decisions.

### Supported Document Types

| Type | Description | Key Indicators |
|------|-------------|----------------|
| `base_lease` | Original lease agreement | "LEASE AGREEMENT", parties as Landlord/Tenant |
| `amendment` | Modification to existing lease | "AMENDMENT", references prior lease |
| `sublease` | Third-party subletting | "SUBLEASE", Sublandlord/Subtenant |
| `assignment` | Lease transfer | "ASSIGNMENT", assignor/assignee |
| `estoppel` | Certification of terms | "ESTOPPEL CERTIFICATE" |
| `snda` | Subordination agreement | "SUBORDINATION", "NON-DISTURBANCE" |
| `other` | Unclassified document | None of the above |

### Tools Available

```python
tools = [
    "analyze_header",        # Check document title/header
    "find_parties",          # Identify party roles
    "check_amendment_refs",  # Look for prior lease references
    "analyze_recitals",      # Parse WHEREAS clauses
    "check_signature_block"  # Analyze signature structure
]
```

### Output Schema

```python
class ClassificationResult:
    document_id: str
    document_type: DocumentType
    confidence: float  # 0.0 - 1.0
    reasoning: str     # Chain-of-thought explanation
    key_indicators: list[str]
    needs_review: bool  # Flag if confidence < 0.7
```

### Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `temperature` | 0.0 | Deterministic output |
| `max_iterations` | 10 | Max reasoning steps |
| `confidence_threshold` | 0.7 | Below triggers review flag |

---

## Agent 2: Lease Extractor

### Purpose
Extract structured data from classified lease documents using Pydantic validation.

### Pattern
**LLMChain + PydanticOutputParser** - Ensures type-safe, validated extraction.

### Extraction Categories

#### Party Information
- Landlord legal name, entity type, address
- Tenant legal name, entity type, address
- Guarantors (if any)

#### Property Details
- Street address, city, state, zip
- Rentable square feet (RSF)
- Usable square feet (USF)
- Property use type (office, retail, industrial)

#### Term Information
- Commencement date
- Expiration date
- Term length (months)
- Renewal options

#### Financial Terms
- Base rent (monthly/annual)
- Rent per square foot
- Escalation schedule
- Security deposit
- CAM/operating expenses

### Prompt Template

```
You are an expert commercial real estate analyst...

IMPORTANT GUIDELINES:
1. Extract data exactly as it appears
2. Use null for missing fields
3. Normalize dates to YYYY-MM-DD
4. Normalize currency to numeric values
5. Extract party names with legal entity types

{format_instructions}

LEASE DOCUMENT:
{document_text}
```

### Confidence Scoring

```python
def calculate_confidence(lease: Lease) -> float:
    critical_fields = [
        'tenant', 'landlord', 'property_address',
        'commencement_date', 'expiration_date',
        'base_rent_monthly', 'rentable_square_feet'
    ]
    
    populated = count_populated(critical_fields)
    base_confidence = populated / len(critical_fields)
    
    # Bonus for optional fields
    bonus = min(0.2, optional_count * 0.05)
    
    return min(1.0, base_confidence + bonus)
```

---

## Agent 3: Conflict Detector

### Purpose
Identify contradictions between base leases and amendments using persistent memory.

### Pattern
**OpenAI Functions Agent + ConversationBufferMemory** - Maintains context across document analysis.

### Conflict Categories

| Category | Severity | Example |
|----------|----------|---------|
| `term_conflict` | HIGH | Contradicting expiration dates |
| `rent_conflict` | CRITICAL | Different rent amounts stated |
| `party_conflict` | MEDIUM | Name spelling variations |
| `property_conflict` | HIGH | Square footage discrepancies |
| `date_sequence` | HIGH | Amendment dated before lease |
| `calculation_error` | MEDIUM | Math doesn't match stated total |

### Memory Architecture

```python
class DocumentMemory:
    leases: dict[str, Lease]           # lease_id → Lease
    amendments: dict[str, Amendment]    # amend_id → Amendment
    relationships: dict[str, list]      # lease_id → [amendment_ids]
```

### Conflict Detection Tools

```python
tools = [
    "compare_dates",         # Check date consistency
    "compare_rent",          # Verify rent amounts
    "compare_parties",       # Check party names match
    "compare_property",      # Verify property details
    "check_superseded",      # Ensure proper supersession
    "validate_calculations"  # Check financial math
]
```

### Output Schema

```python
class Conflict:
    conflict_id: str
    category: ConflictCategory
    severity: ConflictSeverity
    field_name: str
    description: str
    evidence: ConflictEvidence
    suggested_resolutions: list[SuggestedResolution]
```

---

## Agent Orchestration

### Pipeline Sequence

```
1. Load Document
       ↓
2. Document Classifier
   → Returns: DocumentType
       ↓
3. Lease Extractor (based on type)
   → Returns: Lease or Amendment
       ↓
4. Add to Memory
       ↓
5. Conflict Detector (when analyzing related docs)
   → Returns: ConflictReport
```

### Error Handling

| Scenario | Behavior |
|----------|----------|
| Classification fails | Return `DocumentType.UNKNOWN`, flag for review |
| Extraction fails | Return empty result with error message |
| Conflict detection fails | Log error, continue with partial results |

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Classification time | < 5 seconds |
| Extraction time | < 30 seconds |
| Conflict detection | < 10 seconds per document pair |
| Accuracy (classification) | > 95% |
| Accuracy (extraction) | > 90% for critical fields |

---

## Future Enhancements

- [ ] Custom extraction prompts per document format
- [ ] Field-level confidence scoring
- [ ] Async batch processing
- [ ] Fine-tuned classification model
- [ ] Active learning from corrections
