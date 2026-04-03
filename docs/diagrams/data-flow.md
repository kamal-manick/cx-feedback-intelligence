# Data Flow Diagram

Shows how data transforms as it moves through each pipeline stage.

```mermaid
graph TD
    subgraph "Stage 1: Extraction"
        A1["Survey Platform API"] -->|"JSON"| A2["Raw JSON Files<br/>~10K records/file"]
    end

    A2 -->|"Load & merge"| B1

    subgraph "Stage 2: Ingestion"
        B1["Consolidated DataFrame<br/>~35K rows"] -->|"Filter blanks"| B2["Comments DataFrame<br/>~20K rows"]
        B2 -->|"Clean & normalize"| B3["Cleaned DataFrame"]
    end

    B3 -->|"spaCy custom boundaries"| C1

    subgraph "Stage 3-6: NLP Pipeline"
        C1["Atomic Statements<br/>~34K rows"] -->|"VADER + custom lexicon"| D1["+ sentiscore, sentcategory"]
        D1 -->|"spaCy Matcher"| E1["+ topic set"]
        E1 -->|"NPS score x sentiment"| F1["+ directional labels"]
    end

    F1 -->|"Aggregate to response level"| G1

    subgraph "Stage 7: Export"
        G1["Final DataFrame<br/>~35K rows + topics"] -->|"Write"| G2["Excel Export<br/>2 sheets"]
    end

    style A1 fill:#fff3e0
    style G2 fill:#e8f5e9
    style C1 fill:#e1f5fe
    style D1 fill:#e1f5fe
    style E1 fill:#e1f5fe
    style F1 fill:#e1f5fe
```

## Row Count Transformation

This diagram illustrates how the dataset size changes through the pipeline:

```mermaid
graph TD
    R1["Raw Responses<br/>~35,000 rows"] -->|"Filter for comments"| R2["Responses with Comments<br/>~20,000 rows"]
    R2 -->|"Sentence splitting<br/>(~1.7x expansion)"| R3["Atomic Statements<br/>~34,000 rows"]
    R3 -->|"Topic matching<br/>(drop unmatched)"| R4["Matched Statements<br/>~28,000 rows"]
    R4 -->|"Aggregate by response"| R5["Labeled Responses<br/>~18,000 rows with topics"]
    R5 -->|"Rejoin full dataset"| R6["Final Export<br/>~35,000 rows<br/>(~18K with topics, ~17K without)"]

    style R1 fill:#e1f5fe
    style R3 fill:#fff3e0
    style R6 fill:#e8f5e9
```

## Data Schema at Each Stage

### After Ingestion (Stage 2)
| Column | Type | Description |
|---|---|---|
| survey_date | datetime | Response timestamp |
| response_id | string | Unique response identifier |
| nps_score | int | NPS rating (0-10) |
| comment | string | Free-text feedback |
| nps_category | string | Promoter / Passive / Detractor |
| region | string | Geographic region |
| segment | string | Market segment |
| ... | ... | Additional demographic dimensions |

### After Sentence Splitting (Stage 3)
| Column | Type | Description |
|---|---|---|
| *(all above)* | | |
| statement_seq | int | Statement sequence within response |
| statement_text | string | Individual atomic statement |

### After Sentiment Analysis (Stage 4)
| Column | Type | Description |
|---|---|---|
| *(all above)* | | |
| sentiment_score | float | Enhanced polarity score [-1, +1] |
| sentiment_category | string | Very Negative / Negative / Mixed / Positive / Very Positive |

### After Topic-Sentiment Mapping (Stage 6)
| Column | Type | Description |
|---|---|---|
| *(all above)* | | |
| topics | set[str] | Matched categories (e.g., {"product", "support"}) |
| directional_topics | set[str] | Labeled topics (e.g., {"product is good", "support is bad"}) |
