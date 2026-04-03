# Component Interaction Diagram

Shows how internal components of the pipeline interact with each other.

```mermaid
graph TD
    subgraph "Configuration"
        Lexicon["Sentiment Lexicon<br/>(lexicon.py)"]
        Categories["Category Taxonomy<br/>(categories.py)"]
    end

    subgraph "Data Acquisition"
        Client["SurveyClient<br/>(survey_client.py)"]
        Consolidator["DataConsolidator<br/>(consolidator.py)"]
    end

    subgraph "NLP Processing"
        Splitter["SentenceSplitter<br/>(sentence_splitter.py)"]
        Sentiment["SentimentAnalyzer<br/>(sentiment_analyzer.py)"]
        Topics["TopicCategorizer<br/>(topic_categorizer.py)"]
        Mapper["TopicSentimentMapper<br/>(topic_sentiment_mapper.py)"]
    end

    subgraph "Output"
        Exporter["DataExporter<br/>(exporter.py)"]
    end

    Orchestrator["Pipeline Orchestrator<br/>(pipeline.py)"]

    Client -->|"Raw JSON records"| Consolidator
    Consolidator -->|"Cleaned DataFrame<br/>(1 row per response)"| Splitter
    Splitter -->|"Expanded DataFrame<br/>(1 row per statement)"| Sentiment
    Lexicon -.->|"Custom word scores"| Sentiment
    Sentiment -->|"Scored DataFrame<br/>(+ sentiscore, sentcategory)"| Topics
    Categories -.->|"Keyword patterns"| Topics
    Topics -->|"DataFrame with<br/>matched topic sets"| Mapper
    Mapper -->|"DataFrame with<br/>directional labels"| Exporter

    Orchestrator ====>|"Coordinates"| Client
    Orchestrator ====>|"Coordinates"| Consolidator
    Orchestrator ====>|"Coordinates"| Splitter
    Orchestrator ====>|"Coordinates"| Sentiment
    Orchestrator ====>|"Coordinates"| Topics
    Orchestrator ====>|"Coordinates"| Mapper
    Orchestrator ====>|"Coordinates"| Exporter

    style Orchestrator fill:#fff3e0,stroke:#f57c00
    style Splitter fill:#e1f5fe,stroke:#0288d1
    style Sentiment fill:#e1f5fe,stroke:#0288d1
    style Topics fill:#e1f5fe,stroke:#0288d1
    style Mapper fill:#e1f5fe,stroke:#0288d1
    style Lexicon fill:#fce4ec,stroke:#c62828
    style Categories fill:#fce4ec,stroke:#c62828
```

## Component Responsibilities

| Component | Input | Output | Key Dependency |
|---|---|---|---|
| SurveyClient | API credentials + date range | List of raw record dicts | Survey platform API |
| DataConsolidator | Raw JSON files | Cleaned, normalized DataFrame | pandas |
| SentenceSplitter | Comment text | List of (index, text) tuples | spaCy `en_core_web_lg` |
| SentimentAnalyzer | Statement text | Polarity score + category | NLTK VADER + custom lexicon |
| TopicCategorizer | Statement text | Set of matched categories | spaCy Matcher + keyword taxonomy |
| TopicSentimentMapper | Topics + sentiment + NPS score | Set of directional labels | Business rules |
| DataExporter | Labeled DataFrame | Excel/CSV files | openpyxl |
| Pipeline | Configuration | End-to-end execution | All components |
