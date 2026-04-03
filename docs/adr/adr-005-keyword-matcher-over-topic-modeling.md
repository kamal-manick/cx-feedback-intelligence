# ADR-005: Keyword Matcher Over Statistical Topic Modeling

## Status
Accepted

## Context
The pipeline needs to categorize each atomic statement into one or more strategic topic areas (product, engagement, support, pricing, etc.) so that leadership can map customer feedback to specific organizational initiatives.

Two broad approaches were evaluated:

**Statistical topic modeling** (LDA, NMF, or BERTopic): Automatically discovers topic clusters from the corpus. Requires no manual taxonomy. Produces probabilistic topic assignments.

**Keyword-based matching** (spaCy Matcher): Uses a manually curated taxonomy of keywords mapped to predefined categories. Deterministic. Requires ongoing maintenance of the keyword list.

## Decision
Use spaCy's `Matcher` with a hybrid pattern strategy:

1. **Single-word keywords** are matched using both exact text (`LOWER`) and lemma form (`LEMMA`), catching inflections automatically (e.g., "implementing" -> "implement" -> product category)
2. **Multi-word phrases** are matched using exact token sequences (e.g., "ease of use" -> product category)
3. **Named entity patterns** use spaCy's NER to detect person names (`ENT_TYPE: PERSON`) and map them to the engagement category (customers mentioning their account representative)

The keyword taxonomy (~280 entries) maps to ~10 categories aligned with organizational strategic initiatives.

## Consequences

### What becomes easier
- **Deterministic and explainable:** Every categorization can be traced to a specific keyword match. When leadership asks "why is this labeled 'support'?", the answer is concrete: "because the word 'ticket' appeared in the statement"
- **Aligned with business language:** Categories map directly to strategic initiatives - no post-hoc interpretation of abstract topic clusters required
- **Incremental improvement:** Adding a missed keyword is a one-line CSV change, not a model retrain
- **No training data required:** The matcher works from day one with a manually curated list

### What becomes harder
- **Maintenance overhead:** New terms, jargon, and product names require manual addition to the taxonomy
- **Coverage gaps:** Unknown terms or novel phrasing won't match any pattern - the system fails silently (returns no topic rather than a wrong topic)
- **Recall limitations:** The system only finds what it's been told to look for, unlike statistical models which can surface unexpected patterns

### What was rejected
**LDA** produced topics like [license, cost, pricing, model, expensive] - semantically coherent but not actionable. The cluster needed human interpretation to map it to "pricing initiative." With 9 strategic initiatives, we needed exact mapping, not approximate clustering.

**BERTopic** produced better clusters but required GPU compute, had non-deterministic output across runs, and still required manual mapping from clusters to business categories. The added complexity wasn't justified when the keyword matcher achieved the same end result with full determinism.

### Trade-off accepted
Manual taxonomy curation is a real cost, but it's front-loaded (most terms were identified in the first pass) and incremental maintenance is low-effort. The determinism and explainability benefits are critical for stakeholder trust - leadership needs to understand and verify the categorization logic, which is only possible with an explicit, auditable taxonomy.
