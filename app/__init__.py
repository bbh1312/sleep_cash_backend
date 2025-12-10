from flask import Flask
from .config import DevConfig
from .extensions import db, jwt
from .routes.auth import auth_bp
from .routes.sleep import sleep_bp
from .routes.points import points_bp
from .routes.rewards import rewards_bp
from .routes.shop import shop_bp

def create_app(config_class=DevConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    jwt.init_app(app)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(sleep_bp, url_prefix='/api/sleep')
    app.register_blueprint(points_bp, url_prefix='/api/points')
    app.register_blueprint(rewards_bp, url_prefix='/api/rewards')
    app.register_blueprint(shop_bp, url_prefix='/api/shop')

    @app.get('/health')
    def health(): return {'status': 'ok'}

    return app
