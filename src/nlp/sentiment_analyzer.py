"""
Sentiment Analysis with Domain-Tuned Lexicon

Combines NLTK's VADER sentiment analyzer with a custom lexicon overlay and
an asymmetric polarity scoring function designed to amplify negative signals.

Two key customizations over vanilla VADER:

1. Custom Lexicon Overlay (ADR-003):
   Domain-specific words have their sentiment scores overridden. In enterprise
   software feedback, "licensing" is strongly negative and "flexible" is strongly
   positive - generic VADER treats both as near-neutral.

2. Enhanced Polarity Scoring (ADR-002):
   Replaces VADER's compound score with asymmetric logic that amplifies negative
   signals. The business objective is pain-point identification, so the scoring
   function deliberately over-indexes on negativity.

See ADR-002 and ADR-003 for full design rationale.
"""

from nltk.sentiment.vader import SentimentIntensityAnalyzer

from src.config.lexicon import CUSTOM_LEXICON, NEGATION_OVERRIDES


# Sentiment category thresholds - calibrated against manually reviewed samples
SENTIMENT_THRESHOLDS: dict[str, tuple[float, float]] = {
    "Very Negative": (-1.0, -0.6),
    "Negative": (-0.6, -0.2),
    "Mixed": (-0.2, 0.2),
    "Positive": (0.2, 0.6),
    "Very Positive": (0.6, 1.0),
}


class SentimentAnalyzer:
    """
    Sentiment analyzer with domain-tuned lexicon and asymmetric scoring.
    """

    def __init__(
        self,
        custom_lexicon: dict[str, float] | None = None,
        negation_overrides: list[str] | None = None,
    ):
        """
        Initialize VADER with custom lexicon overlay.

        Args:
            custom_lexicon: Dict of {word: score} to override in VADER's lexicon.
                If None, uses the default CUSTOM_LEXICON from config.
            negation_overrides: Words to move from VADER's lexicon to its negation
                list. If None, uses the default NEGATION_OVERRIDES from config.
        """
        self.sia = SentimentIntensityAnalyzer()
        self._apply_lexicon_overlay(
            custom_lexicon or CUSTOM_LEXICON,
            negation_overrides or NEGATION_OVERRIDES,
        )

    def _apply_lexicon_overlay(
        self,
        lexicon: dict[str, float],
        negation_words: list[str],
    ) -> None:
        """
        Merge custom word scores into VADER's lexicon and adjust negation handling.

        This modifies VADER's internal state:
        - Updates lexicon entries with domain-specific scores
        - Moves specified words from the lexicon to the negation set

        Args:
            lexicon: Dict of {word: score} overrides.
            negation_words: Words to treat as negation modifiers instead of
                standalone sentiment carriers.
        """
        self.sia.lexicon.update(lexicon)

        for word in negation_words:
            self.sia.constants.NEGATE.add(word)
            self.sia.lexicon.pop(word, None)

    def score(self, text: str) -> float:
        """
        Compute the enhanced polarity score for a text statement.

        Uses VADER's polarity_scores() internally, then applies asymmetric
        logic via enhanced_score() to amplify negative signals.

        Args:
            text: A single atomic statement (post sentence-splitting).

        Returns:
            Float in range [-1, +1]. Positive values indicate positive sentiment,
            negative values indicate negative sentiment. The distribution is
            deliberately asymmetric - see enhanced_score() for details.
        """
        raw_scores = self.sia.polarity_scores(text)
        return self.enhanced_score(raw_scores)

    @staticmethod
    def enhanced_score(scores: dict[str, float]) -> float:
        """
        Asymmetric polarity scoring that amplifies negative signals.

        Replaces VADER's default compound score with logic that treats negative
        feedback more decisively. This reflects the business objective: NPS
        improvement programs need to find pain points, not confirm strengths.

        Logic:
        - If neg == 0.0: purely positive -> return +1
        - If pos == 0.0: purely negative -> return -1
        - If pos > neg: positive-leaning -> return pos + neu (retain magnitude)
        - If neg > pos: negative-leaning -> return -(neg + neu) (amplified)
        - Otherwise: tied -> fall back to compound score

        The key asymmetry is that for negative-leaning text, the neutral component
        is added to the negative magnitude rather than diluting it. In NPS feedback,
        neutral words surrounding a negative term are context, not counterbalance.

        Args:
            scores: VADER polarity_scores output dict with keys:
                'neg', 'neu', 'pos', 'compound'.

        Returns:
            Enhanced polarity score in range [-1, +1].
        """
        if scores["neg"] == 0.0:
            return 1.0
        elif scores["pos"] == 0.0:
            return -1.0
        elif scores["pos"] > scores["neg"]:
            return scores["pos"] + scores["neu"]
        elif scores["pos"] < scores["neg"]:
            return (scores["neg"] + scores["neu"]) * -1
        else:
            return scores["compound"]

    @staticmethod
    def categorize(score: float) -> str:
        """
        Map a polarity score to a human-readable sentiment category.

        Args:
            score: Enhanced polarity score from score() method.

        Returns:
            One of: "Very Negative", "Negative", "Mixed", "Positive", "Very Positive",
            or "Neutral" (if score is exactly 0).

        Thresholds were calibrated against manually reviewed samples to minimize
        the "Mixed" bucket, which was uninformative for leadership reporting.
        """
        if score == 0:
            return "Neutral"
        elif score < -0.6:
            return "Very Negative"
        elif score < -0.2:
            return "Negative"
        elif score < 0.2:
            return "Mixed"
        elif score < 0.6:
            return "Positive"
        else:
            return "Very Positive"
