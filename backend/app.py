import logging
from urllib.parse import urlsplit, urlunsplit

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from routes.auth_routes import auth_bp
from routes.analysis_routes import analysis_bp
from routes.dashboard_routes import dashboard_bp
from routes.assistant_routes import assistant_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    frontend_origin = app.config["FRONTEND_ORIGIN"]
    allowed_origins = {frontend_origin}
    parsed_origin = urlsplit(frontend_origin)
    if parsed_origin.hostname in {"localhost", "127.0.0.1"}:
        alias = "127.0.0.1" if parsed_origin.hostname == "localhost" else "localhost"
        netloc = f"{alias}:{parsed_origin.port}" if parsed_origin.port else alias
        allowed_origins.add(urlunsplit((parsed_origin.scheme, netloc, "", "", "")))
    CORS(app, origins=sorted(allowed_origins))
    app.register_blueprint(auth_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assistant_bp)

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify({"status": "error", "message": "Upload exceeds the 5 MB limit"}), 413

    @app.errorhandler(500)
    def server_error(error):
        logging.getLogger(__name__).exception("Unhandled request error", exc_info=error)
        return jsonify({"status": "error", "message": "An unexpected server error occurred"}), 500

    @app.route("/")
    def home():
        return jsonify({"status": "success", "message": "CyberSahak backend is running"})

    @app.route("/api/health")
    def health():
        return jsonify({"status": "success", "message": "CyberSahak API is healthy"})

    return app


app = create_app()

if __name__ == "__main__":
    Config.validate()
    app.run(debug=False)
