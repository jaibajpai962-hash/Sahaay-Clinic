"""
FILE: backend/config.py

Centralised Configuration Loader

Loads configuration from the project's .env file.

Database:
    Uses mysql.connector.
    No SQLAlchemy configuration is required.

Usage:
    from config import config

    print(config.DB_HOST)
    print(config.DB_PORT)
    print(config.DB_NAME)
"""

import os
import sys
import logging

from dotenv import load_dotenv


# ================================================================
# PROJECT / .ENV LOCATION
# ================================================================

# backend/config.py
#        ↓
# backend/
#        ↓
# project root/
#        ↓
# .env

_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

_ENV_FILE = os.path.join(
    _PROJECT_ROOT,
    ".env"
)

load_dotenv(_ENV_FILE)


# ================================================================
# CONFIGURATION
# ================================================================

class Config:
    """
    Central application configuration.

    All environment variables are loaded and converted
    to their appropriate Python types here.
    """

    # ============================================================
    # FLASK CORE
    # ============================================================

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "dev-fallback-secret-CHANGE-ME"
    )

    FLASK_ENV: str = os.getenv(
        "FLASK_ENV",
        "development"
    )

    DEBUG: bool = (
        os.getenv("FLASK_DEBUG", "1") == "1"
    )

    HOST: str = os.getenv(
        "FLASK_HOST",
        "0.0.0.0"
    )

    PORT: int = int(
        os.getenv("FLASK_PORT", "5000")
    )


    # ============================================================
    # MYSQL DATABASE
    # ============================================================

    # These values are used by database.py:
    #
    # mysql.connector.connect(
    #     host=DB_HOST,
    #     port=DB_PORT,
    #     user=DB_USER,
    #     password=DB_PASSWORD,
    #     database=DB_NAME
    # )

    # ============================================================================
# MYSQL DATABASE
# ============================================================================

    MYSQL_HOST: str = os.getenv(
        "MYSQL_HOST",
        "localhost"
    )

    MYSQL_PORT: int = int(
        os.getenv(
            "MYSQL_PORT",
            "3306"
        )
    )

    MYSQL_USER: str = os.getenv(
        "MYSQL_USER",
        "root"
    )

    MYSQL_PASSWORD: str = os.getenv(
        "MYSQL_PASSWORD",
        ""
    )

    MYSQL_DATABASE: str = os.getenv(
        "MYSQL_DATABASE",
        "sahaay_clinic"
    )


# Backwards-compatible aliases expected by some modules
    DB_HOST = MYSQL_HOST
    DB_PORT = MYSQL_PORT
    DB_USER = MYSQL_USER
    DB_PASSWORD = MYSQL_PASSWORD
    DB_NAME = MYSQL_DATABASE


    # ============================================================
    # JWT AUTHENTICATION
    # ============================================================

    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        SECRET_KEY
    )

    JWT_ACCESS_TOKEN_EXPIRES_MINUTES: int = int(
        os.getenv(
            "JWT_ACCESS_TOKEN_EXPIRES_MINUTES",
            "1440"
        )
    )

    JWT_REFRESH_TOKEN_EXPIRES_DAYS: int = int(
        os.getenv(
            "JWT_REFRESH_TOKEN_EXPIRES_DAYS",
            "365"
        )
    )


    # ============================================================
    # GEMINI API — PRIMARY AI ENGINE
    # ============================================================

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "models/gemini-3.1-flash-lite")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))
    GEMINI_MAX_TOKENS: int = int(os.getenv("GEMINI_MAX_TOKENS", "800"))
    GEMINI_TIMEOUT: int = int(os.getenv("GEMINI_TIMEOUT", "45"))


    # ============================================================
    # TWILIO SMS
    # ============================================================

    TWILIO_ACCOUNT_SID: str = os.getenv(
        "TWILIO_ACCOUNT_SID",
        ""
    )

    TWILIO_AUTH_TOKEN: str = os.getenv(
        "TWILIO_AUTH_TOKEN",
        ""
    )

    TWILIO_PHONE_NUMBER: str = os.getenv(
        "TWILIO_PHONE_NUMBER",
        ""
    )

    SMS_TEMPLATE: str = os.getenv(
        "SMS_TEMPLATE",
        "Sahaay Clinic: Dear {name}, {message}"
    )

    SMS_ENABLED: bool = bool(
        TWILIO_ACCOUNT_SID
        and TWILIO_AUTH_TOKEN
        and TWILIO_PHONE_NUMBER
    )


    # ============================================================
    # CORS
    # ============================================================

    CORS_ORIGINS: list = os.getenv(
        "CORS_ORIGINS",
        "*"
    ).split(",")

    CORS_METHODS: list = os.getenv(
        "CORS_METHODS",
        "GET,POST,PUT,DELETE,OPTIONS"
    ).split(",")


    # ============================================================
    # RATE LIMITING
    # ============================================================

    RATE_LIMIT_PER_MINUTE: int = int(
        os.getenv(
            "RATE_LIMIT_PER_MINUTE",
            "60"
        )
    )

    LOGIN_MAX_ATTEMPTS: int = int(
        os.getenv(
            "LOGIN_MAX_ATTEMPTS",
            "5"
        )
    )

    LOGIN_LOCKOUT_MINUTES: int = int(
        os.getenv(
            "LOGIN_LOCKOUT_MINUTES",
            "15"
        )
    )


    # ============================================================
    # LOGGING
    # ============================================================

    LOG_LEVEL: str = os.getenv(
        "LOG_LEVEL",
        "INFO"
    ).upper()

    LOG_FILE: str = os.getenv(
        "LOG_FILE",
        ""
    )

    LOG_MAX_BYTES: int = int(
        os.getenv(
            "LOG_MAX_BYTES",
            str(10 * 1024 * 1024)
        )
    )

    LOG_BACKUP_COUNT: int = int(
        os.getenv(
            "LOG_BACKUP_COUNT",
            "5"
        )
    )


    # ============================================================
    # SMTP EMAIL
    # ============================================================

    SMTP_HOST: str = os.getenv(
        "SMTP_HOST",
        "smtp.gmail.com"
    )

    SMTP_PORT: int = int(
        os.getenv(
            "SMTP_PORT",
            "587"
        )
    )

    SMTP_USER: str = os.getenv(
        "SMTP_USER",
        ""
    )

    SMTP_PASSWORD: str = os.getenv(
        "SMTP_PASSWORD",
        ""
    )

    SMTP_FROM: str = os.getenv(
        "SMTP_FROM",
        "noreply@sahaay-clinic.example.com"
    )

    SMTP_ENABLED: bool = bool(
        os.getenv("SMTP_USER", "")
        and os.getenv("SMTP_PASSWORD", "")
    )


    # ============================================================
    # CLOUDINARY (media storage)
    # ============================================================

    CLOUDINARY_CLOUD_NAME: str = os.getenv(
        "CLOUDINARY_CLOUD_NAME",
        ""
    )

    CLOUDINARY_API_KEY: str = os.getenv(
        "CLOUDINARY_API_KEY",
        ""
    )

    CLOUDINARY_API_SECRET: str = os.getenv(
        "CLOUDINARY_API_SECRET",
        ""
    )

    CLOUDINARY_ENABLED: bool = bool(
        os.getenv("CLOUDINARY_CLOUD_NAME", "")
        and os.getenv("CLOUDINARY_API_KEY", "")
        and os.getenv("CLOUDINARY_API_SECRET", "")
    )


    # ============================================================
    # APPLICATION BASE URL (for password-reset links in emails)
    # ============================================================

    APP_BASE_URL: str = os.getenv(
        "APP_BASE_URL",
        "http://localhost:5000"
    )


    # ============================================================
    # TELECONSULT
    # ============================================================

    TELECONSULT_PROVIDER: str = os.getenv(
        "TELECONSULT_PROVIDER",
        "jitsi"
    )

    JITSI_BASE_URL: str = os.getenv(
        "JITSI_BASE_URL",
        "https://meet.jit.si"
    )


    # ============================================================
    # CLINIC SETTINGS
    # ============================================================

    CLINIC_NAME: str = os.getenv(
        "CLINIC_NAME",
        "Sahaay Clinic"
    )

    CLINIC_DISTRICT_CODE: str = os.getenv(
        "CLINIC_DISTRICT_CODE",
        "MH"
    )

    ADMIN_EMAIL: str = os.getenv(
        "ADMIN_EMAIL",
        ""
    )

    QUEUE_HISTORY_DAYS: int = int(
        os.getenv(
            "QUEUE_HISTORY_DAYS",
            "1"
        )
    )

    DEFAULT_PAGE_SIZE: int = int(
        os.getenv(
            "DEFAULT_PAGE_SIZE",
            "50"
        )
    )

    MAX_PAGE_SIZE: int = int(
        os.getenv(
            "MAX_PAGE_SIZE",
            "200"
        )
    )


    # ============================================================
    # CONFIGURATION VALIDATION
    # ============================================================

    @classmethod
    def validate(cls) -> None:
        """
        Validate application configuration at startup.
        """

        errors = []
        warnings = []

        # --------------------------------------------------------
        # SECRET KEY
        # --------------------------------------------------------

        if cls.SECRET_KEY in (
            "",
            "dev-fallback-secret-CHANGE-ME",
            "change-me-to-a-long-random-string-before-deploying"
        ):

            if cls.FLASK_ENV == "production":

                errors.append(
                    "SECRET_KEY must be set to a strong random "
                    "value in production.\n"
                    "Run:\n"
                    "python -c "
                    "\"import secrets; "
                    "print(secrets.token_hex(32))\""
                )

            else:

                warnings.append(
                    "SECRET_KEY is using the insecure development "
                    "default."
                )


        # --------------------------------------------------------
        # DATABASE
        # --------------------------------------------------------

        if not cls.DB_HOST:
            errors.append(
                "DB_HOST is not configured."
            )

        if not cls.DB_USER:
            errors.append(
                "DB_USER is not configured."
            )

        if not cls.DB_NAME:
            errors.append(
                "DB_NAME is not configured."
            )


        # --------------------------------------------------------
        # GEMINI
        # --------------------------------------------------------

        if not cls.GEMINI_API_KEY:
            warnings.append(
                "GEMINI_API_KEY is not set. AI features will use the rule-based fallback."
            )


        # --------------------------------------------------------
        # TWILIO
        # --------------------------------------------------------

        if not cls.SMS_ENABLED:

            warnings.append(
                "Twilio SMS is disabled. "
                "Patient SMS alerts will not be sent."
            )


        # --------------------------------------------------------
        # LOGGING
        # --------------------------------------------------------

        logger = logging.getLogger(
            "sahaay.config"
        )


        for warning in warnings:

            logger.warning(
                "CONFIG WARNING: %s",
                warning
            )


        for error in errors:

            logger.critical(
                "CONFIG ERROR: %s",
                error
            )


        # --------------------------------------------------------
        # STOP APPLICATION ON CRITICAL ERRORS
        # --------------------------------------------------------

        if errors:

            print(
                "\nStartup aborted due to configuration errors."
            )

            print(
                "Check your .env file.\n"
            )

            sys.exit(1)


        # --------------------------------------------------------
        # SUCCESS
        # --------------------------------------------------------

        logger.info(
            "Configuration loaded from: %s",
            _ENV_FILE
        )

        logger.info(
            "Environment: %s",
            cls.FLASK_ENV
        )

        logger.info(
            "Database host: %s",
            cls.DB_HOST
        )

        logger.info(
            "Database port: %s",
            cls.DB_PORT
        )

        logger.info(
            "Database name: %s",
            cls.DB_NAME
        )

        logger.info(
            "AI model: %s",
            (
                cls.GEMINI_MODEL
                if cls.GEMINI_API_KEY
                else "rule-based fallback"
            )
        )

        logger.info(
            "SMS enabled: %s",
            cls.SMS_ENABLED
        )


# ================================================================
# SINGLE CONFIG INSTANCE
# ================================================================

config = Config()