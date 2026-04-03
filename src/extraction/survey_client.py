"""
Survey Data Extraction Client

Abstract interface for extracting NPS survey responses from an external survey
platform. The production implementation used API-based extraction from a survey
platform to pull batch data by year.

Architecture notes:
- Extraction is decoupled from processing - raw data is persisted to disk as
  JSON, so the NLP pipeline can be re-run without re-fetching.
- The API returns paginated results (max ~10,000 records per request). The
  client handles pagination transparently and writes one file per batch.
- Authentication is session-based. The production implementation managed
  session credentials externally (not stored in code).

This module provides the interface contract only. The production extraction
logic used a platform-specific API that is not reproducible here.
See ADR-006 in the original codebase for the extraction pattern rationale.
"""

from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path


class SurveyClient(ABC):
    """
    Abstract base class for survey data extraction.

    Implementations handle platform-specific authentication, pagination,
    and response format normalization.
    """

    @abstractmethod
    def extract(self, year: int, output_dir: Path) -> Path:
        """
        Extract all survey responses for a given calendar year.

        Args:
            year: The calendar year to extract (e.g., 2023).
            output_dir: Directory to write the raw JSON output file.

        Returns:
            Path to the written JSON file.

        The output file contains a JSON array of record objects, each with
        raw field identifiers from the survey platform. Field ID normalization
        happens in the ingestion stage, not here.
        """
        raise NotImplementedError

    @abstractmethod
    def extract_range(self, start_date: date, end_date: date, output_dir: Path) -> Path:
        """
        Extract survey responses within a specific date range.

        Args:
            start_date: Inclusive start date for the extraction window.
            end_date: Inclusive end date for the extraction window.
            output_dir: Directory to write the raw JSON output file.

        Returns:
            Path to the written JSON file.
        """
        raise NotImplementedError

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Test connectivity to the survey platform API.

        Returns:
            True if the connection is valid and authenticated.
        """
        raise NotImplementedError
