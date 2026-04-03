"""
Pipeline Orchestrator

Ties all stages together into an end-to-end execution flow:

    Extraction -> Ingestion -> Sentence Splitting -> Sentiment Analysis
    -> Topic Categorization -> Topic-Sentiment Mapping -> Export

Each stage is a separate module with a well-defined interface (see
ARCHITECTURE.md for interface contracts). The orchestrator coordinates
data flow between stages and manages the shared spaCy model instance.

Design notes:
- The spaCy model is loaded once and shared between SentenceSplitter and
  TopicCategorizer to avoid redundant memory usage (~500MB for en_core_web_lg).
- Each stage operates on pandas DataFrames, passing them forward through
  the pipeline.
- The pipeline is idempotent - re-running on the same input produces
  identical output.
- Raw extraction artifacts are persisted to disk, decoupling extraction
  from processing.
"""

from pathlib import Path

import pandas as pd
import spacy

from src.ingestion.consolidator import DataConsolidator
from src.nlp.sentence_splitter import SentenceSplitter
from src.nlp.sentiment_analyzer import SentimentAnalyzer
from src.nlp.topic_categorizer import TopicCategorizer
from src.nlp.topic_sentiment_mapper import TopicSentimentMapper, aggregate_response_topics
from src.transformation.exporter import DataExporter


class FeedbackAnalysisPipeline:
    """
    End-to-end orchestrator for the CX feedback analysis pipeline.
    """

    def __init__(
        self,
        raw_data_dir: Path,
        output_path: Path,
        spacy_model: str = "en_core_web_lg",
    ):
        """
        Initialize all pipeline components.

        Args:
            raw_data_dir: Directory containing raw JSON export files.
            output_path: Path for the final Excel output file.
            spacy_model: Name of the spaCy model to load. Shared between
                the sentence splitter and topic categorizer.
        """
        # Load spaCy model once - shared across NLP components
        self.nlp = spacy.load(spacy_model)

        # Initialize pipeline stages
        self.consolidator = DataConsolidator()
        self.splitter = SentenceSplitter.__new__(SentenceSplitter)
        self.splitter.nlp = self.nlp
        self.sentiment = SentimentAnalyzer()
        self.topics = TopicCategorizer(nlp=self.nlp)
        self.mapper = TopicSentimentMapper()
        self.exporter = DataExporter(output_path)

        self.raw_data_dir = raw_data_dir
        self.output_path = output_path

    def run(self) -> pd.DataFrame:
        """
        Execute the full pipeline end-to-end.

        Steps:
        1. Discover and consolidate raw data files
        2. Clean and filter for comments
        3. Split comments into atomic statements
        4. Score sentiment for each statement
        5. Extract topic categories for each statement
        6. Map topics + sentiment + NPS score to directional labels
        7. Aggregate topics to response level
        8. Export structured output

        Returns:
            The final enriched DataFrame (also written to disk via exporter).
        """
        raise NotImplementedError

    def _discover_raw_files(self) -> list[Path]:
        """Find all raw JSON export files in the data directory."""
        return sorted(self.raw_data_dir.glob("*.json"))

    def _stage_ingest(self, raw_files: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Stage 1-2: Load, consolidate, and clean raw data.

        Returns:
            Tuple of (full_dataset, comments_only_dataset).
            The full dataset is retained for the final join.
        """
        raise NotImplementedError

    def _stage_split(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Stage 3: Expand each comment into atomic statements.

        Applies sentence splitting and explodes the DataFrame so each
        statement gets its own row. Adds statement_seq and statement_text
        columns.
        """
        raise NotImplementedError

    def _stage_sentiment(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Stage 4: Score sentiment for each atomic statement.

        Adds sentiment_score and sentiment_category columns.
        """
        raise NotImplementedError

    def _stage_topics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Stage 5: Extract topic categories for each statement.

        Adds a topics column containing a set of matched categories.
        """
        raise NotImplementedError

    def _stage_map(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Stage 6: Produce directional topic labels.

        Cross-references topics, sentiment, and NPS score to produce
        labels like "product is good" or "pricing is bad".
        Adds a directional_topics column.
        """
        raise NotImplementedError

    def _stage_aggregate_and_export(
        self,
        statements_df: pd.DataFrame,
        full_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Stage 7-8: Aggregate statement topics to response level and export.

        Unions directional labels from all statements belonging to the same
        response, joins back to the full dataset, and writes to Excel.
        """
        raise NotImplementedError
