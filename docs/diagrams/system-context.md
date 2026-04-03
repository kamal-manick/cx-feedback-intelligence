# System Context Diagram

Shows the CX Feedback Intelligence system in relation to its external actors and systems.

```mermaid
graph TB
    subgraph External Systems
        SurveyPlatform["Survey Platform<br/>(NPS Survey Tool)"]
        BIDashboard["BI Dashboard<br/>(Power BI)"]
    end

    subgraph Users
        DataEngineer["Data Engineer"]
        Leadership["Senior Leadership"]
        CXAnalyst["CX Analyst"]
    end

    subgraph "CX Feedback Intelligence"
        Pipeline["NLP Analysis Pipeline"]
    end

    SurveyPlatform -->|"Raw survey responses<br/>(JSON via API)"| Pipeline
    DataEngineer -->|"Configures extraction<br/>Maintains lexicons<br/>Monitors pipeline"| Pipeline
    Pipeline -->|"Structured categorized<br/>feedback (Excel/CSV)"| BIDashboard
    BIDashboard -->|"Visualized insights<br/>Topic trends<br/>Sentiment breakdown"| Leadership
    BIDashboard -->|"Drill-down analysis<br/>Response-level detail"| CXAnalyst

    style Pipeline fill:#e1f5fe,stroke:#0288d1
    style SurveyPlatform fill:#fff3e0,stroke:#f57c00
    style BIDashboard fill:#e8f5e9,stroke:#388e3c
```

## Key Interactions

| From | To | Data | Frequency |
|---|---|---|---|
| Survey Platform | Pipeline | Raw NPS responses (JSON) | Batch per year/quarter |
| Pipeline | BI Dashboard | Categorized feedback (Excel) | After each pipeline run |
| Data Engineer | Pipeline | Lexicon updates, extraction config | As needed |
| BI Dashboard | Leadership | Aggregated insights, trends | On-demand |
| BI Dashboard | CX Analyst | Response-level drill-downs | On-demand |
