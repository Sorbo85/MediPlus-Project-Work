import unittest
import tempfile
import os
import app as application

class MediPlusAPITest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.tmp.close()
        self.old_db = application.DB_PATH
        application.DB_PATH = application.Path(self.tmp.name)
        application.init_db()
        application.app.config["TESTING"] = True
        self.client = application.app.test_client()

    def tearDown(self):
        application.DB_PATH = self.old_db
        os.unlink(self.tmp.name)

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")

    def test_list_doctors(self):
        response = self.client.get("/api/doctors")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json), 1)

    def test_create_requires_fields(self):
        response = self.client.post("/api/appointments", json={})
        self.assertEqual(response.status_code, 400)

    def test_invalid_status(self):
        response = self.client.patch("/api/appointments/1", json={"status":"Altro"})
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
