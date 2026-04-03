"""
Data Transformation and Export

Prepares the analyzed DataFrame for BI dashboard consumption. Handles:
- Filtering to retain only statements with valid topic matches
- Aggregating statement-level topics back to the response level
- Joining enriched data back to the full dataset
- Writing structured output in Excel format with multiple sheets

Output format:
- Sheet 1 ("NPS_Data"): Full dataset with one row per original response,
  including the aggregated directional topic set
- Sheet 2 ("Topics"): Exploded view with one row per directional label,
  designed for pivot table and dashboard consumption

The BI layer (Power BI) consumes the Excel export directly. The two-sheet
design allows the dashboard to show both aggregate trends (from the topics
sheet) and drill-down detail (from the full data sheet).
"""

from pathlib import Path

import pandas as pd


class DataExporter:
    """
    Transforms analyzed data and writes structured output for BI consumption.
    """

    def __init__(self, output_path: Path):
        """
        Args:
            output_path: Path for the output Excel file.
        """
        self.output_path = output_path

    def prepare_topics_sheet(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create the exploded topics view for dashboard consumption.

        Takes the statement-level DataFrame with directional topic sets and:
        1. Groups by original response index
        2. Unions topic sets across all statements in each response
        3. Explodes the unioned set so each directional label gets its own row

        Args:
            df: Statement-level DataFrame with a 'directional_topics' column
                containing sets of directional labels.

        Returns:
            DataFrame with one row per (response_index, directional_label) pair.
        """
        raise NotImplementedError

    def join_to_full_dataset(
        self,
        full_df: pd.DataFrame,
        topics_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Join the aggregated topic data back to the full response dataset.

        The full dataset includes all responses (including those without comments
        or without topic matches). The join adds the 'directional_topics' column
        to responses that have matches; others receive NaN.

        Args:
            full_df: Complete response-level DataFrame (all ~35K responses).
            topics_df: Aggregated topic data from prepare_topics_sheet().

        Returns:
            Full DataFrame with directional_topics column added.
        """
        raise NotImplementedError

    def export(
        self,
        full_df: pd.DataFrame,
        topics_df: pd.DataFrame,
    ) -> None:
        """
        Write the final output to Excel with two sheets.

        Args:
            full_df: Full response dataset with topic annotations.
            topics_df: Exploded topics view for pivot tables.

        Output file structure:
            Sheet "NPS_Data": full_df with date formatting
            Sheet "Topics": topics_df for dashboard consumption
        """
        raise NotImplementedError
