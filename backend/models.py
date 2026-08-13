"""
==============================================================================
FILE: backend/models.py  —  MySQL Database Models
==============================================================================

Uses mysql.connector instead of SQLAlchemy.

TABLES:
    health_workers
    patients
    assessments
    teleconsult_sessions
    audit_logs

IMPORTANT:
    There is NO db.Model, db.Column, db.relationship, or SQLAlchemy here.

Database connection is obtained from:
    database.get_db()
==============================================================================
"""

import json
import uuid
from datetime import datetime, timezone

from database import get_db


# ============================================================================
# UTC HELPER
# ============================================================================

def _utcnow():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


# ============================================================================
# JSON HELPER
# ============================================================================

def _json(value):
    """
    Convert Python data to JSON string for MySQL JSON columns.

    MySQL accepts JSON text through mysql.connector.
    """
    if value is None:
        return None

    if isinstance(value, str):
        return value

    return json.dumps(value, ensure_ascii=False)


def _parse_json(value):
    """
    Convert MySQL JSON value back into Python object.
    """

    if value is None:
        return None

    if isinstance(value, (dict, list)):
        return value

    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


# ============================================================================
# DATABASE TABLE CREATION
# ============================================================================

def create_tables():
    """
    Create all Sahaay Clinic tables.

    Called from database.init_db().
    """

    db = get_db()
    cursor = db.cursor()

    try:

        # ====================================================================
        # HEALTH WORKERS
        # ====================================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_workers (

                id INT AUTO_INCREMENT PRIMARY KEY,

                worker_id VARCHAR(50) NOT NULL UNIQUE,

                name VARCHAR(120) NOT NULL,

                role VARCHAR(30) NOT NULL DEFAULT 'health_worker',

                password_hash VARCHAR(255) NOT NULL,

                is_active BOOLEAN NOT NULL DEFAULT TRUE,

                phone VARCHAR(20),

                email VARCHAR(120),

                district VARCHAR(80),

                created_at DATETIME NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at DATETIME NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,

                INDEX idx_worker_id (worker_id),

                INDEX idx_worker_phone (phone)

            ) ENGINE=InnoDB
        """)


        # ====================================================================
        # PATIENTS
        # ====================================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (

                id INT AUTO_INCREMENT PRIMARY KEY,

                patient_id VARCHAR(40) NOT NULL UNIQUE,

                name VARCHAR(120) NOT NULL,

                age INT NOT NULL,

                gender VARCHAR(10) NOT NULL,

                phone VARCHAR(20),

                village VARCHAR(120),

                chief_complaint TEXT,

                symptom_duration VARCHAR(30),

                known_conditions TEXT,

                current_medications TEXT,

                allergies TEXT,

                pregnancy_status VARCHAR(20),

                vitals_json JSON,

                media_json JSON,

                status VARCHAR(20) NOT NULL
                    DEFAULT 'waiting',

                registered_by INT NULL,

                sync_status VARCHAR(20) NOT NULL
                    DEFAULT 'synced',

                created_at DATETIME NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at DATETIME NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,

                INDEX idx_patient_id (patient_id),

                INDEX idx_patient_phone (phone),

                INDEX idx_patient_status (status),

                INDEX idx_patient_worker (registered_by),

                CONSTRAINT fk_patient_worker
                    FOREIGN KEY (registered_by)
                    REFERENCES health_workers(id)
                    ON DELETE SET NULL

            ) ENGINE=InnoDB
        """)


        # ====================================================================
        # ASSESSMENTS
        # ====================================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (

                id INT AUTO_INCREMENT PRIMARY KEY,

                assessment_id VARCHAR(40) NOT NULL UNIQUE,

                patient_id_fk INT NOT NULL,

                worker_id_fk INT NULL,

                symptoms_json JSON,

                vitals_snapshot JSON,

                additional_notes TEXT,

                ai_condition VARCHAR(200),

                ai_urgency VARCHAR(20),

                ai_confidence VARCHAR(20),

                ai_recommendations JSON,

                ai_medicine_suggestions JSON,

                ai_reasoning TEXT,

                ai_raw_response JSON,

                ai_key_points JSON,

                verification_status VARCHAR(20) NOT NULL
                    DEFAULT 'pending',

                doctor_decision VARCHAR(20),

                doctor_diagnosis VARCHAR(200),

                doctor_treatment TEXT,

                doctor_notes TEXT,

                doctor_name VARCHAR(120),

                doctor_specialty VARCHAR(80),

                verified_at DATETIME,

                created_at DATETIME NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                INDEX idx_assessment_id (assessment_id),

                INDEX idx_assessment_patient (patient_id_fk),

                INDEX idx_assessment_worker (worker_id_fk),

                INDEX idx_assessment_status (verification_status),

                CONSTRAINT fk_assessment_patient
                    FOREIGN KEY (patient_id_fk)
                    REFERENCES patients(id)
                    ON DELETE CASCADE,

                CONSTRAINT fk_assessment_worker
                    FOREIGN KEY (worker_id_fk)
                    REFERENCES health_workers(id)
                    ON DELETE SET NULL

            ) ENGINE=InnoDB
        """)


        # ====================================================================
        # CLINICAL GUIDANCE HISTORY — server history for online/offline reuse
        # ====================================================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clinical_guidance_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_id_fk INT NOT NULL,
                assessment_id VARCHAR(40),
                worker_id_fk INT NULL,
                source VARCHAR(30) NOT NULL DEFAULT 'gemini',
                verification_status VARCHAR(20) NOT NULL DEFAULT 'pending',
                guidance_json JSON NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                verified_at DATETIME NULL,
                INDEX idx_guidance_patient (patient_id_fk),
                INDEX idx_guidance_assessment (assessment_id),
                INDEX idx_guidance_worker (worker_id_fk),
                INDEX idx_guidance_status (verification_status),
                CONSTRAINT fk_guidance_patient FOREIGN KEY (patient_id_fk)
                    REFERENCES patients(id) ON DELETE CASCADE,
                CONSTRAINT fk_guidance_worker FOREIGN KEY (worker_id_fk)
                    REFERENCES health_workers(id) ON DELETE SET NULL
            ) ENGINE=InnoDB
        """)

        # ====================================================================
        # TELECONSULT SESSIONS
        # ====================================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teleconsult_sessions (

                id INT AUTO_INCREMENT PRIMARY KEY,

                session_id VARCHAR(40) NOT NULL UNIQUE,

                patient_id_fk INT NOT NULL,

                session_url VARCHAR(500),

                reason TEXT,

                priority VARCHAR(20) NOT NULL
                    DEFAULT 'routine',

                status VARCHAR(20) NOT NULL
                    DEFAULT 'requested',

                doctor_name VARCHAR(120),

                notes TEXT,

                created_at DATETIME NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                scheduled_at DATETIME NULL,

                INDEX idx_session_id (session_id),

                INDEX idx_session_patient (patient_id_fk),

                INDEX idx_session_status (status),

                CONSTRAINT fk_teleconsult_patient
                    FOREIGN KEY (patient_id_fk)
                    REFERENCES patients(id)
                    ON DELETE CASCADE

            ) ENGINE=InnoDB
        """)


        # ====================================================================
        # AUDIT LOGS
        # ====================================================================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (

                id INT AUTO_INCREMENT PRIMARY KEY,

                action VARCHAR(80) NOT NULL,

                entity_type VARCHAR(40),

                entity_id VARCHAR(40),

                performed_by VARCHAR(50),

                ip_address VARCHAR(50),

                user_agent VARCHAR(200),

                details JSON,

                created_at DATETIME NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                INDEX idx_audit_action (action),

                INDEX idx_audit_entity (entity_type, entity_id),

                INDEX idx_audit_performed_by (performed_by),

                INDEX idx_audit_created_at (created_at)

            ) ENGINE=InnoDB
        """)


        # --------------------------------------------------------------------
        # Compatibility migrations for databases created by earlier Sahaay
        # versions. CREATE TABLE IF NOT EXISTS does not alter an existing table.
        # These columns are required by the current triage/doctor workflow.
        # --------------------------------------------------------------------
        migrations = [
            ("assessments", "ai_medicine_suggestions", "JSON NULL"),
            ("assessments", "ai_key_points", "JSON NULL"),
            ("assessments", "doctor_decision", "VARCHAR(20) NULL"),
            ("assessments", "doctor_diagnosis", "VARCHAR(200) NULL"),
            ("assessments", "doctor_treatment", "TEXT NULL"),
            ("assessments", "doctor_notes", "TEXT NULL"),
            ("assessments", "doctor_name", "VARCHAR(120) NULL"),
            ("assessments", "doctor_specialty", "VARCHAR(80) NULL"),
            ("assessments", "verified_at", "DATETIME NULL"),
            ("clinical_guidance_history", "patient_id_fk", "INT NULL"),
            ("clinical_guidance_history", "assessment_id", "VARCHAR(40) NULL"),
            ("clinical_guidance_history", "worker_id_fk", "INT NULL"),
            ("clinical_guidance_history", "source", "VARCHAR(30) NOT NULL DEFAULT 'gemini'"),
            ("clinical_guidance_history", "verification_status", "VARCHAR(20) NOT NULL DEFAULT 'pending'"),
            ("clinical_guidance_history", "guidance_json", "JSON NULL"),
            ("clinical_guidance_history", "verified_at", "DATETIME NULL"),
        ]
        for table_name, column_name, column_definition in migrations:
            try:
                cursor.execute(
                    f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_definition}"
                )
            except Exception:
                # Column already exists, or this migration is not needed.
                pass

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        cursor.close()


# ============================================================================
# HEALTH WORKER MODEL
# ============================================================================

class HealthWorker:
    """
    MySQL helper for health_workers.
    """

    @staticmethod
    def create(
        worker_id,
        name,
        role,
        password_hash,
        phone=None,
        district=None
    ):

        db = get_db()
        cursor = db.cursor()

        try:

            cursor.execute("""
                INSERT INTO health_workers
                (
                    worker_id,
                    name,
                    role,
                    password_hash,
                    phone,
                    district
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                worker_id,
                name,
                role,
                password_hash,
                phone,
                district
            ))

            db.commit()

            return cursor.lastrowid

        except Exception:
            db.rollback()
            raise

        finally:
            cursor.close()


    @staticmethod
    def get_by_worker_id(worker_id):

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT *
                FROM health_workers
                WHERE worker_id = %s
                LIMIT 1
            """, (worker_id,))

            return cursor.fetchone()

        finally:
            cursor.close()


    @staticmethod
    def get_by_phone(phone):

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT *
                FROM health_workers
                WHERE phone = %s
                LIMIT 1
            """, (phone,))

            return cursor.fetchone()

        finally:
            cursor.close()


    @staticmethod
    def to_dict(worker):

        if not worker:
            return None

        return {
            "id": worker["id"],
            "worker_id": worker["worker_id"],
            "name": worker["name"],
            "role": worker["role"],
            "is_active": bool(worker["is_active"]),
            "district": worker["district"],
            "created_at": (
                worker["created_at"].isoformat()
                if worker["created_at"]
                else None
            )
        }


# ============================================================================
# PATIENT MODEL
# ============================================================================

class Patient:
    """
    MySQL helper for patients.
    """

    @staticmethod
    def create(
        patient_id,
        name,
        age,
        gender,
        phone=None,
        village=None,
        chief_complaint=None,
        symptom_duration=None,
        known_conditions=None,
        current_medications=None,
        allergies=None,
        pregnancy_status=None,
        vitals=None,
        media=None,
        status="waiting",
        registered_by=None,
        sync_status="synced"
    ):

        db = get_db()
        cursor = db.cursor()

        try:

            cursor.execute("""
                INSERT INTO patients
                (
                    patient_id,
                    name,
                    age,
                    gender,
                    phone,
                    village,
                    chief_complaint,
                    symptom_duration,
                    known_conditions,
                    current_medications,
                    allergies,
                    pregnancy_status,
                    vitals_json,
                    media_json,
                    status,
                    registered_by,
                    sync_status
                )
                VALUES
                (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
            """, (
                patient_id,
                name,
                age,
                gender,
                phone,
                village,
                chief_complaint,
                symptom_duration,
                known_conditions,
                current_medications,
                allergies,
                pregnancy_status,
                _json(vitals),
                _json(media),
                status,
                registered_by,
                sync_status
            ))

            db.commit()

            return cursor.lastrowid

        except Exception:
            db.rollback()
            raise

        finally:
            cursor.close()


    @staticmethod
    def get_by_patient_id(patient_id):

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT *
                FROM patients
                WHERE patient_id = %s
                LIMIT 1
            """, (patient_id,))

            patient = cursor.fetchone()

            if patient:
                patient["vitals_json"] = _parse_json(
                    patient["vitals_json"]
                )
                patient["media_json"] = _parse_json(patient.get("media_json"))

            return patient

        finally:
            cursor.close()


    @staticmethod
    def get_by_id(patient_id):

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT *
                FROM patients
                WHERE id = %s
                LIMIT 1
            """, (patient_id,))

            patient = cursor.fetchone()

            if patient:
                patient["vitals_json"] = _parse_json(
                    patient["vitals_json"]
                )

            return patient

        finally:
            cursor.close()


    @staticmethod
    def update_status(patient_id, status):

        db = get_db()
        cursor = db.cursor()

        try:

            cursor.execute("""
                UPDATE patients
                SET status = %s
                WHERE patient_id = %s
            """, (
                status,
                patient_id
            ))

            db.commit()

            return cursor.rowcount > 0

        except Exception:
            db.rollback()
            raise

        finally:
            cursor.close()


    @staticmethod
    def update_sync_status(patient_id, sync_status):

        db = get_db()
        cursor = db.cursor()

        try:

            cursor.execute("""
                UPDATE patients
                SET sync_status = %s
                WHERE patient_id = %s
            """, (
                sync_status,
                patient_id
            ))

            db.commit()

            return cursor.rowcount > 0

        except Exception:
            db.rollback()
            raise

        finally:
            cursor.close()


    @staticmethod
    def update_vitals(patient_id, vitals):
        """Persist and return the latest vital-sign snapshot for a patient."""
        db = get_db()
        cursor = db.cursor(dictionary=True)
        try:
            normalized = dict(vitals or {})
            normalized["recordedAt"] = normalized.get("recordedAt") or _utcnow().isoformat()
            payload = _json(normalized)
            cursor.execute("""
                UPDATE patients
                SET vitals_json = %s, updated_at = CURRENT_TIMESTAMP
                WHERE patient_id = %s
            """, (payload, patient_id))
            if cursor.rowcount < 1:
                db.rollback()
                return None
            cursor.execute("""
                SELECT patient_id, vitals_json, updated_at
                FROM patients WHERE patient_id = %s LIMIT 1
            """, (patient_id,))
            row = cursor.fetchone()
            db.commit()
            if not row:
                return None
            return {
                "patientId": row["patient_id"],
                "vitals": _parse_json(row["vitals_json"]) or {},
                "updatedAt": row["updated_at"].isoformat() if row["updated_at"] else None
            }
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()


    @staticmethod
    def list_patients(
        limit=50,
        offset=0
    ):

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT *
                FROM patients
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (
                limit,
                offset
            ))

            patients = cursor.fetchall()

            for patient in patients:
                patient["vitals_json"] = _parse_json(
                    patient["vitals_json"]
                )

            return patients

        finally:
            cursor.close()


    @staticmethod
    def to_dict(
        patient,
        include_vitals=True,
        include_assessments=False
    ):

        if not patient:
            return None

        data = {
            "patientId": patient["patient_id"],
            "name": patient["name"],
            "age": patient["age"],
            "gender": patient["gender"],
            "phone": patient["phone"],
            "village": patient["village"],
            "chiefComplaint": patient["chief_complaint"],
            "symptomDuration": patient["symptom_duration"],
            "knownConditions": patient["known_conditions"],
            "currentMedications": patient["current_medications"],
            "allergies": patient["allergies"],
            "pregnancyStatus": patient["pregnancy_status"],
            "attachments": patient.get("media_json") or [],
            "status": patient["status"],
            "syncStatus": patient["sync_status"],
            "createdAt": (
                patient["created_at"].isoformat()
                if patient["created_at"]
                else None
            ),
            "updatedAt": (
                patient["updated_at"].isoformat()
                if patient["updated_at"]
                else None
            )
        }

        if include_vitals:
            data["vitals"] = (
                _parse_json(patient.get("vitals_json")) or {}
            )

        if include_assessments:
            data["assessments"] = [Assessment.to_dict(a) for a in Patient.get_assessments(patient["id"])]

        return data

    @staticmethod
    def get_assessments(patient_db_id, limit=50):
        db = get_db()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT * FROM assessments
                WHERE patient_id_fk = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (patient_db_id, int(limit)))
            rows = cursor.fetchall()
            for row in rows:
                row["symptoms_json"] = _parse_json(row.get("symptoms_json"))
                row["vitals_snapshot"] = _parse_json(row.get("vitals_snapshot"))
                row["ai_recommendations"] = _parse_json(row.get("ai_recommendations"))
                row["ai_medicine_suggestions"] = _parse_json(row.get("ai_medicine_suggestions"))
                row["ai_raw_response"] = _parse_json(row.get("ai_raw_response"))
                row["ai_key_points"] = _parse_json(row.get("ai_key_points"))
            return rows
        finally:
            cursor.close()


# ============================================================================
# ASSESSMENT MODEL
# ============================================================================

class Assessment:
    """
    MySQL helper for AI triage assessments.
    """

    @staticmethod
    def create(
        assessment_id,
        patient_id_fk,
        worker_id_fk=None,
        symptoms=None,
        vitals=None,
        additional_notes=None
    ):

        db = get_db()
        cursor = db.cursor()

        try:

            cursor.execute("""
                INSERT INTO assessments
                (
                    assessment_id,
                    patient_id_fk,
                    worker_id_fk,
                    symptoms_json,
                    vitals_snapshot,
                    additional_notes
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                assessment_id,
                patient_id_fk,
                worker_id_fk,
                _json(symptoms),
                _json(vitals),
                additional_notes
            ))

            db.commit()

            return cursor.lastrowid

        except Exception:
            db.rollback()
            raise

        finally:
            cursor.close()


    @staticmethod
    def get_by_assessment_id(assessment_id):

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    a.*,
                    p.patient_id,
                    p.name AS patient_name
                FROM assessments a
                JOIN patients p
                    ON p.id = a.patient_id_fk
                WHERE a.assessment_id = %s
                LIMIT 1
            """, (assessment_id,))

            assessment = cursor.fetchone()

            if assessment:

                assessment["symptoms_json"] = _parse_json(
                    assessment["symptoms_json"]
                )

                assessment["vitals_snapshot"] = _parse_json(
                    assessment["vitals_snapshot"]
                )

                assessment["ai_recommendations"] = _parse_json(
                    assessment["ai_recommendations"]
                )

                assessment["ai_raw_response"] = _parse_json(
                    assessment["ai_raw_response"]
                )

            return assessment

        finally:
            cursor.close()


    @staticmethod
    def update_ai_result(
        assessment_id,
        condition=None,
        urgency=None,
        confidence=None,
        recommendations=None,
        medicine_suggestions=None,
        reasoning=None,
        raw_response=None,
        key_points=None
    ):

        db = get_db()
        cursor = db.cursor()

        try:

            cursor.execute("""
                UPDATE assessments
                SET
                    ai_condition = %s,
                    ai_urgency = %s,
                    ai_confidence = %s,
                    ai_recommendations = %s,
                    ai_medicine_suggestions = %s,
                    ai_reasoning = %s,
                    ai_raw_response = %s,
                    ai_key_points = %s
                WHERE assessment_id = %s
            """, (
                condition,
                urgency,
                confidence,
                _json(recommendations),
                _json(medicine_suggestions),
                reasoning,
                _json(raw_response),
                _json(key_points),
                assessment_id
            ))

            db.commit()

            return cursor.rowcount > 0

        except Exception:
            db.rollback()
            raise

        finally:
            cursor.close()


    @staticmethod
    def to_dict(assessment):
        if not assessment:
            return None
        return {
            "assessmentId": assessment.get("assessment_id"),
            "patientId": assessment.get("patient_id"),
            "patientName": assessment.get("patient_name"),
            "symptoms": _parse_json(assessment.get("symptoms_json")),
            "vitals": _parse_json(assessment.get("vitals_snapshot")),
            "additionalNotes": assessment.get("additional_notes"),
            "condition": assessment.get("ai_condition"),
            "urgency": assessment.get("ai_urgency"),
            "confidence": assessment.get("ai_confidence"),
            "recommendations": _parse_json(assessment.get("ai_recommendations")) or [],
            "medicineSuggestions": _parse_json(assessment.get("ai_medicine_suggestions")) or [],
            "reasoning": assessment.get("ai_reasoning"),
            "redFlags": [],
            "keyPoints": _parse_json(assessment.get("ai_key_points")) or [],
            "verificationStatus": assessment.get("verification_status"),
            "doctorDecision": assessment.get("doctor_decision"),
            "doctorDiagnosis": assessment.get("doctor_diagnosis"),
            "doctorTreatment": assessment.get("doctor_treatment"),
            "doctorNotes": assessment.get("doctor_notes"),
            "doctorName": assessment.get("doctor_name"),
            "doctorSpecialty": assessment.get("doctor_specialty"),
            "verifiedAt": assessment.get("verified_at").isoformat() if assessment.get("verified_at") and hasattr(assessment.get("verified_at"), "isoformat") else assessment.get("verified_at"),
            "createdAt": assessment.get("created_at").isoformat() if assessment.get("created_at") and hasattr(assessment.get("created_at"), "isoformat") else assessment.get("created_at")
        }


    @staticmethod
    def verify(
        assessment_id,
        verification_status,
        doctor_decision=None,
        doctor_diagnosis=None,
        doctor_treatment=None,
        doctor_notes=None,
        doctor_name=None,
        doctor_specialty=None
    ):

        db = get_db()
        cursor = db.cursor()

        try:

            cursor.execute("""
                UPDATE assessments
                SET
                    verification_status = %s,
                    doctor_decision = %s,
                    doctor_diagnosis = %s,
                    doctor_treatment = %s,
                    doctor_notes = %s,
                    doctor_name = %s,
                    doctor_specialty = %s,
                    verified_at = CURRENT_TIMESTAMP
                WHERE assessment_id = %s
            """, (
                verification_status,
                doctor_decision,
                doctor_diagnosis,
                doctor_treatment,
                doctor_notes,
                doctor_name,
                doctor_specialty,
                assessment_id
            ))

            db.commit()

            return cursor.rowcount > 0

        except Exception:
            db.rollback()
            raise

        finally:
            cursor.close()


# ============================================================================
# TELECONSULT MODEL
# ============================================================================

class ClinicalGuidanceHistory:
    @staticmethod
    def create(patient_id_fk, assessment_id, worker_id_fk, source, guidance, verification_status="pending"):
        db = get_db(); cur = db.cursor()
        try:
            cur.execute("""
                INSERT INTO clinical_guidance_history
                (patient_id_fk, assessment_id, worker_id_fk, source, verification_status, guidance_json)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (patient_id_fk, assessment_id, worker_id_fk, source, verification_status, _json(guidance or {})))
            db.commit(); return cur.lastrowid
        finally:
            cur.close(); db.close()

    @staticmethod
    def mark_verified(assessment_id, verification_status="verified"):
        db = get_db(); cur = db.cursor()
        try:
            cur.execute("UPDATE clinical_guidance_history SET verification_status=%s, verified_at=CURRENT_TIMESTAMP WHERE assessment_id=%s", (verification_status, assessment_id))
            db.commit()
        finally:
            cur.close(); db.close()

    @staticmethod
    def get_by_patient(patient_id_fk, limit=50):
        db = get_db(); cur = db.cursor(dictionary=True)
        try:
            cur.execute("""
                SELECT id, assessment_id, source, verification_status, guidance_json, created_at, verified_at
                FROM clinical_guidance_history WHERE patient_id_fk=%s
                ORDER BY created_at DESC LIMIT %s
            """, (patient_id_fk, int(limit)))
            rows = cur.fetchall()
            for row in rows: row["guidance_json"] = _parse_json(row["guidance_json"])
            return rows
        finally:
            cur.close(); db.close()


class TeleconsultSession:
    """
    MySQL helper for teleconsultation sessions.
    """

    @staticmethod
    def create(
        session_id,
        patient_id_fk,
        session_url=None,
        reason=None,
        priority="routine",
        status="requested",
        doctor_name=None,
        notes=None,
        scheduled_at=None
    ):

        db = get_db()
        cursor = db.cursor()

        try:

            cursor.execute("""
                INSERT INTO teleconsult_sessions
                (
                    session_id,
                    patient_id_fk,
                    session_url,
                    reason,
                    priority,
                    status,
                    doctor_name,
                    notes,
                    scheduled_at
                )
                VALUES
                (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, (
                session_id,
                patient_id_fk,
                session_url,
                reason,
                priority,
                status,
                doctor_name,
                notes,
                scheduled_at
            ))

            db.commit()

            return cursor.lastrowid

        except Exception:
            db.rollback()
            raise

        finally:
            cursor.close()


    @staticmethod
    def get_by_session_id(session_id):

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT
                    t.*,
                    p.patient_id,
                    p.name AS patient_name
                FROM teleconsult_sessions t
                JOIN patients p
                    ON p.id = t.patient_id_fk
                WHERE t.session_id = %s
                LIMIT 1
            """, (session_id,))

            return cursor.fetchone()

        finally:
            cursor.close()


    @staticmethod
    def update_status(
        session_id,
        status
    ):

        db = get_db()
        cursor = db.cursor()

        try:

            cursor.execute("""
                UPDATE teleconsult_sessions
                SET status = %s
                WHERE session_id = %s
            """, (
                status,
                session_id
            ))

            db.commit()

            return cursor.rowcount > 0

        except Exception:
            db.rollback()
            raise

        finally:
            cursor.close()


    @staticmethod
    def get_recent(limit=20, status_filter=None):
        """
        Return recent teleconsult sessions joined with patient data.

        Args:
            limit        : max rows (capped at 50)
            status_filter: None/"all" → all rows, else filter by status

        Returns:
            list of dicts
        """

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            limit = min(int(limit), 50)

            if status_filter and status_filter != "all":
                cursor.execute("""
                    SELECT
                        ts.session_id,
                        ts.session_url,
                        ts.reason,
                        ts.priority,
                        ts.status,
                        ts.created_at,
                        p.patient_id,
                        p.name AS patient_name,
                        p.age,
                        p.gender
                    FROM teleconsult_sessions ts
                    JOIN patients p ON p.id = ts.patient_id_fk
                    WHERE ts.status = %s
                    ORDER BY ts.created_at DESC
                    LIMIT %s
                """, (status_filter, limit))
            else:
                cursor.execute("""
                    SELECT
                        ts.session_id,
                        ts.session_url,
                        ts.reason,
                        ts.priority,
                        ts.status,
                        ts.created_at,
                        p.patient_id,
                        p.name AS patient_name,
                        p.age,
                        p.gender
                    FROM teleconsult_sessions ts
                    JOIN patients p ON p.id = ts.patient_id_fk
                    ORDER BY ts.created_at DESC
                    LIMIT %s
                """, (limit,))

            rows = cursor.fetchall()

            for row in rows:
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()

            return rows

        finally:
            cursor.close()


# ============================================================================
# AUDIT LOG MODEL
# ============================================================================

class AuditLog:
    """
    Immutable security/audit trail.

    Records are inserted only.
    """

    @staticmethod
    def create(
        action,
        entity_type=None,
        entity_id=None,
        performed_by=None,
        ip_address=None,
        user_agent=None,
        details=None
    ):

        db = get_db()
        cursor = db.cursor()

        try:

            cursor.execute("""
                INSERT INTO audit_logs
                (
                    action,
                    entity_type,
                    entity_id,
                    performed_by,
                    ip_address,
                    user_agent,
                    details
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                action,
                entity_type,
                entity_id,
                performed_by,
                ip_address,
                user_agent,
                _json(details)
            ))

            db.commit()

            return cursor.lastrowid

        except Exception:
            db.rollback()
            raise

        finally:
            cursor.close()


    @staticmethod
    def get_recent(limit=100):

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT *
                FROM audit_logs
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))

            logs = cursor.fetchall()

            for log in logs:

                log["details"] = _parse_json(
                    log["details"]
                )

            return logs

        finally:
            cursor.close()
