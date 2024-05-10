import unittest
from unittest.mock import patch, MagicMock
from app import app


class SpotifyOAuthTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch('app.create_spotify_oath')
    def test_login_redirect(self, mock_create_spotify_oath):
        # Mock the SpotifyOAuth object to return a test authorize URL
        mock_spotify_oath = MagicMock()
        mock_spotify_oath.get_authorize_url.return_value = "https://example.com/authorize"
        mock_create_spotify_oath.return_value = mock_spotify_oath

        response = self.client.get('/login')
        self.assertEqual(response.status_code, 302)
        self.assertIn("https://example.com/authorize", response.location)

