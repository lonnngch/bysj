# app/__init__.py
import os
import sys
from pathlib import Path
from werkzeug.exceptions import HTTPException
from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

# 切换回原来的推理服务
from app.inference import VideoQualityInferenceService
from app.storage import EvaluationStore

ALLOWED_EXTENSIONS = {"mp4", "avi", "mov", "mkv"}


def create_app(test_config=None):
    # 创建Flask应用，指定模板和静态文件夹路径
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # 默认配置
    app.config.update(
        SECRET_KEY="dev",
        UPLOAD_DIR=os.environ.get("UPLOAD_DIR", "uploads"),
        DB_PATH=os.environ.get("DB_PATH", "data/evaluations.db"),
        MAX_CONTENT_LENGTH=300 * 1024 * 1024,  # 300MB
    )

    # 如果提供了测试配置，更新配置
    if test_config:
        app.config.update(test_config)

    # 确保上传目录存在
    Path(app.config["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)

    # 初始化存储服务
    store = EvaluationStore(app.config["DB_PATH"])

    # 检查模型文件是否存在
    checkpoint_path = os.environ.get("CHECKPOINT_PATH", "checkpoints/best_model.pth")
    if not os.path.exists(checkpoint_path):
        app.logger.warning(f"模型文件 {checkpoint_path} 不存在，将使用启发式引擎")
    else:
        app.logger.info(f"模型文件存在: {checkpoint_path}")

    # 初始化推理服务 - 使用原来的服务
    try:
        inference_service = VideoQualityInferenceService(
            checkpoint_path=checkpoint_path
        )
        app.logger.info(f"推理服务初始化成功，引擎: {inference_service.engine}")
    except Exception as e:
        app.logger.error(f"推理服务初始化失败: {e}")
        import traceback
        traceback.print_exc()
        # 如果初始化失败，使用一个简单的回退服务
        from app.debug_inference import DebugInferenceService
        inference_service = DebugInferenceService(checkpoint_path=checkpoint_path)
        app.logger.info(f"使用调试服务作为回退，引擎: {inference_service.engine}")

    # 将服务附加到app实例
    app.store = store
    app.inference_service = inference_service

    def _allowed(filename: str) -> bool:
        """检查文件扩展名是否允许"""
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    def _is_api_request() -> bool:
        """判断是否为API请求"""
        return request.path.startswith("/api/")

    # 错误处理
    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        """处理HTTP异常"""
        app.logger.error(f"HTTP Exception {err.code}: {err.description}")

        # 非API请求返回默认错误页面
        if not _is_api_request():
            return render_template('error.html', error=str(err.description)), err.code

        # API请求返回JSON格式错误
        return jsonify({"error": err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(err: Exception):
        """处理未预期的异常"""
        app.logger.exception("未处理的异常", exc_info=err)

        # 非API请求返回错误页面
        if not _is_api_request():
            return render_template('error.html', error=f"服务器内部错误: {str(err)}"), 500

        # API请求返回JSON格式错误
        return jsonify({"error": f"服务器内部错误: {str(err)}"}), 500

    @app.after_request
    def ensure_api_errors_are_json(resp):
        """确保API错误返回JSON格式"""
        # 只处理API请求的错误响应
        if not _is_api_request() or resp.status_code < 400:
            return resp

        # 如果已经是JSON，直接返回
        content_type = (resp.content_type or "").lower()
        if "application/json" in content_type:
            return resp

        # 获取响应内容
        body = resp.get_data(as_text=True) or ""
        # 压缩空白字符，提取前160个字符
        compact = " ".join(body.split())
        excerpt = compact[:160] + ("..." if len(compact) > 160 else "") if compact else "未知错误"

        # 创建JSON响应
        payload = {"error": f"服务返回了非JSON响应: {excerpt}"}
        response = jsonify(payload)
        response.status_code = resp.status_code
        return response

    @app.route("/")
    def index():
        """首页"""
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        """健康检查接口"""
        return jsonify({
            "status": "ok",
            "engine": app.inference_service.engine,
            "model_exists": os.path.exists(app.inference_service.checkpoint_path)
        })

    @app.route("/api/debug-info")
    def debug_info():
        """调试信息接口"""
        info = {
            "python_version": sys.version,
            "cwd": os.getcwd(),
            "upload_dir": {
                "path": app.config["UPLOAD_DIR"],
                "exists": os.path.exists(app.config["UPLOAD_DIR"]),
                "writable": os.access(app.config["UPLOAD_DIR"], os.W_OK) if os.path.exists(
                    app.config["UPLOAD_DIR"]) else False
            },
            "db_path": {
                "path": app.config["DB_PATH"],
                "exists": os.path.exists(app.config["DB_PATH"]),
                "parent_exists": os.path.exists(os.path.dirname(app.config["DB_PATH"]))
            },
            "model": {
                "path": str(app.inference_service.checkpoint_path),
                "exists": os.path.exists(app.inference_service.checkpoint_path),
                "engine": app.inference_service.engine
            },
            "max_content_length": app.config["MAX_CONTENT_LENGTH"]
        }
        return jsonify(info)

    @app.route("/api/evaluate", methods=["POST"])
    def evaluate_video():
        """视频评估接口"""
        save_path = None
        try:
            print("\n" + "=" * 60)
            print("开始处理评估请求")
            print("=" * 60)

            # 检查文件
            if "video" not in request.files:
                print("错误: 没有video字段")
                return jsonify({"error": "未找到视频文件字段 video"}), 400

            file = request.files["video"]
            print(f"收到文件: {file.filename}")

            if file.filename == "":
                print("错误: 文件名为空")
                return jsonify({"error": "未选择文件"}), 400

            # 检查文件扩展名
            if not _allowed(file.filename):
                print(f"错误: 不允许的扩展名 {file.filename}")
                return jsonify({"error": "仅支持 mp4/avi/mov/mkv 格式"}), 400

            # 安全处理文件名
            filename = secure_filename(file.filename)
            save_path = Path(app.config["UPLOAD_DIR"]) / filename
            print(f"保存路径: {save_path}")

            # 保存上传的文件
            file.save(save_path)
            file_size = save_path.stat().st_size
            print(f"文件已保存, 大小: {file_size} 字节 ({file_size / 1024 / 1024:.2f} MB)")

            # 执行推理
            print("开始推理...")
            print(f"使用引擎: {app.inference_service.engine}")

            try:
                result = app.inference_service.predict_video(str(save_path), filename)
                print(f"推理完成: {result}")
            except Exception as err:
                print(f"推理失败: {err}")
                import traceback
                traceback.print_exc()
                return jsonify({"error": f"推理失败: {str(err)}"}), 500
            finally:
                # 清理上传的临时文件
                if save_path and save_path.exists():
                    try:
                        save_path.unlink()
                        print(f"临时文件已删除: {save_path}")
                    except Exception as e:
                        print(f"删除临时文件失败: {e}")

            # 保存结果到数据库
            print("保存到数据库...")
            try:
                item_id = app.store.add(result)
                result["id"] = item_id
                print(f"数据库保存成功, ID: {item_id}")
            except Exception as e:
                print(f"数据库保存失败: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({"error": f"保存结果失败: {str(e)}"}), 500

            print("=" * 60)
            print("处理完成")
            print("=" * 60)

            return jsonify(result)

        except Exception as e:
            print(f"未处理的异常: {e}")
            import traceback
            traceback.print_exc()

            # 确保清理临时文件
            if save_path and save_path.exists():
                try:
                    save_path.unlink()
                    print(f"异常后清理临时文件: {save_path}")
                except:
                    pass

            return jsonify({"error": f"处理失败: {str(e)}"}), 500

    @app.route("/api/results")
    def list_results():
        """获取评估结果列表"""
        try:
            # 获取并验证limit参数
            limit_str = request.args.get("limit", "20")
            try:
                limit = int(limit_str)
                if limit < 1 or limit > 100:
                    return jsonify({"error": "limit 参数必须在 1-100 之间"}), 400
            except ValueError:
                return jsonify({"error": "limit 参数必须是整数"}), 400

            # 从数据库获取结果列表
            results = app.store.list(limit=limit)
            return jsonify(results)

        except Exception as e:
            app.logger.exception("获取结果列表失败")
            return jsonify({"error": f"获取结果失败: {str(e)}"}), 500

    @app.route("/api/results/<int:item_id>")
    def get_result(item_id: int):
        """获取单个评估结果"""
        try:
            # 从数据库获取结果
            result = app.store.get(item_id)
            if not result:
                return jsonify({"error": "记录不存在"}), 404
            return jsonify(result)

        except Exception as e:
            app.logger.exception("获取结果详情失败")
            return jsonify({"error": f"获取结果失败: {str(e)}"}), 500

    # 添加一个简单的错误页面模板
    @app.route("/error")
    def error_page():
        """错误页面"""
        error = request.args.get("error", "未知错误")
        return render_template("error.html", error=error)

    return app