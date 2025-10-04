"""
Data models and type definitions for the air quality processor.
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class AirQualityMeasurement:
    """Represents a single air quality measurement."""

    city_name: str
    location_name: str
    parameter_name: str
    parameter_value: float
    parameter_unit: str
    utc_ts: str


@dataclass
class ProcessingResult:
    """Result of air quality data processing."""

    success: bool
    measurements_count: int
    csv_file_path: Optional[str] = None
    error_message: Optional[str] = None


# Type aliases for better code readability
MeasurementList = List[AirQualityMeasurement]
