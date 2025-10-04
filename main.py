"""
Google Cloud Function for processing air quality data from OpenAQ API.
Fetches data for specified cities and uploads CSV to Google Cloud Storage.
"""

import logging
import os
from flask import Flask, request, jsonify

from services.air_quality_processor import fetch_air_quality_data
from services.gcs_manager import GCSManager
from models import ProcessingResult, MeasurementList

# Create Flask app
app = Flask(__name__)
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


@app.route("/", methods=["GET", "POST"])
def air_quality_processor():
    """
    Air quality data processing endpoint.

    Returns:
        HTTP response with processing results
    """
    try:
        api_key = os.getenv("OPENAQ_API_KEY")
        if not api_key:
            logger.error("OPENAQ_API_KEY environment variable not set")
            return jsonify({"error": "OPENAQ_API_KEY not configured"}), 400

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
            return jsonify(
                {
                    "message": result.error_message,
                    "measurements_count": result.measurements_count,
                }
            )

        # Upload results to GCS
        gcs_manager = GCSManager()
        csv_file_path = gcs_manager.upload_csv_to_gcs(
            all_measurements, bucket_name, filename
        )

        logger.info(f"Successfully processed {len(all_measurements)} measurements")

        result = create_processing_result(True, all_measurements, csv_file_path)
        return jsonify(
            {
                "message": "Air quality data processed successfully",
                "measurements_count": result.measurements_count,
                "csv_file": result.csv_file_path,
            }
        )

    except Exception as e:
        logger.error(f"Error processing air quality data: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting air quality processor on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
