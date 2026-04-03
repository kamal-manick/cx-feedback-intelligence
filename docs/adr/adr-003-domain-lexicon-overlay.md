# ADR-003: Domain-Specific Lexicon Overlay

## Status
Accepted

## Context
VADER ships with a general-purpose lexicon of ~7,500 words with human-rated sentiment scores. This works well for social media and product reviews but fails for enterprise software feedback because:

1. **Domain-neutral words carry strong domain sentiment.** "Licensing" is neutral in everyday language but strongly negative in enterprise software feedback (customers rarely mention licensing when they're happy about it). "Flexible" is mildly positive generally but strongly positive in platform evaluation ("the platform is flexible" is high praise).

2. **Intensity miscalibration.** VADER rates "good" at +1.9 and "great" at +3.1 on its internal scale. In NPS feedback, "good" often appears in luke-warm context ("it's good enough") while "great" signals genuine enthusiasm. The default spread didn't match the domain.

3. **Missing words.** Terms like "OOB" (out-of-the-box), "ITSM", and product-specific abbreviations are absent from VADER's lexicon entirely.

## Decision
Build a custom lexicon overlay (~70 terms) that is loaded at pipeline initialization and merged into VADER's lexicon via `sia.lexicon.update()`. The overlay:

- **Overrides** existing VADER scores for domain-significant words (e.g., "licensing": -3.4, "flexible": +2.5)
- **Adds** missing domain-specific terms with calibrated scores
- **Handles special cases:** The word "no" is removed from VADER's lexicon and added to VADER's negation list instead (`sia.constants.NEGATE`), because "no" in NPS feedback functions as a negation modifier rather than a standalone negative word

The lexicon is maintained as a simple CSV file (word, score) that can be updated without code changes.

## Consequences

### What becomes easier
- Sentiment accuracy improves substantially for domain-specific vocabulary
- The lexicon is human-readable and auditable - when a categorization is wrong, the team can trace it to a specific word-score pair and adjust
- New terms can be added by appending to the CSV, with no code deployment required

### What becomes harder
- The lexicon requires periodic maintenance as customer language evolves
- Score calibration is subjective - different reviewers might assign different scores to the same word
- The overlay is tightly coupled to the specific domain - it cannot be reused for a different survey context without recalibration

### Trade-off accepted
The maintenance overhead of ~70 terms is minimal compared to the accuracy gain. The lexicon was calibrated against a manually reviewed sample of 200 responses and achieved ~85% agreement with human reviewers - a significant improvement over vanilla VADER (~65% agreement on the same sample). The subjective nature of score assignment is mitigated by documenting the rationale for each override.
