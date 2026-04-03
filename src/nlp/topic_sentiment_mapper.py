"""
Dual-Signal Topic-Sentiment Mapping

Cross-references three signals to produce directional topic labels:
1. Matched topic categories (from TopicCategorizer)
2. Text sentiment category (from SentimentAnalyzer)
3. NPS numeric score (from the original survey response)

This is the core analytical innovation of the pipeline. A topic alone
("pricing") is not actionable - leadership needs to know whether pricing
is a strength or a pain point. The mapper produces labels like
"pricing is bad" or "product is good" that map directly to strategic decisions.

Mapping rules (see ADR-004 for full rationale):
- Promoters (score > 7): default "is good"; override to "is bad" only if
  text sentiment is Very Negative
- Passives (score 5-7): default "is bad"; override to "is good" only if
  text sentiment is Very Positive
- Detractors (score < 5): always "is bad"

Special cases:
- "high-price" always maps to "price is bad" regardless of signals
- Person entity matches (account-rep) are remapped to "engagement"
- Lone "company" topic retains its own directional label
"""


class TopicSentimentMapper:
    """
    Maps topic categories + sentiment + NPS score to directional labels.
    """

    # NPS score band boundaries
    PROMOTER_THRESHOLD = 7
    PASSIVE_THRESHOLD = 4

    # Sentiment categories that trigger override rules
    STRONG_NEGATIVE = "Very Negative"
    STRONG_POSITIVE = "Very Positive"

    def map(
        self,
        topics: set[str],
        sentiment_category: str,
        nps_score: int,
    ) -> set[str] | None:
        """
        Produce directional topic labels from the three input signals.

        Args:
            topics: Set of matched category labels from TopicCategorizer
                (e.g., {"product", "licensing"}).
            sentiment_category: Text sentiment label from SentimentAnalyzer
                (e.g., "Very Negative").
            nps_score: Original NPS numeric score (0-10) from the survey response.

        Returns:
            Set of directional labels (e.g., {"product is good", "licensing is bad"}).
            Returns None if topics is empty.

        Decision matrix:
            NPS Band    | Text Sentiment  | Direction
            ------------|-----------------|----------
            Promoter    | Very Negative   | is bad
            Promoter    | (anything else) | is good
            Passive     | Very Positive   | is good
            Passive     | (anything else) | is bad
            Detractor   | (any)           | is bad
        """
        if not topics:
            return None

        # Determine direction based on NPS score band and text sentiment
        if nps_score > self.PROMOTER_THRESHOLD:
            direction = " is bad" if sentiment_category == self.STRONG_NEGATIVE else " is good"
        elif nps_score > self.PASSIVE_THRESHOLD:
            direction = " is good" if sentiment_category == self.STRONG_POSITIVE else " is bad"
        else:
            direction = " is bad"

        return self._apply_special_cases(topics, direction)

    def _apply_special_cases(
        self,
        topics: set[str],
        default_direction: str,
    ) -> set[str]:
        """
        Handle special mapping rules before applying the default direction.

        Special cases:
        1. "high-price" -> always "price is bad" (negative by definition)
        2. "account-rep" -> remapped to "engagement" with default direction
        3. Lone "company" -> retains its own directional label

        Args:
            topics: Mutable set of matched category labels.
            default_direction: The direction string (" is good" or " is bad")
                determined by the NPS score band and sentiment.

        Returns:
            Set of directional labels with special cases applied.
        """
        raise NotImplementedError


def aggregate_response_topics(statement_topics: list[set[str]]) -> set[str]:
    """
    Union all directional topic labels from a response's statements.

    A single survey response may contain multiple atomic statements, each
    with its own set of directional labels. This function unions them into
    a single set for the response-level export.

    Args:
        statement_topics: List of directional label sets, one per statement.

    Returns:
        Union of all non-None label sets.

    Example:
        >>> aggregate_response_topics([
        ...     {"product is good"},
        ...     {"support is bad", "engagement is bad"},
        ...     None,
        ... ])
        {"product is good", "support is bad", "engagement is bad"}
    """
    from functools import reduce
    valid = [t for t in statement_topics if t is not None]
    if not valid:
        return set()
    return reduce(set.union, valid)
