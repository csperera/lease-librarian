# Lease Digitizer - Streamlit Dashboard Specification

## Overview

This document specifies the user interface design for the Lease Digitizer Streamlit dashboard.

---

## Page Structure

### Navigation

```
Sidebar:
├── 🏢 Lease Digitizer (Logo/Title)
├── ─────────────────
├── 📤 Upload Documents
├── 📊 Lease Dashboard  
├── ⚠️ Conflict Alerts
├── 📈 Analytics
├── ⚙️ Settings
├── ─────────────────
├── Quick Stats
│   ├── Documents: [count]
│   └── Conflicts: [count]
└── Processing Status
```

---

## Page Designs

### 1. Upload Documents Page

**Purpose:** Upload and process new lease documents

**Components:**

| Component | Type | Description |
|-----------|------|-------------|
| File Uploader | `st.file_uploader` | Multi-file PDF upload |
| File List | Expandable cards | Show selected files with size |
| Process Button | `st.button` | Trigger processing pipeline |
| Progress Bar | `st.progress` | Show processing status |
| Results Area | Container | Display classification results |

**User Flow:**
```
1. User selects PDF files
2. Files appear in list with metadata
3. User clicks "Process"
4. Progress bar shows status
5. Results display with classifications
```

---

### 2. Lease Dashboard Page

**Purpose:** View and manage extracted lease data

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Lease Dashboard                                           │
├─────────────────────────────────────────────────────────────┤
│ [Search Bar]                    [Filter: Type ▼] [Sort ▼]   │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐             │
│ │ Lease Card  │ │ Lease Card  │ │ Lease Card  │             │
│ │ Tenant Name │ │ Tenant Name │ │ Tenant Name │             │
│ │ Address     │ │ Address     │ │ Address     │             │
│ │ Rent: $X    │ │ Rent: $X    │ │ Rent: $X    │             │
│ │ [View]      │ │ [View]      │ │ [View]      │             │
│ └─────────────┘ └─────────────┘ └─────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

**Lease Card Fields:**
- Tenant name
- Property address (abbreviated)
- Monthly rent
- Term dates
- Amendment count badge
- Confidence indicator

**Detail Modal:**
- Full lease data in organized sections
- Party information
- Property details
- Financial terms
- Linked amendments
- Edit capability (TODO)

---

### 3. Conflict Alerts Page

**Purpose:** Review and resolve detected conflicts

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Conflict Alerts                                           │
├─────────────────────────────────────────────────────────────┤
│ [🔴 Critical] [🟡 High/Medium] [🟢 Resolved]                 │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🔴 CRITICAL: Rent Amount Mismatch                       │ │
│ │ ─────────────────────────────────────────────────────── │ │
│ │ Base Lease: $10,000/month                               │ │
│ │ Amendment 1: References $10,500 as "original rent"      │ │
│ │ ─────────────────────────────────────────────────────── │ │
│ │ Suggested Resolution: Use Amendment value (later date)  │ │
│ │ [Resolve] [Ignore] [Add Note]                           │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Conflict Card Elements:**
- Severity badge (color-coded)
- Conflict category label
- Source document excerpts
- Suggested resolution
- Action buttons

---

### 4. Analytics Page

**Purpose:** Portfolio-level insights and metrics

**Metrics Dashboard:**

| Metric | Visualization |
|--------|---------------|
| Total Documents | Big number |
| Processing Success Rate | Percentage + trend |
| Avg Confidence Score | Gauge chart |
| Document Types | Pie chart |
| Conflicts by Severity | Bar chart |
| Processing Time | Line chart (over time) |

**Portfolio Summary:**
- Total leases
- Total square footage
- Average rent PSF
- Lease expirations by year

---

### 5. Settings Page

**Purpose:** Configure application settings

**Sections:**

```
API Configuration
├── OpenAI API Key [password input]
├── Model Selection [dropdown]
└── [Save]

Processing Options
├── Confidence Threshold [slider: 0-1]
├── Enable LangSmith Tracing [checkbox]
└── [Save]

Export Settings
├── Default Format [dropdown: JSON/CSV/XLSX]
└── Include Raw Text [checkbox]
```

---

## Component Styling

### Color Scheme

| Element | Color | Usage |
|---------|-------|-------|
| Primary | `#1f77b4` | Buttons, links |
| Success | `#28a745` | Resolved, complete |
| Warning | `#ffc107` | Medium priority |
| Danger | `#dc3545` | Critical alerts |
| Info | `#17a2b8` | Informational |

### Status Indicators

```python
severity_colors = {
    "critical": "🔴",
    "high": "🟠", 
    "medium": "🟡",
    "low": "🟢",
    "info": "🔵"
}
```

---

## Session State

```python
st.session_state = {
    "processed_documents": [],    # List of processed docs
    "conflict_reports": [],       # Detected conflicts
    "processing_status": "idle",  # idle/processing/complete
    "selected_lease": None,       # Currently viewing
    "filter_type": "all",         # Document type filter
}
```

---

## Responsive Design

| Screen Size | Layout |
|-------------|--------|
| Desktop (>1200px) | 3-column card grid |
| Tablet (768-1200px) | 2-column card grid |
| Mobile (<768px) | Single column, stacked |

---

## Future Enhancements

- [ ] Document preview (PDF viewer)
- [ ] Batch export functionality
- [ ] Email alert integration
- [ ] User authentication
- [ ] Multi-tenant support
- [ ] Dark mode toggle
