import io
import tempfile
import unittest

from run import create_app


class SystemIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = f"{self.temp_dir.name}/test.db"
        self.upload_dir = f"{self.temp_dir.name}/uploads"

        app = create_app(
            {
                "TESTING": True,
                "DB_PATH": self.db_path,
                "UPLOAD_DIR": self.upload_dir,
            }
        )

        self.client = app.test_client()
        self.app = app

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_health(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("status", resp.get_json())

    def test_evaluate_reject_invalid_extension(self):
        resp = self.client.post(
            "/api/evaluate",
            data={"video": (io.BytesIO(b"fake"), "bad.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 400)

    def test_evaluate_and_query_result(self):
        self.app.inference_service.predict_video = lambda path, filename: {
            "filename": filename,
            "score": 3.8,
            "confidence": 0.9,
            "duration_sec": 3.1,
            "frame_count": 12,
            "engine": "mock",
            "created_at": "2026-01-01T00:00:00Z",
        }

        resp = self.client.post(
            "/api/evaluate",
            data={"video": (io.BytesIO(b"00fakevideo"), "demo.mp4")},
            content_type="multipart/form-data",
        )

        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertIn("id", payload)

        list_resp = self.client.get("/api/results")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(len(list_resp.get_json()), 1)

        detail_resp = self.client.get(f"/api/results/{payload['id']}")
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.get_json()["filename"], "demo.mp4")


if __name__ == "__main__":
    unittest.main()
