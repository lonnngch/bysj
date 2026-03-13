# run_debug.py
from app.init import create_app
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)

app = create_app()

if __name__ == "__main__":
    print("启动服务器...")
    print(f"数据库路径: {app.config['DB_PATH']}")
    print(f"上传目录: {app.config['UPLOAD_DIR']}")
    print(f"模型文件: checkpoints/best_model.pth")

    app.run(host="0.0.0.0", port=8000, debug=True)