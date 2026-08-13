"""MySQL Connector database lifecycle and forward migrations."""

import mysql.connector
from mysql.connector import Error

from config import config


def get_db():
    try:
        connection = mysql.connector.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DATABASE,
            autocommit=False,
        )
        if not connection.is_connected():
            raise RuntimeError("Unable to connect to MySQL.")
        return connection
    except Error as exc:
        raise RuntimeError(f"MySQL connection failed: {exc}") from exc


def _ensure_column(connection, table, column, definition):
    cursor = connection.cursor()
    try:
        cursor.execute(f"SHOW COLUMNS FROM `{table}` LIKE %s", (column,))
        if cursor.fetchone() is None:
            cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}")
            connection.commit()
    finally:
        cursor.close()


def migrate_schema(connection):
    # These migrations fix databases created by older Sahaay versions.
    _ensure_column(connection, "health_workers", "email", "VARCHAR(120) NULL")
    _ensure_column(connection, "patients", "media_json", "JSON NULL")
    _ensure_column(connection, "patients", "vitals_json", "JSON NULL")
    _ensure_column(connection, "patients", "updated_at", "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    _ensure_column(connection, "assessments", "vitals_snapshot", "JSON NULL")


def init_db(app):
    connection = None
    try:
        connection = get_db()
        # IMPORTANT: the previous version only created health_workers here,
        # which caused patient registration to fail on a fresh MySQL database.
        from models import create_tables
        create_tables()
        migrate_schema(connection)
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        app.logger.info("MySQL database initialized and schema migrated successfully.")
    except Exception as exc:
        if connection:
            connection.rollback()
        app.logger.critical("MySQL initialization failed: %s", exc)
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()
