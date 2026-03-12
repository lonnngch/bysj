import os
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from .inference import VideoQualityInferenceService
from .storage import EvaluationStore

ALLOWED_EXTENSIONS = {"mp4", "avi", "mov", "mkv"}

def create_app(test_config=None):
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY="dev",
        UPLOAD_DIR=os.environ.get("UPLOAD_DIR", "uploads"),
        DB_PATH=os.environ.get("DB_PATH", "data/evaluations.db"),
        MAX_CONTENT_LENGTH=300 * 1024 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    Path(app.config["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)

    store = EvaluationStore(app.config["DB_PATH"])
    inference_service = VideoQualityInferenceService(
        checkpoint_path=os.environ.get("CHECKPOINT_PATH", "checkpoints/best_model.pth")
    )

    app.store = store
    app.inference_service = inference_service

    def _allowed(filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "engine": app.inference_service.engine,
        })

    @app.route("/api/evaluate", methods=["POST"])
    def evaluate_video():
        if "video" not in request.files:
            return jsonify({"error": "未找到视频文件字段 video"}), 400

        file = request.files["video"]
        if file.filename == "":
            return jsonify({"error": "未选择文件"}), 400

        if not _allowed(file.filename):
            return jsonify({"error": "仅支持 mp4/avi/mov/mkv"}), 400

        filename = secure_filename(file.filename)
        save_path = Path(app.config["UPLOAD_DIR"]) / filename
        file.save(save_path)

        result = app.inference_service.predict_video(str(save_path), filename)
        item_id = app.store.add(result)

        return jsonify({"id": item_id, **result})

    @app.route("/api/results")
    def list_results():
        limit = int(request.args.get("limit", 20))
        return jsonify(app.store.list(limit=limit))

    @app.route("/api/results/<int:item_id>")
    def get_result(item_id: int):
        result = app.store.get(item_id)
        if not result:
            return jsonify({"error": "记录不存在"}), 404
        return jsonify(result)

    return app