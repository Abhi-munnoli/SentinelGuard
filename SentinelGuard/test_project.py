import unittest
from app import app, parse_transaction

class SentinelGuardTests(unittest.TestCase):
    def test_parse_defaults_and_values(self):
        item = parse_transaction({"amount": "500", "hour": "12"})
        self.assertEqual(item["amount"], 500.0)
        self.assertEqual(item["hour"], 12)
        self.assertIn("merchant_risk", item)

    def test_invalid_hour(self):
        with self.assertRaises(ValueError):
            parse_transaction({"hour": "30"})

    def test_health_endpoint(self):
        client = app.test_client()
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "running")

if __name__ == "__main__":
    unittest.main()
