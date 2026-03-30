"""
Flask application factory.
"""
import os
from flask import Flask
from flask_cors import CORS
from .services.rgs_validation_service import RgsValidationError

from .routes.dashboard import dashboard_bp
from .routes.relaties import relaties_bp
from .routes.artikelen import artikelen_bp
from .routes.verkoopfacturen import verkoopfacturen_bp
from .routes.inkoopfacturen import inkoopfacturen_bp
from .routes.kasboek import kasboek_bp
from .routes.activa import activa_bp
from .routes.platform import platform_bp
from .routes.btw import btw_bp
from .routes.export import export_bp
from .routes.instellingen import instellingen_bp


def create_app(db_path: str) -> Flask:
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_url_path="",
    )
    app.config["DB_PATH"] = db_path
    app.config["EXPORT_DIR"] = os.path.join(os.path.dirname(__file__), "..", "exports")
    app.config["CONFIG_DIR"] = os.path.join(os.path.dirname(__file__), "..", "config")

    CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:5000"}})

    # Register all blueprints
    app.register_blueprint(dashboard_bp,        url_prefix="/api/dashboard")
    app.register_blueprint(relaties_bp,         url_prefix="/api/relaties")
    app.register_blueprint(artikelen_bp,        url_prefix="/api/artikelen")
    app.register_blueprint(verkoopfacturen_bp,  url_prefix="/api/verkoopfacturen")
    app.register_blueprint(inkoopfacturen_bp,   url_prefix="/api/inkoopfacturen")
    app.register_blueprint(kasboek_bp,          url_prefix="/api/kasboek")
    app.register_blueprint(activa_bp,           url_prefix="/api/activa")
    app.register_blueprint(platform_bp,         url_prefix="/api/platform")
    app.register_blueprint(btw_bp,              url_prefix="/api/btw")
    app.register_blueprint(export_bp,           url_prefix="/api/export")
    app.register_blueprint(instellingen_bp,     url_prefix="/api/instellingen")

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.errorhandler(RgsValidationError)
    def handle_rgs_validation_error(exc: RgsValidationError):
        return {
            "error": "RGS_VALIDATION_FAILED",
            "code": exc.code,
            "message": exc.message,
            "details": exc.details or [],
        }, 400

    return app
