# tests/test_system.py
import io
import tempfile
import unittest
from pathlib import Path
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Response
from run import create_app


class SystemIntegrationTest(unittest.TestCase):
    def setUp(self):
        # 为每个测试创建独立的临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.upload_dir = os.path.join(self.temp_dir, "uploads")

        # 确保上传目录存在
        os.makedirs(self.upload_dir, exist_ok=True)

        # 创建应用实例
        self.app = create_app(
            {
                "TESTING": True,
                "DB_PATH": self.db_path,
                "UPLOAD_DIR": self.upload_dir,
            }
        )

        @self.app.route("/api/mock-html-error")
        def mock_html_error():
            return Response("<!doctype html><h1>500 Internal Server Error</h1>",
                            status=500, mimetype="text/html")

        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        # 弹出应用上下文
        self.ctx.pop()

        # 强制垃圾回收
        import gc
        gc.collect()

        # 给系统一点时间释放文件句柄
        time.sleep(0.1)

        # 清理临时目录
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"清理临时目录时出错: {e}")

    def test_health(self):
        """测试健康检查接口"""
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "ok")
        print(f"Health check: {data}")

    def test_evaluate_reject_invalid_extension(self):
        """测试拒绝无效文件扩展名"""
        data = {"video": (io.BytesIO(b"fake"), "bad.txt")}
        resp = self.client.post("/api/evaluate", data=data,
                                content_type="multipart/form-data")
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("仅支持", data["error"])

    def test_evaluate_and_query_result(self):
        """测试评估和查询结果"""

        # 创建模拟预测函数
        def mock_predict(path, filename):
            return {
                "filename": filename,
                "score": 3.8,
                "confidence": 0.9,
                "duration_sec": 3.1,
                "frame_count": 12,
                "engine": "mock",
                "created_at": "2026-01-01T00:00:00Z",
            }

        self.app.inference_service.predict_video = mock_predict

        # 测试评估接口
        data = {"video": (io.BytesIO(b"fake video content"), "demo.mp4")}
        resp = self.client.post("/api/evaluate", data=data,
                                content_type="multipart/form-data")

        self.assertEqual(resp.status_code, 200)
        payload = resp.get_json()
        self.assertIn("id", payload)
        self.assertEqual(payload["filename"], "demo.mp4")

        eval_id = payload["id"]

        # 测试列表接口
        list_resp = self.client.get("/api/results?limit=10")
        self.assertEqual(list_resp.status_code, 200)
        results = list_resp.get_json()
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)

        # 测试详情接口
        detail_resp = self.client.get(f"/api/results/{eval_id}")
        self.assertEqual(detail_resp.status_code, 200)
        detail_data = detail_resp.get_json()
        self.assertEqual(detail_data["filename"], "demo.mp4")
        self.assertEqual(detail_data["id"], eval_id)

    def test_uploaded_file_is_cleaned_after_evaluate(self):
        """测试上传文件在评估后被清理"""

        def mock_predict(path, filename):
            return {
                "filename": filename,
                "score": 3.0,
                "confidence": 0.8,
                "duration_sec": 1.0,
                "frame_count": 3,
                "engine": "mock",
                "created_at": "2026-01-01T00:00:00Z",
            }

        self.app.inference_service.predict_video = mock_predict

        uploaded_file_path = os.path.join(self.upload_dir, "cleanup.mp4")
        self.assertFalse(os.path.exists(uploaded_file_path))

        data = {"video": (io.BytesIO(b"fake video"), "cleanup.mp4")}
        resp = self.client.post("/api/evaluate", data=data,
                                content_type="multipart/form-data")

        self.assertEqual(resp.status_code, 200)

        # 检查文件是否被删除
        self.assertFalse(os.path.exists(uploaded_file_path))

    def test_evaluate_returns_json_error_when_inference_crashes(self):
        """测试推理失败时返回JSON错误"""

        def mock_predict(path, filename):
            raise ValueError("模拟推理错误")

        self.app.inference_service.predict_video = mock_predict

        data = {"video": (io.BytesIO(b"fake video"), "demo.mp4")}
        resp = self.client.post("/api/evaluate", data=data,
                                content_type="multipart/form-data")

        self.assertEqual(resp.status_code, 500)
        self.assertTrue(resp.content_type.startswith("application/json"))
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("推理失败", data["error"])

    def test_unknown_api_route_returns_json_not_html(self):
        """测试未知API路由返回JSON而不是HTML"""
        resp = self.client.get("/api/not-found")

        self.assertEqual(resp.status_code, 404)
        self.assertTrue(resp.content_type.startswith("application/json"))
        data = resp.get_json()
        self.assertIn("error", data)

    def test_non_json_api_error_is_rewritten_to_json(self):
        """测试非JSON错误响应被重写为JSON"""
        resp = self.client.get("/api/mock-html-error")

        self.assertEqual(resp.status_code, 500)
        self.assertTrue(resp.content_type.startswith("application/json"))
        data = resp.get_json()
        self.assertIn("error", data)
        self.assertIn("非JSON响应", data["error"])

    def test_results_limit_validation(self):
        """测试结果列表的limit参数验证"""
        # 测试无效的limit参数
        bad_type = self.client.get("/api/results?limit=abc")
        self.assertEqual(bad_type.status_code, 400)
        data = bad_type.get_json()
        self.assertIn("error", data)

        # 测试超出范围的limit
        out_of_range = self.client.get("/api/results?limit=999")
        self.assertEqual(out_of_range.status_code, 400)
        data = out_of_range.get_json()
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()