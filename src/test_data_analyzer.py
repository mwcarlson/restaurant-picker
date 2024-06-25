import unittest
import json
import pika
from unittest.mock import patch, MagicMock
from data_analyzer import select_random_restaurant, callback, send_result_to_frontend


class TestDataAnalyzer(unittest.TestCase):
    @patch('data_analyzer.session.execute')
    def test_select_random_restaurant(self, mock_execute):
        # Setup a mock restaurant
        mock_restaurant = MagicMock()
        mock_restaurant.name = "Test Restaurant"
        mock_restaurant.address = "123 Test St"
        mock_restaurant.latitude = 40.7128
        mock_restaurant.longitude = -74.0060
        mock_restaurant.zip = "10001"
        mock_restaurant.distance = 1609
        mock_restaurant.keyword = "pizza"

        # Configure the mock to return a mock restaurant
        mock_execute.return_value.scalars.return_value.first.return_value = mock_restaurant

        # Execute the function
        result = select_random_restaurant("10001", 1609, "pizza")

        # Check that the result is as expected
        self.assertEqual(result.name, "Test Restaurant")
        self.assertEqual(result.address, "123 Test St")

    @patch('data_analyzer.json.loads')
    @patch('data_analyzer.select_random_restaurant')
    @patch('data_analyzer.send_result_to_frontend')
    def test_callback(self, mock_send_result, mock_select_random, mock_json_loads):
        # Setup
        mock_json_loads.return_value = {'zip': '10001', 'distance': 1609, 'keyword': 'pizza'}
        mock_restaurant = MagicMock()
        mock_restaurant.name = "Test Restaurant"
        mock_restaurant.address = "123 Test St"
        mock_restaurant.latitude = 40.7128
        mock_restaurant.longitude = -74.0060
        mock_select_random.return_value = mock_restaurant

        # Simulate receiving a message
        callback(None, None, None, json.dumps({'zip': '10001', 'distance': 1609, 'keyword': 'pizza'}))

        # Ensure send_result_to_frontend was called with correct data
        mock_send_result.assert_called_once_with(json.dumps({
            'name': 'Test Restaurant',
            'address': '123 Test St',
            'latitude': 40.7128,
            'longitude': -74.0060
        }))

    @patch('data_analyzer.channel.basic_publish')
    def test_send_result_to_frontend(self, mock_publish):
        message = json.dumps({
            'name': 'Test Restaurant',
            'address': '123 Test St',
            'latitude': 40.7128,
            'longitude': -74.0060
        })
        send_result_to_frontend(message)

        # Check if the message was published to RabbitMQ
        mock_publish.assert_called_once_with(
            exchange='',
            routing_key='frontend_queue',
            body=message,
            properties=pika.BasicProperties(delivery_mode=2, )
        )


if __name__ == '__main__':
    unittest.main()
