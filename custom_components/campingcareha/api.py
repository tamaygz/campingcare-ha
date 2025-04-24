import logging
from aiohttp import ClientSession, ClientError
from .const import ApiEndpoints, ApiQuery

_LOGGER = logging.getLogger(__name__)

class CampingCareAPI:
    """Class to handle API communication with CampingCare."""

    def __init__(self, api_url: str, api_key: str):
        """Initialize the API client."""
        self.api_url = api_url
        self.api_key = api_key

    async def test_connection(self) -> bool:
        """Test the API connection."""
        version = await self.version()
        if version:
            _LOGGER.debug("CampingCareAPI: API test successful. Version: %s", version)
            return True
        _LOGGER.warning("CampingCareAPI: API test failed. (Unable to get positive answer on version request)")
        return False

    async def version(self) -> str:
        """Get the API version."""
        try:
            async with ClientSession() as session:
                async with session.get(
                    f"{self.api_url}{ApiEndpoints.GET_API_VERSION}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                ) as response:
                    if response.status == 200:
                        _version = await response.text()
                        _LOGGER.debug("CampingCareAPI: Version request successful: %s", _version)
                        return str(_version)
                    else:
                        _LOGGER.error("CampingCareAPI: API error: %s", response.status)
                        return None
        except ClientError as e:
            _LOGGER.error("CampingCareAPI: API request failed: %s", e)
            return None
        

    async def check_license_plate(self, plate: str) -> dict:
        """Check if a license plate is valid."""
        try:
            async with ClientSession() as session:
                async with session.get(
                    f"{self.api_url}{ApiEndpoints.CHECK_LICENSE_PLATE.format(plate=plate)}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.debug("CampingCareAPI: License plate check successful: %s", data)
                        return {"success": True, "data": data}
                    else:
                        _LOGGER.error("CampingCareAPI: API error: %s", response.status)
                        return {"success": False, "error": f"API error: {response.status}"}
        except ClientError as e:
            _LOGGER.error("CampingCareAPI: API request failed: %s", e)
            return {"success": False, "error": str(e)}
        
    async def query_license_plate(self, plate: str) -> dict:
        """Search for a license plate and retrieve the associated reservation."""
        try:
            async with ClientSession() as session:
                # Construct the endpoint with query parameters
                endpoint = f"{self.api_url}{ApiEndpoints.FIND_LICENSE_PLATE_AND_GET_RESERVATION.format(plate=plate)}"
                async with session.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # _LOGGER.debug("CampingCareAPI: License plate search successful: %s", data)
                        
                        # Check if the response is a list
                        if isinstance(data, list):
                            if len(data) > 0:
                                for item in data:
                                    _LOGGER.info("Reservation found: Kategorie: %s, Platznummer: %s", 
                                                 item.get("reservation", {}).get("accommodation", {}).get("name", "Unknown"), 
                                                 item.get("reservation", {}).get("place", {}).get("name", "Unknown"))
                                return {"success": True, "data": data}
                            else:
                                _LOGGER.warning("CampingCareAPI: No reservation found for plate: %s", plate)
                                return {"success": False, "error": "No reservation found"}
                        
                        # Handle unexpected response formats
                        _LOGGER.error("CampingCareAPI: Unexpected response format: %s", data)
                        return {"success": False, "error": "Unexpected response format"}
                    
                    elif response.status == 404:
                        _LOGGER.warning("CampingCareAPI: No reservation found for plate: %s", plate)
                        return {"success": False, "error": "No reservation found"}
                    else:
                        _LOGGER.error("CampingCareAPI: API error: %s", response.status)
                        return {"success": False, "error": f"API error: {response.status}"}
        except ClientError as e:
            _LOGGER.error("CampingCareAPI: API request failed: %s", e)
            return {"success": False, "error": str(e)}
        
    async def get_reservation(self, reservation_id: str) -> dict:
        """Retrieve a reservation by its ID."""
        try:
            async with ClientSession() as session:
                # Construct the endpoint with the reservation ID
                endpoint = f"{self.api_url}{ApiEndpoints.GET_RESERVATION.format(id=reservation_id)}"
                async with session.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        _LOGGER.debug("CampingCareAPI: Reservation retrieval successful: %s", data)
                        return {"success": True, "data": data}
                    elif response.status == 404:
                        _LOGGER.warning("CampingCareAPI: Reservation with ID %s not found.", reservation_id)
                        return {"success": False, "error": "Reservation not found"}
                    else:
                        _LOGGER.error("CampingCareAPI: API error: %s", response.status)
                        return {"success": False, "error": f"API error: {response.status}"}
        except ClientError as e:
            _LOGGER.error("CampingCareAPI: API request failed: %s", e)
            return {"success": False, "error": str(e)}