"""Constants for Camping Care HA integration."""
from __future__ import annotations
from enum import StrEnum

DOMAIN = "campingcareha"

CONF_API_KEY = "api_key"
CONF_API_URL = "api_url"
CONF_NAME = "name"

DEFAULT_API_URL = "https://api.camping.care/v21"


class ApiTopics(StrEnum):
    """API topics for Camping Care."""
    LICENSE_PLATES = "/license_plates"  # Base path for license plate related endpoints
    VERSION = "/version"  # Base path for version related endpoints

class ApiQuery(StrEnum):
    """API query parameters for Camping Care."""
    PLATE = "plate={plate}"  # Query parameter for license plate

class ApiEndpoints(StrEnum):
    """API endpoints for Camping Care."""
    CHECK_LICENSE_PLATE = ApiTopics.LICENSE_PLATES + "/check_plate?" + ApiQuery.PLATE  # Check if a license plate is valid
    GET_API_VERSION = ApiTopics.VERSION  # Get the API version
