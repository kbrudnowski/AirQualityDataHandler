"""
Google Cloud Storage manager for uploading CSV files.
"""

import logging
import csv
import io
from datetime import datetime
from models import MeasurementList
from google.cloud import storage

logger = logging.getLogger(__name__)


class GCSManager:
    """Manages Google Cloud Storage operations."""

    def __init__(self):
        """Initialize GCS client."""
        self.client = storage.Client()

    def upload_csv_to_gcs(
        self, measurements: MeasurementList, bucket_name: str, filename: str
    ) -> str:
        """
        Upload measurements as CSV to Google Cloud Storage

        Args:
            measurements: List of AirQualityMeasurement objects
            bucket_name: Name of the GCS bucket
            filename: Base name of the file (without .csv extension)
                     A timestamp will be automatically added to ensure uniqueness

        Returns:
            GCS path of the uploaded file (includes timestamp in filename)
        """
        try:
            bucket = self.client.bucket(bucket_name)
            csv_content = self._create_csv_content(measurements)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            blob_name = f"{filename}_{timestamp}.csv"
            blob = bucket.blob(blob_name)
            blob.upload_from_string(csv_content, content_type="text/csv")

            gcs_path = f"gs://{bucket_name}/{blob_name}"
            logger.info(f"Successfully uploaded CSV to {gcs_path}")

            return gcs_path

        except Exception as e:
            logger.error(f"Error uploading to GCS: {str(e)}")
            raise

    def _create_csv_content(self, measurements: MeasurementList) -> str:
        """
        Create CSV content from measurements

        Args:
            measurements: List of AirQualityMeasurement objects

        Returns:
            CSV content as string
        """
        if not measurements:
            return ""

        fieldnames = [
            "city_name",
            "location_name",
            "parameter_name",
            "parameter_value",
            "parameter_unit",
            "utc_ts",
        ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for measurement in measurements:
            writer.writerow(
                {
                    "city_name": measurement.city_name,
                    "location_name": measurement.location_name,
                    "parameter_name": measurement.parameter_name,
                    "parameter_value": measurement.parameter_value,
                    "parameter_unit": measurement.parameter_unit,
                    "utc_ts": measurement.utc_ts,
                }
            )

        return output.getvalue()
