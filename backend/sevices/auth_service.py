"""
==============================================================================
FILE: backend/services/auth_service.py
Authentication utilities
==============================================================================
"""

import bcrypt

from datetime import timedelta

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token
)

from database import get_db


# ============================================================================
# PASSWORD HASH
# ============================================================================

def hash_password(password: str) -> str:

    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


# ============================================================================
# PASSWORD VERIFY
# ============================================================================

def verify_password(
    password: str,
    password_hash: str
) -> bool:

    if not password_hash:
        return False

    try:

        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )

    except ValueError:

        return False


# ============================================================================
# JWT TOKENS
# ============================================================================

def generate_tokens(
    worker,
    expires_minutes=480
):

    identity = worker["worker_id"]

    additional_claims = {
        "role": worker["role"],
        "name": worker["name"]
    }

    access_token = create_access_token(
        identity=identity,
        additional_claims=additional_claims,
        expires_delta=timedelta(
            minutes=expires_minutes
        )
    )

    refresh_token = create_refresh_token(
        identity=identity
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_minutes * 60
    }


# ============================================================================
# AUDIT LOG
# ============================================================================

def log_audit(
    action,
    entity_type=None,
    entity_id=None,
    performed_by=None,
    ip_address=None,
    user_agent=None,
    details=None
):

    connection = None

    try:

        connection = get_db()

        cursor = connection.cursor()

        import json

        details_json = (
            json.dumps(details)
            if details is not None
            else None
        )

        cursor.execute(
            """
            INSERT INTO audit_logs (
                action,
                entity_type,
                entity_id,
                performed_by,
                ip_address,
                user_agent,
                details
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s
            )
            """,
            (
                action,
                entity_type,
                entity_id,
                performed_by,
                ip_address,
                user_agent,
                details_json
            )
        )

        connection.commit()

        cursor.close()

    except Exception:

        if connection:
            connection.rollback()

        # Audit failure should not normally
        # destroy the main login operation.

    finally:

        if connection and connection.is_connected():
            connection.close()