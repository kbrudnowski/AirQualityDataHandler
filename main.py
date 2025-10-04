"""
Google Cloud Function for processing air quality data from OpenAQ API.
Fetches data for specified cities and uploads CSV to Google Cloud Storage.
"""

import json
import logging
import os
from typing import List
from functions_framework import http

from services.air_quality_processor import fetch_air_quality_data
from services.gcs_manager import GCSManager
from models import ProcessingResult, MeasurementList

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_processing_result(
    success: bool,
    measurements: MeasurementList,
    csv_file_path: str = None,
    error_message: str = None,
) -> ProcessingResult:
    """Create a ProcessingResult object."""
    return ProcessingResult(
        success=success,
        measurements_count=len(measurements) if measurements else 0,
        csv_file_path=csv_file_path,
        error_message=error_message,
    )


@http
def air_quality_processor(request):
    """
    Google Cloud Function entry point for air quality data processing.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with processing results
    """
    try:
        api_key = os.getenv("OPENAQ_API_KEY")
        if not api_key:
            logger.error("OPENAQ_API_KEY environment variable not set")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "OPENAQ_API_KEY not configured"}),
            }

        # Default parameters (can be overridden via request parameters)
        cities = ["Warsaw", "London"]
        bucket_name = "air-quality-data-bucket-01"
        filename = "air_quality_data"

        if request.method == "POST":
            try:
                request_data = request.get_json()
                if request_data:
                    if "cities" in request_data:
                        cities = request_data["cities"]
                    if "bucket_name" in request_data:
                        bucket_name = request_data["bucket_name"]
                    if "filename" in request_data:
                        filename = request_data["filename"]
            except Exception as e:
                logger.warning(f"Could not parse request JSON: {str(e)}")

        logger.info(f"Starting air quality data processing for cities: {cities}")
        all_measurements = fetch_air_quality_data(cities, api_key)

        if not all_measurements:
            logger.warning("No measurements retrieved")
            result = create_processing_result(
                False,
                all_measurements,
                error_message="No air quality data found for the specified cities",
            )
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": result.error_message,
                        "measurements_count": result.measurements_count,
                    }
                ),
            }

        # Upload results to GCS
        gcs_manager = GCSManager()
        csv_file_path = gcs_manager.upload_csv_to_gcs(
            all_measurements, bucket_name, filename
        )

        logger.info(f"Successfully processed {len(all_measurements)} measurements")

        result = create_processing_result(True, all_measurements, csv_file_path)
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Air quality data processed successfully",
                    "measurements_count": result.measurements_count,
                    "csv_file": result.csv_file_path,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error processing air quality data: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Internal server error: {str(e)}"}),
        }
