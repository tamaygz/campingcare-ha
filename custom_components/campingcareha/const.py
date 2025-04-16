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
    RESERVATIONS = "/reservations"  # Base path for reservation related endpoints
    PLACES = "/places"  # Base path for places related endpoints
    VERSION = "/version"  # Base path for version related endpoints

class ApiQuery(StrEnum):
    """API query parameters for Camping Care."""
    PLATE = "plate={plate}"  # Query parameter for license plate
    LICENSE_PLATE = "license_plate={plate}"  # Query parameter for license plate in search
    ID = "/{id}"  # Placeholder for ID in URL
    START_DATE = "start_date={start_date}"  # Query parameter for start date
    END_DATE = "end_date={end_date}"  # Query parameter for end date

class ApiEndpoints(StrEnum):
    """API endpoints for Camping Care."""
    # LICENSE PLATES
    FIND_LICENSE_PLATE_AND_GET_RESERVATION = ApiTopics.LICENSE_PLATES + "?" + ApiQuery.LICENSE_PLATE + "&get_reservation=true"  # Search for a license plate and retrieve the associated reservation
    CHECK_LICENSE_PLATE = ApiTopics.LICENSE_PLATES + "/check_plate?" + ApiQuery.PLATE  # Check if a license plate is valid

    #RESERVATIONS
    GET_RESERVATION = ApiTopics.RESERVATIONS + ApiQuery.ID  # Get reservation details by ID

    #PLACES
    GET_PLACES = ApiTopics.PLACES  # Endpoint to retrieve the list of places
    
    #API
    GET_API_VERSION = ApiTopics.VERSION  # Get the API version


