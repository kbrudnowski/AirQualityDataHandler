"""
Air quality data processing service.
"""

import logging
from typing import List
from openaq import OpenAQ
from openaq.shared.responses import Location, LatestResponse

from models import AirQualityMeasurement, MeasurementList
from utils import get_city_bbox_from_osm

logger = logging.getLogger(__name__)

STATIONS_PER_CITY_LIMIT = 3
REQUESTED_PARAMETERS = ["pm25", "pm10", "o3", "no2"]


class AirQualityDataProcessor:
    """Processes air quality data from OpenAQ API."""

    def process_measurements(
        self, location_info: Location, measurements_data: LatestResponse, city_name: str
    ) -> MeasurementList:
        """
        Process raw measurements into standardized format

        Args:
            location_info: Location information from OpenAQ
            measurements_data: Latest measurements data
            city_name: Name of the city

        Returns:
            List of AirQualityMeasurement objects
        """
        processed_measurements = []

        try:
            location_name = location_info.name

            sensor_mapping = {}
            for sensor in location_info.sensors:
                sensor_mapping[sensor.id] = {
                    "units": sensor.parameter.units,
                    "name": sensor.parameter.name,
                }

            if not measurements_data.results:
                logger.warning(f"No measurements found for {city_name}")
                return processed_measurements

            for measurement in measurements_data.results:
                try:
                    sensor_id = measurement.sensors_id
                    value = measurement.value
                    datetime_info = measurement.datetime
                    utc_ts = datetime_info.get("utc") if datetime_info else None

                    if sensor_id in sensor_mapping:
                        sensor_info = sensor_mapping[sensor_id]
                        sensor_unit = sensor_info["units"]
                        sensor_name = sensor_info["name"]
                    else:
                        sensor_unit = "Unknown"
                        sensor_name = f"Sensor_{sensor_id}"

                    if value is None:
                        logger.warning(
                            f"Skipping measurement with no value for sensor {sensor_id}"
                        )
                        continue

                    if sensor_name not in REQUESTED_PARAMETERS:
                        logger.warning(
                            f"Skipping measurement with parameter {sensor_name} not in {REQUESTED_PARAMETERS}"
                        )
                        continue

                    processed_measurement = AirQualityMeasurement(
                        city_name=city_name,
                        location_name=location_name,
                        parameter_name=sensor_name,
                        parameter_value=value,
                        parameter_unit=sensor_unit,
                        utc_ts=utc_ts,
                    )

                    processed_measurements.append(processed_measurement)

                except Exception as e:
                    logger.warning(f"Error processing measurement: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error processing measurements for {city_name}: {e}")

        return processed_measurements


def fetch_air_quality_data(cities: List[str], api_key: str) -> MeasurementList:
    """
    Fetch air quality data for specified cities

    Args:
        cities: List of city names
        api_key: OpenAQ API key

    Returns:
        List of AirQualityMeasurement objects
    """
    client = OpenAQ(api_key=api_key)
    processor = AirQualityDataProcessor()
    all_measurements = []

    for city in cities:
        try:
            city_bbox = get_city_bbox_from_osm(city)
            if not city_bbox:
                logger.warning(f"Could not get coordinates for {city}")
                continue

            logger.info(f"Fetching locations for {city} with bbox: {city_bbox}")

            # Get locations within the city bounding box
            locations = client.locations.list(
                bbox=city_bbox,
                limit=STATIONS_PER_CITY_LIMIT,
            )

            if not locations.results:
                logger.warning(f"No locations found for {city}")
                continue

            logger.info(f"Found {len(locations.results)} locations for {city}")

            for location in locations.results:
                try:
                    location_info = client.locations.get(location.id).results[0]
                    raw_measurements = client.locations.latest(locations_id=location.id)
                    processed_measurements = processor.process_measurements(
                        location_info, raw_measurements, city
                    )
                    all_measurements.extend(processed_measurements)
                    logger.info(
                        f"Processed measurements for location {location.id} in {city}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to get measurements for location {location.id} in {city}: {e}"
                    )
                    continue

        except Exception as e:
            logger.error(f"Failed to process data for {city}: {str(e)}")
            continue

    return all_measurements
