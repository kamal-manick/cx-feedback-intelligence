# Architecture

## System Design Narrative

CX Feedback Intelligence is a batch-processing NLP pipeline that transforms raw NPS survey responses into structured, actionable insight data. The system was designed for a specific business constraint: leadership needed to understand *what customers are talking about* and *whether it's good or bad*, mapped to the organization's strategic initiative categories - not just aggregate NPS scores.

The architecture follows a staged pipeline pattern where each stage has a single responsibility, takes a well-defined input, and produces a well-defined output. This was a deliberate choice over a monolithic notebook approach - while the initial prototyping happened in Jupyter notebooks, the production design separates concerns so that individual stages can be tested, tuned, and replaced independently.

---

## Data Flow Walkthrough

### Stage 1: Data Extraction

**Input:** Survey platform API credentials + date range parameters
**Output:** Raw JSON files (one per year/batch)

Survey responses are extracted from the survey platform's reporting API. The extraction pulls all responses for a given time period, including the NPS numeric score (0-10), free-text comment, and embedded metadata (account information, geographic segmentation, organizational hierarchy).

The extraction layer handles pagination (API returns max 10,000 records per request) and writes raw JSON to disk as an intermediate artifact. This decouples extraction from processing - if the NLP pipeline needs to be re-run, the raw data doesn't need to be re-fetched.

### Stage 2: Data Ingestion & Consolidation

**Input:** Multiple raw JSON files across years
**Output:** Single consolidated, cleaned DataFrame

Multiple years of survey data are merged into a single dataset. This stage handles:

- **Schema normalization:** The survey platform uses internal field identifiers that change between API versions. This stage maps them to stable, human-readable column names.
- **Array-to-text conversion:** Some fields arrive as JSON arrays (e.g., multi-select topics). These are flattened to comma-separated strings.
- **Date parsing and sorting:** Ensures chronological ordering for time-series analysis.
- **Blank and null filtering:** Removes responses with no comment text (numeric-only responses are retained in the full dataset but excluded from NLP processing).
- **HTML entity decoding:** Survey responses sometimes contain HTML-encoded characters (`&amp;` -> `&`) from the survey platform's text processing.

### Stage 3: Sentence Segmentation

**Input:** Cleaned DataFrame with one row per survey response
**Output:** Expanded DataFrame with one row per atomic statement

This is the most architecturally significant transformation in the pipeline. A single survey response often contains multiple distinct feedback points:

> *"The platform is excellent for automation; however, the licensing model is confusing and support response times need improvement."*

Default NLP sentence parsers would treat this as one or two sentences, but it contains three distinct feedback signals (positive-product, negative-licensing, negative-support). The custom sentence boundary detector:

1. Loads the spaCy `en_core_web_lg` model
2. Injects a custom pipeline component (`set_custom_boundaries`) that marks sentence starts on:
   - Semicolons and commas (when not preceded by conjunctions)
   - Conjunctions like "however" and "but"
3. Further splits on newline characters (survey responses often contain line breaks)
4. Filters out salutation lines ("Thanks!", "Regards,") that carry no feedback signal
5. Assigns each fragment a sequence number within the original response

The result is a ~1.7x expansion of the dataset (20,000 responses -> ~34,000 atomic statements), where each row can receive independent sentiment and topic analysis.

### Stage 4: Sentiment Analysis

**Input:** DataFrame with atomic statements
**Output:** Same DataFrame with sentiment score and category columns added

Each atomic statement is scored using NLTK's VADER sentiment analyzer, augmented with two customizations:

**Custom Lexicon Overlay:**
VADER's built-in lexicon treats domain-specific words as neutral. The pipeline loads a custom lexicon (~70 terms) that overrides scores for words with strong domain-specific connotation. For example, "licensing" is neutral in general English but strongly negative in enterprise software feedback. "Flexible" is mildly positive generally but strongly positive in a platform evaluation context.

**Enhanced Polarity Scoring:**
VADER returns four scores: `neg`, `neu`, `pos`, and `compound`. The default `compound` score is a normalized weighted composite that tends to soften extreme signals. The custom `enhanced_score()` function replaces it with asymmetric logic:

- If `neg == 0.0` -> return `+1` (purely positive)
- If `pos == 0.0` -> return `-1` (purely negative)
- If `pos > neg` -> return `pos + neu` (positive-leaning)
- If `neg > pos` -> return `-(neg + neu)` (negative-leaning, amplified)
- Otherwise -> fall back to `compound`

This produces more decisive categorization, particularly for negative feedback which the business most needs to identify.

**Sentiment Categories:**
The continuous score is then bucketed into categories: Very Positive (>= 0.6), Positive (0.2-0.6), Mixed (-0.2-0.2), Negative (-0.6--0.2), Very Negative (< -0.6). The thresholds were calibrated against manually reviewed samples.

### Stage 5: Topic Categorization

**Input:** Scored atomic statements
**Output:** Same DataFrame with matched topic set added

Each statement is analyzed using spaCy's `Matcher` to identify which strategic category it relates to. The matcher is built from a keyword taxonomy (~280 entries) that maps terms to categories:

**Pattern Types:**
- **Single-word keywords** match on both exact text and lemma form (catching inflections: "implementing" -> "implement" -> product category)
- **Multi-word phrases** match on exact token sequences ("ease of use" -> product category)
- **Named entity patterns** detect person names (via spaCy NER `PERSON` entity type) and map them to the engagement category (customers mentioning their account representative)

**Typo and Variant Handling:**
The keyword lexicon includes known misspellings, typos, and abbreviations that appear frequently in customer feedback. For example, "flexability", "Licensce", "reliablity" are all mapped to their correct categories. This ensures topic extraction succeeds on malformed input without requiring a spell-correction preprocessing step (which can introduce its own errors).

**Categories** include: product, engagement, support, pricing, licensing, monetization, transparency, and value - each mapping to a specific organizational strategic initiative.

### Stage 6: Topic-Sentiment Mapping

**Input:** Statements with sentiment scores and topic sets
**Output:** Directional topic labels (e.g., "product is good", "pricing is bad")

This is the core analytical innovation. A topic alone ("pricing") is not actionable. Leadership needs to know whether pricing is a *strength* or a *pain point*. The mapper cross-references two signals:

1. **The NPS numeric score** (from the original survey response)
2. **The text sentiment category** (from the per-statement sentiment analysis)

The mapping logic:
- **Promoters (score > 7):** Default to "is good". Override to "is bad" only if text sentiment is "Very Negative".
- **Passives (score 5-7):** Default to "is bad". Override to "is good" only if text sentiment is "Very Positive".
- **Detractors (score < 5):** Always "is bad" regardless of text sentiment.

Special handling:
- "high-price" keywords always map to "price is bad" regardless of score or sentiment
- Person-name matches (account-rep) are remapped to the "engagement" category
- If the only matched topic is "company" (generic), it retains its own directional label rather than being dropped

The output is a set of directional labels per statement: `{"product is good", "licensing is bad"}`.

### Stage 7: Aggregation and Export

**Input:** Directional topic labels per statement
**Output:** Aggregated topic sets per original response + structured Excel/CSV export

Topic sets from all statements belonging to the same original response are unioned together (a single response can have both "product is good" and "support is bad"). The aggregated data is joined back to the full dataset (including responses without comments) and exported as structured Excel with two sheets:

1. **Full dataset** - All responses with their aggregated topic sets
2. **Topics sheet** - Exploded topic labels for pivot table and dashboard consumption

### Stage 8: Visualization

**Input:** Structured Excel export
**Output:** Power BI dashboard

The BI dashboard consumes the export and provides:
- Sentiment distribution over time (by year, quarter, month)
- Topic frequency analysis (what customers talk about most)
- Directional topic breakdown (which areas are strengths vs. pain points)
- Geographic and segment drill-downs
- Individual response detail view with sentence-level sentiment highlighting

---

## Component Interface Contracts

### SurveyClient
```python
class SurveyClient(ABC):
    def extract(self, year: int) -> list[dict]:
        """Fetch all survey responses for a given year. Returns list of raw records."""

    def extract_range(self, start_date: date, end_date: date) -> list[dict]:
        """Fetch survey responses within a date range."""
```

### DataConsolidator
```python
class DataConsolidator:
    def consolidate(self, raw_files: list[Path]) -> pd.DataFrame:
        """Merge multiple raw data files into a single normalized DataFrame."""

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove blanks, decode HTML entities, normalize column types."""
```

### SentenceSplitter
```python
class SentenceSplitter:
    def split(self, text: str) -> list[tuple[int, str]]:
        """Split a comment into (sequence_number, text) atomic statements."""
```

### SentimentAnalyzer
```python
class SentimentAnalyzer:
    def score(self, text: str) -> float:
        """Return enhanced polarity score for a single statement. Range: [-1, +1]."""

    def categorize(self, score: float) -> str:
        """Map a polarity score to a sentiment category label."""
```

### TopicCategorizer
```python
class TopicCategorizer:
    def extract_topics(self, text: str) -> set[str]:
        """Return set of matched category labels for a statement."""
```

### TopicSentimentMapper
```python
class TopicSentimentMapper:
    def map(self, topics: set[str], sentiment: str, nps_score: int) -> set[str]:
        """Produce directional labels by cross-referencing topics, sentiment, and NPS score."""
```

### DataExporter
```python
class DataExporter:
    def export(self, df: pd.DataFrame, topics_df: pd.DataFrame, output_path: Path) -> None:
        """Write structured output to Excel/CSV for BI consumption."""
```

---

## Scalability and Reliability Considerations

**Current scale:** ~35,000 responses/year -> ~34,000 atomic statements after sentence splitting. Processing completes in approximately 15-20 minutes on a single machine (bottleneck is spaCy NLP processing per statement).

**Scaling paths considered:**
- **spaCy `nlp.pipe()` batching:** Process statements in batches rather than individual `nlp()` calls. Would reduce overhead from model loading per call. Not implemented in production due to the DataFrame row-by-row pattern, but would be the first optimization.
- **Dask/multiprocessing:** The per-statement analysis is embarrassingly parallel. A Dask DataFrame or Python multiprocessing pool could distribute across cores. Not needed at current scale but the staged pipeline design makes this straightforward.
- **Incremental processing:** Currently processes the full historical dataset on each run. A future version could track a high-water mark and only process new responses, appending to the existing export.

**Reliability:**
- Raw JSON files are persisted as intermediate artifacts, decoupling extraction from processing.
- The pipeline is idempotent - re-running on the same input produces identical output.
- Export includes both the full dataset and the exploded topics view, allowing the BI layer to validate totals.

---

## Alternatives Considered and Rejected

### LDA / BERTopic for Topic Extraction
**Why considered:** Automated topic discovery without manual taxonomy curation.
**Why rejected:** Produced clusters that were semantically coherent but not aligned with organizational strategic initiatives. A cluster of [license, cost, pricing, model] is useful for a data scientist but not actionable for a VP asking "which initiative should I fund?" The keyword matcher's explicit taxonomy maps directly to organizational language.

### TextBlob for Sentiment Analysis
**Why considered:** Simpler API than VADER.
**Why rejected:** TextBlob's pattern-based approach performed worse on short, fragment-level text (which is what the pipeline produces after sentence splitting). VADER was specifically designed for social-media-style short text and responded better to the custom lexicon overlay.

### Spell-Correction Preprocessing (e.g., pyspellchecker)
**Why considered:** Normalizing typos before topic extraction.
**Why rejected:** Spell-correction introduces false corrections - "OOB" (a common abbreviation for out-of-the-box) would be "corrected" to a different word. Domain-specific abbreviations and product names are not in standard dictionaries. Mapping known variants directly in the keyword lexicon was more reliable, even though it requires manual maintenance.

### Transformer-Based Sentiment (e.g., RoBERTa fine-tuned)
**Why considered:** Higher accuracy than lexicon-based approaches.
**Why rejected:** In 2022, fine-tuning a transformer for this domain would have required labeled training data that didn't exist. VADER + custom lexicon achieved acceptable accuracy (~85% agreement with manual review) with zero training data and full interpretability. The trade-off favored speed-to-deployment and explainability.

### Monolithic Notebook Architecture
**Why considered:** Faster initial development.
**Why rejected for production:** A single notebook is difficult to test, version, and maintain. The staged pipeline design allows individual components to be swapped (e.g., replacing VADER with an LLM) without touching other stages. The prototype was built in notebooks; the production design separated concerns.
