import unittest
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_home(self):
        response = self.app.get('/')
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'running')
        self.assertEqual(response.status_code, 200)

    def test_health(self):
        response = self.app.get('/health')
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(response.status_code, 200)

    def test_status(self):
        response = self.app.get('/api/status')
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(response.status_code, 200)

    def test_ad_stats(self):
        response = self.app.get('/api/ad/123/stats')
        data = json.loads(response.data)
        self.assertEqual(data['ad_id'], '123')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
