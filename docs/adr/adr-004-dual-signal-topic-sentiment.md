# ADR-004: Dual-Signal Topic-Sentiment Mapping

## Status
Accepted

## Context
After topic extraction and sentiment scoring, each atomic statement has:
1. A set of matched topic categories (e.g., {"product", "licensing"})
2. A text-based sentiment category (e.g., "Very Negative")
3. The original NPS numeric score (0-10) from the survey response

The question: how do we combine these into a directional label like "product is good" or "licensing is bad"?

Using text sentiment alone is unreliable because:
- A promoter (score 9) saying "the product could be improved" has mild negative text sentiment but is actually providing constructive feedback from a position of overall satisfaction
- A detractor (score 3) saying "the support team tried their best" has positive text sentiment but the overall relationship is negative

Using the NPS score alone is too coarse:
- A score of 9 applied uniformly would label everything as "good", missing the specific complaints that even promoters raise

We needed a cross-referencing approach that uses both signals.

## Decision
Implement a mapping function that cross-references the NPS score band with the per-statement text sentiment to produce directional topic labels:

**Promoters (score > 7):**
- Default: `"{topic} is good"`
- Exception: If text sentiment is "Very Negative" -> `"{topic} is bad"`
- Rationale: Promoters are generally positive, but when they express strong negativity about a specific topic, that's a high-value signal worth surfacing

**Passives (score 5-7):**
- Default: `"{topic} is bad"`
- Exception: If text sentiment is "Very Positive" -> `"{topic} is good"`
- Rationale: Passives are at-risk customers. Their feedback defaults to "needs improvement" unless they express strong positivity about a specific area

**Detractors (score < 5):**
- Always: `"{topic} is bad"`
- Rationale: Detractors have fundamental dissatisfaction. Even positive text fragments in a detractor response are not reliable indicators of satisfaction

**Special cases:**
- "high-price" keyword matches always map to "price is bad" regardless of score or sentiment
- Named entity (PERSON) matches are remapped to "engagement" category
- Lone "company" topic retains its own directional label

## Consequences

### What becomes easier
- Directional labels are immediately actionable - leadership can see "licensing is bad (47 mentions)" and route it to the right initiative
- The mapping logic is explicit and auditable - every label can be traced back to a specific NPS score + sentiment combination
- Edge cases (promoters with complaints, detractors with praise) are handled with clear, documented rules

### What becomes harder
- The score thresholds (7, 5) and sentiment override rules are judgment calls that encode business assumptions
- Passives default to "bad" which may over-count negative signals from this segment
- The mapping doesn't handle gradients - a topic is binary "good" or "bad" with no middle ground

### Trade-off accepted
Binary directional labels (good/bad) sacrifice nuance for actionability. Leadership dashboards need clear signals, not probability distributions. The specific thresholds were calibrated against stakeholder expectations: "if a promoter says something very negative about licensing, we want to see it." The rules are documented and adjustable without code changes.
