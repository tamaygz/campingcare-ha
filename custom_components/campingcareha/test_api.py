import unittest
from unittest.mock import AsyncMock, patch
from custom_components.campingcareha.api import CampingCareAPI

class TestCampingCareAPI(unittest.TestCase):
    def setUp(self):
        self.api = CampingCareAPI(api_key="test_key", base_url="https://api.camping.care/v21")

    @patch("custom_components.campingcareha.api.aiohttp.ClientSession.get")
    async def test_query_license_plate_success(self, mock_get):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"data": "test_data"}
        mock_get.return_value = mock_response

        result = await self.api.query_license_plate("ABC123")
        self.assertEqual(result, {"data": "test_data"})

    @patch("custom_components.campingcareha.api.aiohttp.ClientSession.get")
    async def test_query_license_plate_failure(self, mock_get):
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.json.return_value = {"error": "Not Found"}
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as context:
            await self.api.query_license_plate("XYZ789")
        self.assertIn("Error querying license plate", str(context.exception))

if __name__ == "__main__":
    unittest.main()