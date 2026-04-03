# ADR-006: Typo, Abbreviation, and Misspelling Handling via Lexicon Mapping

## Status
Accepted

## Context
Customer survey feedback is written quickly, often on mobile devices, and is rarely proofread. The corpus contains a high volume of:

- **Typos:** "flexability" (flexibility), "Licensce" (licence), "reliablity" (reliability), "complicate" (complicated)
- **Misspellings:** "Featrures" (features), "plattform" (platform), "profuct" (product), "customisation" (customization)
- **Abbreviations:** "OOB" (out-of-the-box), "PS" (professional services), "TCO" (total cost of ownership), "ROI" (return on investment)
- **Informal shorthand:** "UI/UX", "ITSM", abbreviations of product or platform names

The keyword-based topic matcher (ADR-005) relies on exact text or lemma matches. A misspelled word like "flexability" has no lemma in spaCy's vocabulary and won't match "flexibility" - meaning the entire statement is silently dropped from topic categorization.

The question: how do we handle these variants without introducing a spell-correction preprocessing step?

## Decision
Map known typos, misspellings, and abbreviations directly into the keyword taxonomy. The keyword CSV includes entries like:

```
flexability -> product
flexi -> product
Flexibel -> product
Licensce -> licensing
lisence -> licensing
reliablity -> product
profuct -> product
customisation -> product
OOB -> product
TCO -> price
```

Each variant is mapped to the same category as its canonical form. The spaCy Matcher treats them as regular keywords - no special handling required. The `LOWER` match mode handles case variations automatically.

This approach was chosen over automated spell-correction (e.g., `pyspellchecker`, `TextBlob.correct()`) because:

1. **Spell-correction introduces false corrections.** "SN" would be "corrected" to "in" or "an". "OOB" would be flagged as an error. Domain-specific abbreviations and product names are not in standard dictionaries.
2. **Spell-correction is non-deterministic.** Different libraries may correct the same word differently, making results harder to reproduce and audit.
3. **The keyword lexicon approach is fully auditable.** Every variant-to-category mapping is explicit and reviewable.

## Consequences

### What becomes easier
- Topic extraction succeeds on malformed input without a separate preprocessing step
- Each mapping is explicit, auditable, and reversible - adding or removing a variant is a one-line CSV change
- No additional library dependency or processing time for spell-correction
- Zero risk of false corrections mangling domain-specific terms

### What becomes harder
- **Manual maintenance is required.** New typos discovered in the data must be manually added to the keyword list
- **Coverage is reactive, not proactive.** Only known variants are handled - novel misspellings of existing keywords won't match until they're added
- **The keyword list grows over time** with variant entries that are not semantically meaningful, making it harder to audit the canonical taxonomy
- **This approach does not scale** to very large corpora where the variety of misspellings would be effectively unbounded

### Trade-off accepted
At the current corpus scale (~280 keywords including variants), the manual maintenance is manageable. The initial keyword list was built by analyzing the actual frequency of misspellings in the corpus - the most common variants were added first, covering ~95% of cases. Rare one-off typos that don't match are silently dropped (no topic assigned), which is an acceptable failure mode.

The long-term plan is to replace this approach with fuzzy matching or embedding-based similarity (see Future Roadmap in README) that can automatically resolve unseen variants to their canonical keywords.
