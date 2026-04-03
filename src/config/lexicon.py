"""
Custom Sentiment Lexicon Configuration

Defines domain-specific word-score overrides for the VADER sentiment analyzer.
These overrides adjust scores for words that carry different connotation in
enterprise customer feedback compared to general English.

In the production system, this lexicon contains ~70 calibrated entries. The
example below demonstrates the structure, rationale, and calibration approach
with a representative subset.

Calibration approach:
- Scores were calibrated against a manually reviewed sample of ~200 responses
- Positive domain terms are scored +2.5 to +3.5 (strong positive signal)
- Negative domain terms are scored -2.5 to -3.5 (strong negative signal)
- Neutral domain terms that carry implicit sentiment are scored ±0.7
- VADER's default scale is roughly -4 to +4

See ADR-003 for the full rationale behind domain lexicon tuning.
"""

# Format: {word: sentiment_score}
# Positive scores indicate positive sentiment, negative scores indicate negative.
CUSTOM_LEXICON: dict[str, float] = {
    # Enterprise platform terms - positive in evaluation context
    "platform": 2.0,
    "product": 2.0,
    "flexibility": 2.5,
    "flexible": 2.5,
    "powerful": 2.5,
    "robust": 3.5,
    "scalable": 2.5,
    "reliable": 2.5,
    "stable": 3.5,
    "comprehensive": 3.5,
    "innovation": 3.5,
    "customization": 2.5,
    "efficient": 3.5,

    # Positive feedback amplifiers
    "great": 3.5,
    "recommend": 3.5,
    "solid": 3.5,
    "fantastic": 3.5,
    "outstanding": 3.5,
    "amazing": 3.5,
    "awesome": 3.5,
    "helpful": 3.5,
    "responsive": 3.5,
    "satisfied": 3.5,

    # Negative domain terms - carry strong negative connotation in CX context
    "licensing": -3.4,
    "expensive": -3.4,
    "pricing": -3.4,
    "license": -3.4,
    "cost": -2.5,
    "costs": -3.5,
    "complex": -3.5,
    "difficult": -2.5,
    "issues": -2.5,
    "issue": -3.5,
    "problems": -2.5,
    "problem": -2.5,
    "lack": -2.5,
    "hard": -2.5,
    "confusing": -2.5,

    # Contextual modifiers - carry mild sentiment as modifiers
    "very": 0.7,
    "customer": 0.7,
    "needs": 0.7,
    "functionality": 0.7,
    "capabilities": 0.7,
    "capability": 0.7,
    "extremely": 0.7,

    # Words that need special handling
    # "better" and "improve" are positive in general English but often appear
    # in NPS feedback as "needs to be better" or "should improve" - scored
    # mildly negative to reflect the complaint context
    "better": -1.5,
    "improve": -2.5,
    "improvement": -1.5,
    "improvements": -2.5,
}

# Words that should be treated as negation modifiers rather than standalone
# sentiment carriers. VADER's default lexicon scores "no" as negative, but
# in NPS feedback "no" functions as a negation prefix: "no issues" should
# negate "issues", not add independent negative weight.
NEGATION_OVERRIDES: list[str] = ["no"]
