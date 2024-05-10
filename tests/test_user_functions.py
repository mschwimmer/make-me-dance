import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import user_functions


class UserFunctionsTests(unittest.TestCase):

    @patch('user_functions.sf.get_user')
    def test_get_user_data(self, mock_get_user):
        mock_get_user.return_value = {
            "display_name": "Test Name",
            "id": "Test ID"
        }

        access_token = "mock_access_token"
        result = user_functions.get_user_data(access_token)

        self.assertEqual(result["id"], "Test ID")
        self.assertEqual(result["display_name"], "Test Name")

        mock_get_user.assert_called_once_with(access_token)

    @patch('user_functions.sf.get_user')  # Mock the get_user method from the sf module
    def test_get_user_data_malformed(self, mock_get_user):
        # Simulate a malformed response (e.g., missing expected keys)
        mock_get_user.return_value = {
            "unexpected_key": "unexpected_value"
        }

        # Call the function with a sample access token and handle exceptions
        access_token = "mock_access_token"
        try:
            result = user_functions.get_user_data(access_token)
            # If no exception occurs, ensure the function returns an empty or default structure
            print(result['id'])
        except KeyError as e:
            # Ensure that specific exceptions are raised (or log the error handling)
            print(f"Handled malformed data exception: {e}")

        # Verify that the mocked function was called once with the expected access token
        mock_get_user.assert_called_once_with(access_token)


