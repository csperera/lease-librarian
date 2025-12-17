# Lease Digitizer API Specification

## Overview
FastAPI backend that exposes LangChain agents via REST endpoints.

## Base URL
`http://localhost:8000/api/v1`

## Endpoints

### 1. Extract Lease Data
**POST** `/extract`

Extract structured data from a lease document.

**Request Body:**
```json
{
  "document_text": "string (required) - Full lease text",
  "document_id": "string (optional) - Unique identifier"
}
```

**Response (200 OK):**
```json
{
  "document_id": "string",
  "lease": {
    "tenant": {"legal_name": "string", ...},
    "landlord": {"legal_name": "string", ...},
    "property_address": {...},
    "rentable_square_feet": "number",
    "base_rent_monthly": "number",
    "commencement_date": "YYYY-MM-DD",
    "expiration_date": "YYYY-MM-DD",
    ...
  },
  "metadata": {
    "confidence_score": "float (0-1)",
    "processing_time_seconds": "float",
    "extracted_fields": "integer",
    "missing_fields": ["string"]
  }
}
```

**Error Response (400/500):**
```json
{
  "error": "string",
  "detail": "string"
}
```

### 2. Health Check
**GET** `/health`

Check API status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## CORS
Enabled for `http://localhost:3000` (React dev server)

## Authentication
None (demo version)
