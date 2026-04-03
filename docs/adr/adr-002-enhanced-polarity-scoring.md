# ADR-002: Enhanced Polarity Scoring

## Status
Accepted

## Context
VADER's default `compound` score is a normalized weighted composite of positive, negative, and neutral components. It ranges from -1 to +1 and is designed for balanced sentiment classification. However, for NPS analysis the business objective is asymmetric: **identifying pain points is more valuable than confirming strengths**.

During validation against manually reviewed samples, we found that VADER's compound score frequently softened clearly negative feedback:

- *"The licensing model is confusing and expensive"* -> compound: -0.25 (mild negative)
- *"Support response times are unacceptable"* -> compound: -0.34 (mild negative)

Both of these would be categorized as "Mixed" or "Mildly Negative" under standard thresholds, but both represent clear, actionable pain points that leadership needs to see.

## Decision
Replace VADER's `compound` score with a custom `enhanced_score()` function that uses the individual polarity components (`pos`, `neg`, `neu`) with asymmetric logic:

1. **If `neg == 0.0`** -> return `+1` (purely positive signal, no hedging)
2. **If `pos == 0.0`** -> return `-1` (purely negative signal, amplified)
3. **If `pos > neg`** -> return `pos + neu` (positive-leaning, retain magnitude)
4. **If `neg > pos`** -> return `-(neg + neu)` (negative-leaning, amplified by including neutral weight)
5. **Otherwise** -> fall back to `compound` (tied signals use default behavior)

The key insight is in rules 2 and 4: when negative signal is present, the neutral component is added to the negative magnitude rather than diluting it. This reflects the observation that in NPS feedback, neutral words surrounding a negative term are context - not counterbalance.

## Consequences

### What becomes easier
- Negative feedback is reliably categorized as "Very Negative" or "Negative" rather than being softened into "Mixed"
- The sentiment categories become more decisive, reducing the "Mixed" bucket (which was uninformative for leadership)
- Pain point identification becomes more reliable, directly serving the business objective

### What becomes harder
- The scoring is no longer symmetric - positive and negative feedback are not treated equivalently
- Mild criticism might be amplified into "Very Negative" when the intent was more moderate
- The enhanced score is not directly comparable to standard VADER scores in academic or cross-system contexts

### Trade-off accepted
This is a deliberate product decision encoded as a scoring function. The NPS improvement program's primary goal is to find and fix pain points, not to produce balanced sentiment distributions. Over-indexing on negativity means leadership sees every potential issue, even at the cost of some false amplification. A comment incorrectly flagged as "Very Negative" gets reviewed and reclassified; a comment incorrectly softened to "Mixed" gets lost in the noise.
