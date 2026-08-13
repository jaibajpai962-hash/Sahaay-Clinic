"""
==============================================================================
FILE: backend/seed_data.py  —  MySQL Demo Data Seeder
==============================================================================

Populates the MySQL database with realistic demo data.

USAGE:
    cd sahaay-clinic/backend
    python seed_data.py

CREATES:
    - Health workers
    - Demo patients
    - AI assessments
    - Audit logs

DATABASE:
    Uses mysql.connector through database.py.

SAFETY:
    This script refuses to run when FLASK_ENV=production.
==============================================================================
"""

import os
import sys
import json

# ============================================================================
# MAKE BACKEND IMPORTABLE
# ============================================================================

sys.path.insert(
    0,
    os.path.dirname(os.path.abspath(__file__))
)


# ============================================================================
# IMPORTS
# ============================================================================

from datetime import datetime, timezone, timedelta

from app import create_app
from config import config
from database import get_db
from models import create_tables
from services.auth_service import hash_password


# ============================================================================
# JSON HELPER
# ============================================================================

def json_value(value):
    """
    Convert Python dictionaries/lists to JSON text for MySQL JSON columns.
    """

    if value is None:
        return None

    if isinstance(value, str):
        return value

    return json.dumps(
        value,
        ensure_ascii=False
    )


# ============================================================================
# SEED FUNCTION
# ============================================================================

def seed():
    """
    Insert demo data into MySQL.

    The operation is idempotent:
    existing records are skipped.
    """

    # ========================================================================
    # PRODUCTION SAFETY
    # ========================================================================

    if config.FLASK_ENV.lower() == "production":

        print(
            "Seeder aborted — FLASK_ENV is 'production'."
        )

        sys.exit(1)


    # ========================================================================
    # CREATE FLASK APPLICATION
    # ========================================================================

    app = create_app()


    with app.app_context():

        print()
        print("=" * 70)
        print("SAHAAY CLINIC — MYSQL DEMO DATA SEEDER")
        print("=" * 70)

        print(
            f"Database : {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
        )


        # ====================================================================
        # MAKE SURE TABLES EXIST
        # ====================================================================

        create_tables()

        db = get_db()


        # ====================================================================
        # 1. HEALTH WORKERS
        # ====================================================================

        workers_data = [

            {
                "worker_id": "HW-DEMO-001",
                "name": "Demo Health Worker",
                "role": "health_worker",
                "pin": "1234",
                "phone": "9999900001",
                "district": "Demo District"
            },

            {
                "worker_id": "HW-MH-0042",
                "name": "Priya Sharma",
                "role": "health_worker",
                "pin": "5678",
                "phone": "9876500042",
                "district": "Wardha, Maharashtra"
            },

            {
                "worker_id": "DOC-MH-001",
                "name": "Dr. Rajesh Mehta",
                "role": "doctor",
                "pin": "9999",
                "phone": "9123456789",
                "district": "Nagpur, Maharashtra"
            },

            {
                "worker_id": "ADMIN-001",
                "name": "System Administrator",
                "role": "admin",
                "pin": "0000",
                "phone": None,
                "district": None
            }
        ]


        workers_created = 0


        for worker in workers_data:

            cursor = db.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT id
                FROM health_workers
                WHERE worker_id = %s
                LIMIT 1
                """,
                (worker["worker_id"],)
            )

            existing = cursor.fetchone()

            cursor.close()


            if existing:

                print(
                    f"  SKIP Worker: "
                    f"{worker['worker_id']} already exists"
                )

                continue


            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO health_workers
                (
                    worker_id,
                    name,
                    role,
                    password_hash,
                    is_active,
                    phone,
                    district
                )
                VALUES
                (
                    %s, %s, %s, %s,
                    %s, %s, %s
                )
                """,
                (
                    worker["worker_id"],
                    worker["name"],
                    worker["role"],
                    hash_password(worker["pin"]),
                    True,
                    worker.get("phone"),
                    worker.get("district")
                )
            )

            db.commit()

            cursor.close()

            workers_created += 1

            print(
                f"  OK Worker: "
                f"{worker['worker_id']} "
                f"({worker['role']})"
            )


        # ====================================================================
        # GET DEMO WORKER DATABASE ID
        # ====================================================================

        cursor = db.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT id
            FROM health_workers
            WHERE worker_id = %s
            LIMIT 1
            """,
            ("HW-DEMO-001",)
        )

        demo_worker = cursor.fetchone()

        cursor.close()

        demo_worker_id = (
            demo_worker["id"]
            if demo_worker
            else None
        )


        # ====================================================================
        # 2. PATIENTS
        # ====================================================================

        now = datetime.now(
            timezone.utc
        ).replace(
            tzinfo=None
        )


        patients_data = [

            {
                "patient_id": "SAH-MH-DEMO-001",
                "name": "Ramesh Kumar",
                "age": 45,
                "gender": "Male",
                "phone": "9876543210",
                "village": "Koregaon, Wardha",
                "chief_complaint": "Fever with chills for 3 days",
                "symptom_duration": "1-3 days",
                "known_conditions": "None",
                "current_medications": "None",
                "allergies": "NKDA",
                "pregnancy_status": "N/A",
                "vitals": {
                    "temperature": 39.2,
                    "bpSystolic": 118,
                    "bpDiastolic": 76,
                    "spo2": 97,
                    "pulseRate": 96,
                    "respiratoryRate": 18,
                    "weight": 65
                },
                "status": "in_progress",
                "created_at": now - timedelta(hours=2)
            },

            {
                "patient_id": "SAH-MH-DEMO-002",
                "name": "Sunita Devi",
                "age": 28,
                "gender": "Female",
                "phone": "9988776655",
                "village": "Hinganghat",
                "chief_complaint": "Diarrhoea and vomiting since yesterday",
                "symptom_duration": "<1 day",
                "known_conditions": "None",
                "current_medications": "None",
                "allergies": "NKDA",
                "pregnancy_status": "pregnant",
                "vitals": {
                    "temperature": 37.8,
                    "bpSystolic": 108,
                    "bpDiastolic": 70,
                    "spo2": 98,
                    "pulseRate": 104,
                    "respiratoryRate": 16,
                    "weight": 58
                },
                "status": "waiting",
                "created_at": now - timedelta(hours=1)
            },

            {
                "patient_id": "SAH-MH-DEMO-003",
                "name": "Arjun Patil",
                "age": 8,
                "gender": "Male",
                "phone": "9123456789",
                "village": "Arvi",
                "chief_complaint": "High fever, rash on body for 2 days",
                "symptom_duration": "1-3 days",
                "known_conditions": "None",
                "current_medications": "None",
                "allergies": "NKDA",
                "pregnancy_status": "N/A",
                "vitals": {
                    "temperature": 40.1,
                    "bpSystolic": 100,
                    "bpDiastolic": 65,
                    "spo2": 96,
                    "pulseRate": 120,
                    "respiratoryRate": 22,
                    "weight": 25
                },
                "status": "critical",
                "created_at": now - timedelta(minutes=30)
            },

            {
                "patient_id": "SAH-MH-DEMO-004",
                "name": "Radha Bai",
                "age": 62,
                "gender": "Female",
                "phone": None,
                "village": "Seloo",
                "chief_complaint": "Chest pain and breathlessness",
                "symptom_duration": "<1 day",
                "known_conditions": "Hypertension, Diabetes",
                "current_medications": "Metformin 500mg, Amlodipine 5mg",
                "allergies": "Penicillin",
                "pregnancy_status": "not_pregnant",
                "vitals": {
                    "temperature": 37.0,
                    "bpSystolic": 188,
                    "bpDiastolic": 112,
                    "spo2": 91,
                    "pulseRate": 110,
                    "respiratoryRate": 26,
                    "weight": 72
                },
                "status": "critical",
                "created_at": now - timedelta(minutes=15)
            },

            {
                "patient_id": "SAH-MH-DEMO-005",
                "name": "Vikram Rao",
                "age": 34,
                "gender": "Male",
                "phone": "9876512345",
                "village": "Pulgaon",
                "chief_complaint": "Minor cut on right hand — wound care needed",
                "symptom_duration": "<1 day",
                "known_conditions": "None",
                "current_medications": "None",
                "allergies": "NKDA",
                "pregnancy_status": "N/A",
                "vitals": {
                    "temperature": 36.8,
                    "bpSystolic": 122,
                    "bpDiastolic": 78,
                    "spo2": 99,
                    "pulseRate": 74,
                    "respiratoryRate": 15,
                    "weight": 78
                },
                "status": "waiting",
                "created_at": now - timedelta(hours=3)
            },

            {
                "patient_id": "SAH-MH-DEMO-006",
                "name": "Meena Shinde",
                "age": 40,
                "gender": "Female",
                "phone": "9443322110",
                "village": "Deoli",
                "chief_complaint": "Headache and body ache, suspected viral fever",
                "symptom_duration": "4-7 days",
                "known_conditions": "Migraine",
                "current_medications": "Paracetamol 500mg PRN",
                "allergies": "NKDA",
                "pregnancy_status": "not_pregnant",
                "vitals": {
                    "temperature": 38.6,
                    "bpSystolic": 126,
                    "bpDiastolic": 82,
                    "spo2": 97,
                    "pulseRate": 88,
                    "respiratoryRate": 17,
                    "weight": 55
                },
                "status": "completed",
                "created_at": now - timedelta(hours=5)
            },

            {
                "patient_id": "SAH-MH-DEMO-007",
                "name": "Baby of Sunita Devi",
                "age": 0,
                "gender": "Female",
                "phone": None,
                "village": "Hinganghat",
                "chief_complaint": "Newborn — routine check after home delivery",
                "symptom_duration": "<1 day",
                "known_conditions": "None",
                "current_medications": "None",
                "allergies": "None",
                "pregnancy_status": "N/A",
                "vitals": {
                    "temperature": 36.5,
                    "spo2": 98,
                    "pulseRate": 140,
                    "respiratoryRate": 44,
                    "weight": 3.2
                },
                "status": "waiting",
                "created_at": now - timedelta(minutes=45)
            },

            {
                "patient_id": "SAH-MH-DEMO-008",
                "name": "Ganesh Mane",
                "age": 55,
                "gender": "Male",
                "phone": "9765432180",
                "village": "Wardha",
                "chief_complaint": "Snake bite — right forearm — 1 hour ago",
                "symptom_duration": "<1 day",
                "known_conditions": "None",
                "current_medications": "None",
                "allergies": "NKDA",
                "pregnancy_status": "N/A",
                "vitals": {
                    "temperature": 37.1,
                    "bpSystolic": 95,
                    "bpDiastolic": 62,
                    "spo2": 94,
                    "pulseRate": 118,
                    "respiratoryRate": 22,
                    "weight": 70
                },
                "status": "critical",
                "created_at": now - timedelta(minutes=10)
            }
        ]


        patients_created = 0


        for patient in patients_data:

            cursor = db.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT id
                FROM patients
                WHERE patient_id = %s
                LIMIT 1
                """,
                (patient["patient_id"],)
            )

            existing = cursor.fetchone()

            cursor.close()


            if existing:

                print(
                    f"  SKIP Patient: "
                    f"{patient['patient_id']}"
                )

                continue


            cursor = db.cursor()

            cursor.execute(
                """
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
                    status,
                    registered_by,
                    sync_status,
                    created_at,
                    updated_at
                )
                VALUES
                (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    patient["patient_id"],
                    patient["name"],
                    patient["age"],
                    patient["gender"],
                    patient.get("phone"),
                    patient.get("village"),
                    patient.get("chief_complaint"),
                    patient.get("symptom_duration"),
                    patient.get("known_conditions"),
                    patient.get("current_medications"),
                    patient.get("allergies"),
                    patient.get("pregnancy_status"),
                    json_value(patient.get("vitals", {})),
                    patient.get("status", "waiting"),
                    demo_worker_id,
                    "synced",
                    patient.get("created_at", now),
                    patient.get("created_at", now)
                )
            )

            db.commit()

            cursor.close()

            patients_created += 1

            print(
                f"  OK Patient: "
                f"{patient['patient_id']} — "
                f"{patient['name']}"
            )


        # ====================================================================
        # 3. ASSESSMENTS
        # ====================================================================

        assessments_data = [

            {
                "assessment_id": "ASMT-DEMO-001",
                "patient_id": "SAH-MH-DEMO-001",

                "symptoms": [
                    "Fever",
                    "Chills",
                    "Headache",
                    "Body ache",
                    "Fatigue"
                ],

                "ai_condition":
                    "Suspected P. falciparum Malaria",

                "ai_urgency":
                    "high",

                "ai_confidence":
                    "Medium (50-80%)",

                "ai_recommendations": [
                    "Perform Rapid Diagnostic Test (RDT) for malaria.",
                    "Provide appropriate supportive care.",
                    "Ensure adequate hydration.",
                    "Refer to a qualified clinician for confirmed treatment."
                ],

                "ai_reasoning":
                    "Fever with chills and headache requires clinical "
                    "assessment and appropriate diagnostic testing.",

                "verification_status":
                    "pending"
            },

            {
                "assessment_id": "ASMT-DEMO-002",
                "patient_id": "SAH-MH-DEMO-002",

                "symptoms": [
                    "Diarrhoea",
                    "Vomiting",
                    "Nausea",
                    "Fatigue"
                ],

                "ai_condition":
                    "Acute Gastroenteritis with Dehydration Risk",

                "ai_urgency":
                    "moderate",

                "ai_confidence":
                    "High (>80%)",

                "ai_recommendations": [
                    "Start oral rehydration promptly.",
                    "Monitor for signs of dehydration.",
                    "Pregnancy requires additional clinical monitoring.",
                    "Refer to a doctor if symptoms worsen."
                ],

                "ai_reasoning":
                    "Diarrhoea and vomiting with elevated pulse may indicate "
                    "dehydration. Pregnancy increases the need for monitoring.",

                "verification_status":
                    "pending"
            },

            {
                "assessment_id": "ASMT-DEMO-003",
                "patient_id": "SAH-MH-DEMO-003",

                "symptoms": [
                    "Fever",
                    "Rash/skin changes",
                    "Headache",
                    "Body ache"
                ],

                "ai_condition":
                    "Suspected Dengue / Viral Exanthem",

                "ai_urgency":
                    "critical",

                "ai_confidence":
                    "Medium (50-80%)",

                "ai_recommendations": [
                    "Immediate clinical evaluation is required.",
                    "Monitor temperature and vital signs.",
                    "Avoid self-medication.",
                    "Arrange urgent hospital assessment."
                ],

                "ai_reasoning":
                    "High fever with rash and elevated pulse in a child "
                    "requires urgent clinical assessment.",

                "verification_status":
                    "pending"
            },

            {
                "assessment_id": "ASMT-DEMO-004",
                "patient_id": "SAH-MH-DEMO-004",

                "symptoms": [
                    "Chest pain",
                    "Difficulty breathing",
                    "Dizziness"
                ],

                "ai_condition":
                    "Hypertensive Emergency + Respiratory Distress",

                "ai_urgency":
                    "critical",

                "ai_confidence":
                    "High (>80%)",

                "ai_recommendations": [
                    "Immediate emergency medical evaluation.",
                    "Arrange emergency transport.",
                    "Monitor blood pressure and oxygen saturation.",
                    "Continuous clinical monitoring is required."
                ],

                "ai_reasoning":
                    "Chest pain, breathlessness, severe hypertension and "
                    "low oxygen saturation represent a potentially "
                    "life-threatening presentation.",

                "verification_status":
                    "verified",

                "doctor_decision":
                    "approve",

                "doctor_diagnosis":
                    "Hypertensive Emergency with Acute Pulmonary Oedema",

                "doctor_treatment":
                    "Emergency hospital management and specialist care.",

                "doctor_notes":
                    "Urgent cardiology assessment required.",

                "doctor_name":
                    "Dr. Rajesh Mehta / REG-MH-001",

                "verified_at":
                    now - timedelta(hours=1)
            },

            {
                "assessment_id": "ASMT-DEMO-005",
                "patient_id": "SAH-MH-DEMO-006",

                "symptoms": [
                    "Fever",
                    "Headache",
                    "Body ache",
                    "Fatigue",
                    "Runny nose"
                ],

                "ai_condition":
                    "Viral Upper Respiratory Tract Infection (URTI)",

                "ai_urgency":
                    "moderate",

                "ai_confidence":
                    "High (>80%)",

                "ai_recommendations": [
                    "Provide appropriate supportive care.",
                    "Encourage adequate rest and fluids.",
                    "Monitor symptoms.",
                    "Clinical review if symptoms worsen or persist."
                ],

                "ai_reasoning":
                    "The symptoms are consistent with a viral upper "
                    "respiratory presentation without respiratory distress.",

                "verification_status":
                    "verified",

                "doctor_decision":
                    "modify",

                "doctor_diagnosis":
                    "Acute Viral URTI with tension headache component",

                "doctor_treatment":
                    "Supportive treatment and clinical follow-up.",

                "doctor_notes":
                    "Migraine history considered during assessment.",

                "doctor_name":
                    "Dr. Rajesh Mehta / REG-MH-001",

                "verified_at":
                    now - timedelta(hours=3)
            }
        ]


        assessments_created = 0


        for assessment in assessments_data:

            # ---------------------------------------------------------------
            # Check existing assessment
            # ---------------------------------------------------------------

            cursor = db.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT id
                FROM assessments
                WHERE assessment_id = %s
                LIMIT 1
                """,
                (assessment["assessment_id"],)
            )

            existing = cursor.fetchone()

            cursor.close()


            if existing:

                print(
                    f"  SKIP Assessment: "
                    f"{assessment['assessment_id']}"
                )

                continue


            # ---------------------------------------------------------------
            # Find patient database ID
            # ---------------------------------------------------------------

            cursor = db.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT
                    id,
                    vitals_json,
                    created_at
                FROM patients
                WHERE patient_id = %s
                LIMIT 1
                """,
                (assessment["patient_id"],)
            )

            patient = cursor.fetchone()

            cursor.close()


            if not patient:

                print(
                    f"  WARNING: Patient not found: "
                    f"{assessment['patient_id']}"
                )

                continue


            # ---------------------------------------------------------------
            # Insert assessment
            # ---------------------------------------------------------------

            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO assessments
                (
                    assessment_id,
                    patient_id_fk,
                    worker_id_fk,
                    symptoms_json,
                    vitals_snapshot,
                    ai_condition,
                    ai_urgency,
                    ai_confidence,
                    ai_recommendations,
                    ai_reasoning,
                    verification_status,
                    doctor_decision,
                    doctor_diagnosis,
                    doctor_treatment,
                    doctor_notes,
                    doctor_name,
                    verified_at,
                    created_at
                )
                VALUES
                (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s
                )
                """,
                (
                    assessment["assessment_id"],
                    patient["id"],
                    demo_worker_id,

                    json_value(
                        assessment.get("symptoms", [])
                    ),

                    patient["vitals_json"],

                    assessment.get("ai_condition"),
                    assessment.get("ai_urgency"),
                    assessment.get("ai_confidence"),

                    json_value(
                        assessment.get(
                            "ai_recommendations",
                            []
                        )
                    ),

                    assessment.get(
                        "ai_reasoning"
                    ),

                    assessment.get(
                        "verification_status",
                        "pending"
                    ),

                    assessment.get(
                        "doctor_decision"
                    ),

                    assessment.get(
                        "doctor_diagnosis"
                    ),

                    assessment.get(
                        "doctor_treatment"
                    ),

                    assessment.get(
                        "doctor_notes"
                    ),

                    assessment.get(
                        "doctor_name"
                    ),

                    assessment.get(
                        "verified_at"
                    ),

                    patient["created_at"]
                )
            )

            db.commit()

            cursor.close()

            assessments_created += 1

            status = (
                "VERIFIED"
                if assessment.get(
                    "verification_status"
                ) == "verified"
                else "PENDING"
            )

            print(
                f"  OK Assessment: "
                f"{assessment['assessment_id']} "
                f"[{status}]"
            )


        # ====================================================================
        # 4. AUDIT LOG
        # ====================================================================

        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO audit_logs
            (
                action,
                entity_type,
                entity_id,
                performed_by,
                details
            )
            VALUES
            (
                %s, %s, %s, %s, %s
            )
            """,
            (
                "system.demo_seed",
                "system",
                "seed_data",
                "SYSTEM",
                json_value({
                    "workers_created": workers_created,
                    "patients_created": patients_created,
                    "assessments_created": assessments_created
                })
            )
        )

        db.commit()

        cursor.close()


        # ====================================================================
        # SUMMARY
        # ====================================================================

        print()
        print("=" * 70)
        print("SEED COMPLETE")
        print("=" * 70)

        print(
            f"Workers created     : {workers_created}"
        )

        print(
            f"Patients created    : {patients_created}"
        )

        print(
            f"Assessments created : {assessments_created}"
        )

        print()
        print("DEMO LOGIN CREDENTIALS")
        print("-" * 45)

        print(
            "HW-DEMO-001   | Demo Health Worker | PIN: 1234"
        )

        print(
            "HW-MH-0042    | Priya Sharma       | PIN: 5678"
        )

        print(
            "DOC-MH-001    | Dr. Rajesh Mehta   | PIN: 9999"
        )

        print(
            "ADMIN-001     | System Administrator| PIN: 0000"
        )

        print()
        print(
            f"App: http://{config.HOST}:{config.PORT}"
        )

        print("=" * 70)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    seed()