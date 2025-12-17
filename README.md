# 🏢 Lease Digitizer

> **A Production-Grade LangChain Multi-Agent System for Commercial Real Estate Lease Intelligence**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)](https://python.langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Overview

**Lease Digitizer** is a sophisticated document intelligence pipeline that transforms unstructured commercial real estate leases into structured, actionable data. Built with LangChain's multi-agent architecture, it demonstrates production-grade patterns for enterprise document processing.

### 🎯 Key Features

- **Intelligent Document Classification** - Automatically identifies base leases vs. amendments using ReAct reasoning
- **Structured Data Extraction** - Extracts 50+ lease data points with Pydantic validation
- **Conflict Detection** - Identifies contradictions between base leases and amendments
- **Interactive Dashboard** - Streamlit-powered visualization of abstracted data and alerts

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Lease Digitizer                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  Document   │    │    Lease    │    │      Conflict       │ │
│  │ Classifier  │───▶│  Extractor  │───▶│      Detector       │ │
│  │   (ReAct)   │    │ (LLMChain)  │    │  (Agent + Memory)   │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│         │                  │                      │             │
│         ▼                  ▼                      ▼             │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   Streamlit Dashboard                       ││
│  │         Abstracted Data • Conflict Alerts • Analytics       ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Agent Descriptions

| Agent | Type | Purpose |
|-------|------|---------|
| **Document Classifier** | ReAct Agent | Classifies documents as base leases, amendments, or other document types using reasoning and action patterns |
| **Lease Extractor** | LLMChain + Pydantic | Extracts structured lease data including parties, terms, financials, and clauses with strict validation |
| **Conflict Detector** | Agent with Memory | Maintains context across documents to identify contradictions and inconsistencies |

## 📁 Project Structure

```
lease-digitizer/
├── src/
│   ├── agents/                 # LangChain agent implementations
│   │   ├── document_classifier.py
│   │   ├── lease_extractor.py
│   │   └── conflict_detector.py
│   ├── schemas/                # Pydantic models for data validation
│   │   ├── lease.py
│   │   ├── amendment.py
│   │   └── conflict.py
│   ├── tools/                  # Custom LangChain tools
│   │   ├── pdf_parser.py
│   │   ├── date_normalizer.py
│   │   └── financial_calculator.py
│   ├── utils/                  # Utility functions
│   │   ├── document_loader.py
│   │   └── text_processing.py
│   ├── config/                 # Configuration management
│   │   └── settings.py
│   └── dashboard/              # Streamlit application
│       └── app.py
├── tests/                      # Comprehensive test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── examples/                   # Sample data and demos
│   └── sample_leases/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- (Optional) LangSmith API key for tracing

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/lease-digitizer.git
cd lease-digitizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application

```bash
# Start the Streamlit dashboard
streamlit run src/dashboard/app.py

# Or process documents via CLI
python -m src.main --input examples/sample_leases/
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

## 📊 Extracted Data Points

The Lease Extractor captures comprehensive lease information:

| Category | Data Points |
|----------|-------------|
| **Parties** | Landlord, Tenant, Guarantors |
| **Property** | Address, Square Footage, Use Type |
| **Term** | Commencement, Expiration, Options |
| **Financial** | Base Rent, Escalations, CAM, Security Deposit |
| **Clauses** | Termination, Assignment, Subletting |

## 🔧 Configuration

Key configuration options in `.env`:

```bash
OPENAI_MODEL=gpt-4-turbo-preview  # LLM model selection
LOG_LEVEL=INFO                     # Logging verbosity
LANGCHAIN_TRACING_V2=true         # Enable LangSmith tracing
```

## 🛣️ Roadmap

- [ ] Support for additional document formats (DOCX, scanned PDFs)
- [ ] Multi-tenant architecture for enterprise deployment
- [ ] REST API for integration with existing systems
- [ ] Advanced analytics and reporting
- [ ] Support for additional LLM providers

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting PRs.

---

<p align="center">
  <strong>Built with ❤️ using LangChain</strong>
</p>
