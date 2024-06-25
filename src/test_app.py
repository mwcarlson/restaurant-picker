import sys
import os
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

import unittest
from unittest.mock import patch
from flask import url_for
from flask_testing import TestCase

class TestFlaskApp(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        return app

    def test_index_get(self):
        response = self.client.get(url_for('index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Find Restaurants', response.data)

    def test_index_post(self):
        with patch('app.send_preferences') as mock_send_preferences:
            response = self.client.post(url_for('index'), data={
                'zip': '10001',
                'distance': '5',
                'keyword': 'Italian'
            }, follow_redirects=True)
            mock_send_preferences.assert_called_once_with('10001', 8046.7, 'Italian')
            self.assertEqual(response.status_code, 200)

    def test_results(self):
        with patch('app.latest_restaurant_data', return_value={'name': 'Pizza Place', 'address': '123 Main St'}):
            response = self.client.get(url_for('results'))
            self.assertIn(b'Pizza Place', response.data)
            self.assertIn(b'123 Main St', response.data)

    def test_fetch_data_success(self):
        with patch('app.latest_restaurant_data', return_value={'name': 'Pizza Place'}):
            response = self.client.get(url_for('fetch_data'))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Pizza Place', response.data)

    def test_fetch_data_failure(self):
        with patch('app.latest_restaurant_data', return_value=None):
            response = self.client.get(url_for('fetch_data'))
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'No data available yet.', response.data)

# Run the tests
if __name__ == '__main__':
    unittest.main()
