import unittest
from unittest.mock import patch, MagicMock
from src.data_collector import fetch_and_store, geocode_zip, send_info_to_analyzer

class TestDataCollector(unittest.TestCase):
    @patch('data_collector.requests.get')
    @patch('data_collector.session.add')
    @patch('data_collector.session.commit')
    def test_fetch_and_store(self, mock_commit, mock_add, mock_get):
        # Setup mock responses for the requests.get call to Google API
        mock_get.return_value.json.return_value = {
            'results': [
                {'name': 'Test Restaurant', 'vicinity': '123 Test St', 'geometry': {'location': {'lat': 40.7128, 'lng': -74.0060}}}
            ],
            'status': 'OK'
        }

        # Call the function
        fetch_and_store('10001', 1609, 'pizza')

        # Check if session.add and session.commit were called
        self.assertTrue(mock_add.called)
        self.assertTrue(mock_commit.called)

    @patch('data_collector.requests.get')
    def test_geocode_zip(self, mock_get):
        # Setup mock response for the geocode API
        mock_get.return_value.json.return_value = {
            'results': [{'geometry': {'location': {'lat': 40.7128, 'lng': -74.0060}}}],
            'status': 'OK'
        }

        # Execute the function
        lat, lng = geocode_zip('10001')

        # Assert the correct values are returned
        self.assertEqual(lat, 40.7128)
        self.assertEqual(lng, -74.0060)

    @patch('data_collector.pika.BlockingConnection')
    def test_send_info_to_analyzer(self, mock_connection):
        # Mock the connection and channel
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        # Execute the function
        send_info_to_analyzer('10001', 1609, 'pizza')

        # Assert that the message was published
        mock_channel.basic_publish.assert_called_once()

if __name__ == '__main__':
    unittest.main()
