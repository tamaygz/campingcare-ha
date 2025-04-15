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
                        data = await response.json()
                        _LOGGER.debug("CampingCareAPI: Version request successful: %s", data)
                        return data["version"]
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