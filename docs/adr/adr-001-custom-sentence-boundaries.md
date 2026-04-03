# ADR-001: Custom Sentence Boundary Detection

## Status
Accepted

## Context
NPS survey comments frequently contain compound sentences with multiple distinct feedback signals. A single response like *"The platform is excellent for automation; however, the licensing model is confusing and support response times need improvement"* contains three separate opinions about three different topics (product, licensing, support), each with a different sentiment.

spaCy's default sentence parser treats this as one or two sentences, producing a blended sentiment score that masks the opposing signals. When we ran sentiment analysis at the full-sentence level, mixed-sentiment comments consistently scored near zero ("neutral") - which is technically correct as a mathematical average but completely useless for identifying specific pain points.

We needed per-clause granularity to produce meaningful topic-sentiment pairs.

## Decision
Inject a custom spaCy pipeline component (`set_custom_boundaries`) that marks additional sentence boundaries on:

1. **Semicolons and commas** - when not preceded by conjunctions (to avoid splitting "however, the product..." into "however" and "the product...")
2. **Conjunctions "however" and "but"** - these words almost always signal a sentiment reversal in NPS feedback
3. **Newline characters** - survey responses often use line breaks to separate distinct thoughts

The component is registered via `@Language.component` and inserted into the spaCy pipeline before the parser, so downstream processing (NER, dependency parsing) operates on the already-split segments.

Additionally, salutation lines ("Thanks!", "Regards,") are filtered out post-split as they carry no feedback signal.

## Consequences

### What becomes easier
- Each atomic statement receives independent sentiment and topic labels, dramatically improving categorization precision
- Mixed-sentiment responses are correctly decomposed rather than averaged into "neutral"
- The per-statement granularity enables more accurate topic-sentiment cross-referencing

### What becomes harder
- Dataset size increases ~1.7x (20,000 responses -> ~34,000 statements), increasing processing time proportionally
- Aggregation logic must union topic sets back to the original response level for the final export
- Some splits are overly aggressive - a comma in a list ("we use it for ticketing, automation, and workflows") creates unnecessary fragments. These are mostly harmless (short fragments often match no topics and are dropped) but add noise to intermediate data

### Trade-off accepted
The precision gain from per-clause analysis far outweighs the processing cost and occasional over-splitting. The ~1.7x row expansion is manageable at the current scale (35,000 responses) and the over-split fragments are naturally filtered out by the topic extraction stage (no keyword match -> no topic -> dropped from final output).
