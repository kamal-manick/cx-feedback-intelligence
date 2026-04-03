"""
Custom Sentence Boundary Detection

Splits multi-clause NPS feedback into atomic statements for independent
sentiment and topic analysis. This is the most architecturally significant
transformation in the pipeline.

Problem:
    NPS feedback is often compound: "The platform is great but licensing is
    confusing and support is slow." Default NLP parsers treat this as 1-2
    sentences, producing a blended sentiment that masks opposing signals.

Solution:
    Inject custom sentence boundaries into the spaCy pipeline that split on:
    - Semicolons and commas (when appropriate)
    - Conjunctions like "however" and "but"
    - Newline characters
    Then filter out salutation lines that carry no feedback signal.

Result:
    ~1.7x expansion of the dataset (20K responses -> ~34K atomic statements),
    where each statement can receive independent sentiment and topic labels.

See ADR-001 for the full rationale behind this approach.
"""

import spacy
from spacy.language import Language
from spacy.tokens import Doc


# Salutation lines to filter out - these carry no feedback signal
SKIP_LINES: list[str] = [
    "thanks!",
    "thanks !",
    "thanks and regards,",
    "thanks,",
    "thanks ,",
    "regards,",
    "regards ,",
]

# Conjunctions that signal sentiment reversal - mark as sentence start
REVERSAL_CONJUNCTIONS: list[str] = ["however", "but"]

# Punctuation marks that indicate clause boundaries
CLAUSE_BOUNDARY_PUNCTUATION: list[str] = [";", ","]


class SentenceSplitter:
    """
    Splits NPS comment text into atomic statements using custom spaCy
    sentence boundary rules.
    """

    def __init__(self, model_name: str = "en_core_web_lg"):
        """
        Initialize the splitter with a spaCy language model.

        Args:
            model_name: Name of the spaCy model to load.
                The production system uses 'en_core_web_lg' for best accuracy
                on varied customer feedback text.
        """
        self.nlp = spacy.load(model_name)
        self._register_custom_boundaries()

    def _register_custom_boundaries(self) -> None:
        """
        Register the custom sentence boundary component in the spaCy pipeline.

        The component is inserted before the parser so that downstream NLP
        processing (NER, dependency parsing) operates on the already-split
        segments.

        Design note: The boundary rules are deliberately aggressive - we prefer
        over-splitting (which produces short fragments that get filtered later)
        over under-splitting (which masks opposing sentiment signals).
        """
        component_name = "set_custom_boundaries"

        if component_name in self.nlp.pipe_names:
            self.nlp.remove_pipe(component_name)

        @Language.component(component_name)
        def set_custom_boundaries(doc: Doc) -> Doc:
            """
            Mark additional sentence boundaries on clause-separating punctuation
            and sentiment-reversing conjunctions.

            Rules:
            1. Semicolons and commas -> sentence break (unless preceded by a
               reversal conjunction, which would create orphan fragments)
            2. "however" and "but" -> sentence break at the conjunction itself

            These rules are tuned for NPS feedback patterns where conjunctions
            almost always signal a topic or sentiment shift.
            """
            # --- Stub: production boundary detection logic ---
            # The actual implementation iterates through tokens and sets
            # is_sent_start based on the rules described above.
            raise NotImplementedError
            return doc

        self.nlp.add_pipe(component_name, before="parser")

    def split(self, text: str) -> list[tuple[int, str]]:
        """
        Split a comment into indexed atomic statements.

        Args:
            text: Raw comment text from a survey response.

        Returns:
            List of (sequence_number, statement_text) tuples.
            Sequence numbers are zero-indexed within the comment.
            Salutation lines and whitespace-only segments are filtered out.
            Returns [(0, "null")] if no valid segments remain.

        Example:
            >>> splitter = SentenceSplitter()
            >>> splitter.split("Great product; however, pricing is confusing.")
            [(0, "Great product"), (1, "however"), (2, "pricing is confusing.")]
        """
        raise NotImplementedError

    @staticmethod
    def _is_skip_line(text: str) -> bool:
        """Check if a text segment is a salutation/skip line."""
        return text.strip().lower() in SKIP_LINES
