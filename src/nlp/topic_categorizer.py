"""
Topic Categorization via spaCy Matcher

Extracts strategic topic categories from atomic statements using spaCy's
rule-based Matcher with a hybrid pattern strategy combining keyword matching,
lemma matching, and named entity recognition.

Design choices:
- Keyword Matcher over statistical topic modeling (LDA/BERTopic) because
  the output must map directly to organizational strategic initiatives,
  not abstract clusters. See ADR-005.
- Includes known typos and misspellings in the keyword lexicon to handle
  malformed input without spell-correction. See ADR-006.
- Uses both LOWER (exact text) and LEMMA (morphological root) matching for
  single-word keywords, catching inflected forms automatically.
- Multi-word phrases use exact token sequence matching.
- Named entity patterns detect person names (PERSON) and map them to the
  engagement category (customers mentioning their account representative).

See ADR-005 and ADR-006 for full rationale.
"""

import spacy
from spacy.matcher import Matcher
from spacy.language import Language

from src.config.categories import get_categories


class TopicCategorizer:
    """
    Extracts topic categories from text using spaCy's rule-based Matcher.
    """

    def __init__(self, nlp: Language | None = None):
        """
        Initialize the categorizer with a spaCy model and build match patterns
        from the category taxonomy.

        Args:
            nlp: A loaded spaCy Language model. If None, loads 'en_core_web_lg'.
                When used as part of the full pipeline, the same nlp instance
                from SentenceSplitter should be passed to avoid loading the
                model twice.
        """
        self.nlp = nlp or spacy.load("en_core_web_lg")
        self.matcher = Matcher(self.nlp.vocab)
        self._build_patterns()

    def _build_patterns(self) -> None:
        """
        Build spaCy Matcher patterns from the category taxonomy.

        For each category in the taxonomy:
        1. Collect all single-word keywords and compute their lemmas
        2. Create a combined pattern matching on LEMMA or LOWER for singles
        3. Create exact token-sequence patterns for multi-word phrases
        4. Register all patterns under the category label

        Additionally registers a special 'account-rep' pattern that matches
        any PERSON entity (via spaCy NER), mapping to the engagement category
        in downstream processing.

        Pattern structure:
        - Single-word: [{"LEMMA": {"IN": [lemmas]}, "OP": "?"}, {"LOWER": {"IN": [words]}, "OP": "?"}]
        - Multi-word: [{"LOWER": "ease"}, {"LOWER": "of"}, {"LOWER": "use"}]
        - Person NER: [{"ENT_TYPE": {"IN": ["PERSON"]}}]
        """
        raise NotImplementedError

    def extract_topics(self, text: str) -> set[str]:
        """
        Extract matched topic categories from a text statement.

        Args:
            text: A single atomic statement (post sentence-splitting).

        Returns:
            Set of matched category labels (e.g., {"product", "support"}).
            Returns an empty set if no keywords match.

        The matcher runs the full spaCy pipeline on the text (tokenization,
        NER, etc.) and applies all registered patterns. Matched pattern IDs
        are resolved to their category label via the spaCy vocabulary.
        """
        raise NotImplementedError

    def extract_topics_with_evidence(self, text: str) -> list[tuple[str, str]]:
        """
        Extract topics with the matched text span as evidence.

        Useful for debugging and auditing categorization decisions.

        Args:
            text: A single atomic statement.

        Returns:
            List of (matched_text, category) tuples.
            Example: [("licensing", "licensing"), ("expensive", "high-price")]
        """
        raise NotImplementedError
