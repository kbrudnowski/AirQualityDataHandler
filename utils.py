"""
Utility functions for the air quality processor.
"""

import logging
import requests
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def get_city_bbox_from_osm(
    city_name: str,
) -> Optional[Tuple[float, float, float, float]]:
    """
    Get city bounding box coordinates from OpenStreetMap Nominatim API

    Args:
        city_name: Name of the city

    Returns:
        Tuple of (min_lon, min_lat, max_lon, max_lat) or None if not found
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "city": city_name,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }
        headers = {"User-Agent": "AirQualityProcessor/1.0"}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        if not data:
            logger.warning(f"No coordinates found for {city_name}")
            return None

        bbox = data[0].get("boundingbox")
        if not bbox:
            logger.warning(f"No bounding box found for {city_name}")
            return None

        return convert_bbox_format(bbox, city_name)

    except Exception as e:
        logger.error(f"Error getting coordinates for {city_name}: {e}")
        return None


def convert_bbox_format(
    osm_bbox: list, city_name: str
) -> Optional[Tuple[float, float, float, float]]:
    """
    Convert OpenStreetMap bbox format to OpenAQ format

    Args:
        osm_bbox: OpenStreetMap bbox [min_lat, max_lat, min_lon, max_lon]
        city_name: City name for error logging

    Returns:
        OpenAQ bbox tuple (min_lon, min_lat, max_lon, max_lat) or None if invalid
    """
    try:
        if len(osm_bbox) != 4:
            logger.error(f"Invalid bbox format for {city_name}: {osm_bbox}")
            return None

        min_lat, max_lat, min_lon, max_lon = (
            round(float(coord), 4) for coord in osm_bbox
        )

        if min_lat >= max_lat or min_lon >= max_lon:
            logger.error(f"Invalid bbox coordinates for {city_name}: {osm_bbox}")
            return None

        openaq_bbox = (
            min_lon,
            min_lat,
            max_lon,
            max_lat,
        )

        logger.info(f"Converted bbox for OpenAQ: {openaq_bbox}")
        return openaq_bbox

    except Exception as e:
        logger.error(f"Error converting bbox for {city_name}: {e}")
        return None
