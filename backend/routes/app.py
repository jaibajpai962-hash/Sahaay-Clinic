"""
FILE: backend/app.py
Flask Application Factory

ENTRY POINT of the Flask backend.

Development:
    python app.py

Production:
    gunicorn --bind 0.0.0.0:5000 --workers 4 "app:create_app()"
"""

import logging
import logging.handlers
import os

from datetime import timedelta

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager


def create_app() -> Flask:
    """
    Build and configure the Flask application.
    Returns the Flask app instance.
    """

    # ============================================================
    # 0. LOAD CONFIGURATION
    # ============================================================

    from config import config

    # ============================================================
    # 1. CREATE FLASK APPLICATION
    # ============================================================

    # backend/
    # ├── app.py
    # ├── database.py
    # ├── config.py
    # └── ...
    #
    # frontend is assumed to be one directory above backend.

    frontend_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

    app = Flask(
        __name__,
        static_folder=frontend_dir,
        static_url_path=""
    )

    # ============================================================
    # 2. FLASK CONFIGURATION
    # ============================================================

    app.config["SECRET_KEY"] = config.SECRET_KEY

    # JWT configuration
    app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY

    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
        minutes=config.JWT_ACCESS_TOKEN_EXPIRES_MINUTES
    )

    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(
        days=config.JWT_REFRESH_TOKEN_EXPIRES_DAYS
    )

    app.config["DEBUG"] = config.DEBUG

    # IMPORTANT:
    # No SQLALCHEMY_DATABASE_URI
    # No SQLALCHEMY_TRACK_MODIFICATIONS
    # No SQLALCHEMY_ECHO
    #
    # Database is handled by mysql.connector in database.py.

    # ============================================================
    # 3. LOGGING
    # ============================================================

    _setup_logging(app, config)

    # ============================================================
    # 4. VALIDATE CONFIGURATION
    # ============================================================

    config.validate()

    # ============================================================
    # 5. CORS
    # ============================================================

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": config.CORS_ORIGINS
            }
        },
        methods=config.CORS_METHODS,
        supports_credentials=True
    )

    # ============================================================
    # 6. JWT
    # ============================================================

    jwt = JWTManager(app)

    # ------------------------------------------------------------
    # JWT ERROR HANDLERS
    # ------------------------------------------------------------

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "success": False,
            "message": "Token has expired. Please log in again."
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "success": False,
            "message": "Invalid token."
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "success": False,
            "message": "Authorization token required."
        }), 401

    # ============================================================
    # 7. INITIALISE MYSQL DATABASE
    # ============================================================

    #
    # database.py now uses mysql.connector.
    #
    # init_db() will:
    #   1. Register Flask DB cleanup
    #   2. Connect to MySQL
    #   3. Create required tables
    #   4. Test SELECT 1
    #

    from database import init_db

    init_db(app)

    # ============================================================
    # 8. REGISTER API BLUEPRINTS
    # ============================================================

    from routes.auth import auth_bp
    from routes.patients import patients_bp
    from routes.assessment import assessment_bp
    from routes.sync import sync_bp
    from routes.doctor import doctor_bp
    from routes.teleconsult import teleconsult_bp
    from routes.doctor_profile import doctor_profile_bp, create_doctor_profiles_table
    from routes.firstaid_ai import firstaid_ai_bp

    API_PREFIX = "/api/v1"

    app.register_blueprint(
        auth_bp,
        url_prefix=f"{API_PREFIX}/auth"
    )

    app.register_blueprint(
        patients_bp,
        url_prefix=f"{API_PREFIX}/patients"
    )

    app.register_blueprint(
        assessment_bp,
        url_prefix=f"{API_PREFIX}"
    )

    app.register_blueprint(
        sync_bp,
        url_prefix=f"{API_PREFIX}/sync"
    )

    app.register_blueprint(
        doctor_bp,
        url_prefix=f"{API_PREFIX}/doctor"
    )

    app.register_blueprint(
        doctor_profile_bp,
        url_prefix=f"{API_PREFIX}/doctor"
    )

    app.register_blueprint(
        teleconsult_bp,
        url_prefix=f"{API_PREFIX}/teleconsult"
    )

    app.register_blueprint(
        firstaid_ai_bp,
        url_prefix=f"{API_PREFIX}/firstaid"
    )

    # Create extra tables for doctor profiles + reset tokens
    try:
        create_doctor_profiles_table()
    except Exception as _exc:
        app.logger.warning("Doctor profile table init: %s", _exc)

    # ============================================================
    # 9. FRONTEND / SPA ROUTING
    # ============================================================

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        """
        Serve frontend files.

        Examples:
            /index.html
            /css/style.css
            /js/app.js

        Unknown frontend routes fall back to index.html.
        """

        from flask import send_from_directory

        target = os.path.join(
            app.static_folder,
            path
        )

        # Prevent invalid path traversal
        target = os.path.abspath(target)

        if (
            path
            and target.startswith(os.path.abspath(app.static_folder))
            and os.path.isfile(target)
        ):
            return send_from_directory(
                app.static_folder,
                path
            )

        return send_from_directory(
            app.static_folder,
            "index.html"
        )

    # ============================================================
    # 10. GLOBAL ERROR HANDLERS
    # ============================================================

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "Endpoint not found."
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "message": "Method not allowed."
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(
            "Internal server error: %s",
            error
        )

        return jsonify({
            "success": False,
            "message": "Internal server error."
        }), 500

    # ============================================================
    # STARTUP MESSAGE
    # ===========================
    # =================================

    app.logger.info(
        "Sahaay Clinic backend started — %s",
        config.CLINIC_NAME
    )

    return app


# ================================================================
# LOGGING SETUP
# ================================================================

def _setup_logging(app: Flask, config) -> None:
    """
    Configure application logging.
    """

    log_level = getattr(
        logging,
        config.LOG_LEVEL,
        logging.INFO
    )

    # ------------------------------------------------------------
    # Console logging
    # ------------------------------------------------------------

    logging.basicConfig(
        level=log_level,
        format=(
            "%(asctime)s "
            "[%(levelname)s] "
            "%(name)s: "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ------------------------------------------------------------
    # File logging
    # ------------------------------------------------------------

    if config.LOG_FILE:

        log_dir = os.path.dirname(
            config.LOG_FILE
        )

        if log_dir:
            os.makedirs(
                log_dir,
                exist_ok=True
            )

        file_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=config.LOG_MAX_BYTES,
            backupCount=config.LOG_BACKUP_COUNT
        )

        file_handler.setLevel(log_level)

        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s "
                "[%(levelname)s] "
                "%(name)s: "
                "%(message)s"
            )
        )

        logging.getLogger().addHandler(
            file_handler
        )

    app.logger.setLevel(log_level)


# ================================================================
# APPLICATION ENTRY POINT
# ================================================================

if __name__ == "__main__":

    from config import config as cfg

    app = create_app()

    app.run(
        host=cfg.HOST,
        port=cfg.PORT,
        debug=cfg.DEBUG
    )