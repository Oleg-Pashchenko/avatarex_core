import unittest
import json
from app.node import app


class APITestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.data = {
            4: "Значение 4",
            5: "Значение 5"
        }

    def test_get_data(self):
        response = self.app.get('/api/data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, self.data)

    def test_add_data(self):
        new_data = {
            "id": 6,
            "value": "Значение 6"
        }
        response = self.app.post('/api/data', json=new_data)
        self.assertEqual(response.status_code, 200)
        self.data[new_data["id"]] = new_data["value"]
        response = self.app.get('/api/data')
        data = json.loads(response.data)
        self.assertEqual(data, self.data)

    def test_add_data_invalid_json(self):
        response = self.app.post('/api/data', data="Invalid JSON")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)

    def test_add_data_missing_fields(self):
        new_data = {
            "id": 7  # Нет поля "value"
        }
        response = self.app.post('/api/data', json=new_data)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn("error", data)


if __name__ == '__main__':
    unittest.main()
