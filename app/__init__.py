# app/__init__.py
from flask import Flask, request
from flask_compress import Compress
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    Compress(app)

    # 위에서 만든 routes.py의 Blueprint 등록
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    @app.after_request
    def add_header(response):
        if request.path.startswith('/static'):
            response.cache_control.max_age = 86400
            response.cache_control.public = True
        return response

    return app

# gunicorn에서 사용할 app 객체 생성
app = create_app()