# Sahaay Clinic — Backend Setup Guide

**AI-Powered Virtual Rural Clinic** · Python + Flask + SQLAlchemy + OpenAI

---

## Quick Start (5 minutes)

```bash
# 1. Clone / navigate to the project
cd sahaay-clinic/backend

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file from the template
cp ../.env.example .env
# → Open .env and fill in your values (see Section 2 below)

# 5. Seed the database with demo data
python seed_data.py

# 6. Start the server
python app.py
# → Server running at http://localhost:5000
# → Open http://localhost:5000 in your browser
```

**Demo login:** Worker ID `HW-DEMO-001` · PIN `1234`

---

## 1. Project Structure

```
sahaay-clinic/
├── .env.example          ← Copy this to .env and fill in your values
├── .gitignore            ← .env is excluded from Git
│
├── backend/
│   ├── app.py            ← Flask app factory (entry point)
│   ├── config.py         ← Reads .env into typed Python config
│   ├── database.py       ← SQLAlchemy init
│   ├── models.py         ← DB tables: HealthWorker, Patient, Assessment, ...
│   ├── seed_data.py      ← Seeds demo data (run once after setup)
│   ├── requirements.txt  ← Python dependencies
│   │
│   ├── routes/
│   │   ├── auth.py       ← POST /api/v1/auth/login + /logout
│   │   ├── patients.py   ← GET/POST /api/v1/patients/*
│   │   ├── assessment.py ← POST /api/v1/assessment
│   │   ├── sync.py       ← POST /api/v1/sync/batch
│   │   ├── doctor.py     ← GET/POST /api/v1/doctor/*
│   │   └── teleconsult.py← POST /api/v1/teleconsult/request
│   │
│   └── services/
│       ├── ai_service.py ← OpenAI triage + rule-based fallback
│       └── auth_service.py← bcrypt PIN hashing + JWT helpers
│
└── (frontend files: index.html, intake.html, etc.)
```

---

## 2. Environment Variables (.env)

Copy `.env.example` to `.env` then set these values:

### Required

| Variable | Example | Description |
|---|---|---|
| `SECRET_KEY` | `abc123...` | Random 64-char string. Run: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_SECRET_KEY` | `xyz789...` | Another random string for JWT signing |

### AI Triage (OpenAI)

| Variable | Example | Description |
|---|---|---|
| `OPENAI_API_KEY` | `sk-proj-xxx` | Your OpenAI API key. Get one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys). **Leave empty** to use the rule-based fallback engine (works offline, no cost). |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model to use. `gpt-4o-mini` is recommended (fast & cheap). |
| `OPENAI_TEMPERATURE` | `0.2` | Keep low (0.1-0.3) for consistent medical responses. |

### Database

| Variable | Example | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///sahaay_clinic.db` | SQLite for dev (no setup needed). Switch to PostgreSQL for production. |

### SMS Alerts (Twilio — Optional)

| Variable | Example | Description |
|---|---|---|
| `TWILIO_ACCOUNT_SID` | `ACxxx...` | From your Twilio console. Leave empty to disable SMS. |
| `TWILIO_AUTH_TOKEN` | `your_token` | From your Twilio console. |
| `TWILIO_PHONE_NUMBER` | `+1234567890` | Your Twilio phone number. |

### All defaults work out-of-the-box for development. Only `SECRET_KEY` and `JWT_SECRET_KEY` must be changed before going to production.

---

## 3. API Endpoints

All routes are prefixed with `/api/v1/`

### Authentication

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/auth/login` | `{worker_id, pin}` | Login, get JWT token |
| `POST` | `/auth/logout` | — | Logout (client deletes token) |

**Login Response:**
```json
{
  "success": true,
  "name": "Demo Health Worker",
  "role": "health_worker",
  "token": "eyJhbGci...",
  "refresh_token": "eyJhbGci..."
}
```

### Patients

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/patients/queue` | Today's patient queue |
| `POST` | `/patients/register` | Register a new patient |
| `GET` | `/patients/<patient_id>` | Get patient by QR Health ID |

**Register Patient Body:**
```json
{
  "name": "Ramesh Kumar",
  "age": 45,
  "gender": "Male",
  "phone": "9876543210",
  "chiefComplaint": "Fever for 3 days",
  "vitals": {
    "temperature": 38.8,
    "bpSystolic": 120, "bpDiastolic": 80,
    "spo2": 97, "pulseRate": 88
  }
}
```

### AI Triage Assessment

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/assessment` | Submit vitals + symptoms for AI triage |

**Assessment Body:**
```json
{
  "patientId": "SAH-MH-LZ4K8A-X7F",
  "symptoms": ["Fever", "Chills", "Headache"],
  "vitals": { "temperature": 39.2, "spo2": 97 },
  "chiefComplaint": "Fever with chills for 3 days",
  "age": 45,
  "gender": "Male"
}
```

**Assessment Response:**
```json
{
  "success": true,
  "condition": "Suspected Malaria",
  "urgency": "high",
  "confidence": "Medium (50-80%)",
  "recommendations": ["Perform RDT for malaria", "..."],
  "reasoning": "Cyclical fever with chills...",
  "refer_immediately": false,
  "source": "openai"
}
```

> **Note:** `source` is `"openai"` when OpenAI is configured, or `"rule_based"` when using the fallback engine.

### Doctor Portal

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/doctor/pending` | List assessments awaiting verification |
| `POST` | `/doctor/verify` | Submit doctor's approval/modification |

**Verify Body:**
```json
{
  "case_id": "SAH-MH-LZ4K8A-X7F",
  "decision": "approve",
  "diagnosis": "P. falciparum Malaria (confirmed RDT+)",
  "treatmentPlan": "Artemether-Lumefantrine 80/480mg...",
  "doctorName": "Dr. R. Mehta / REG-MH-001",
  "specialty": "General Practice"
}
```

### Offline Sync

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/sync/batch` | Sync a batch of offline-queued records |

### Teleconsult

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/teleconsult/request` | Create Jitsi Meet session for patient |

---

## 4. Authentication

All protected endpoints expect a JWT token in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

The frontend stores this token in IndexedDB and sends it with every request via `api.js`.

> Routes decorated with `@jwt_required(optional=True)` also work without a token (for offline/demo use).

---

## 5. Production Deployment

```bash
# Use gunicorn instead of Flask's dev server
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 "app:create_app()"
```

**Production checklist:**
- [ ] Set `FLASK_ENV=production` in `.env`
- [ ] Set `FLASK_DEBUG=0` in `.env`
- [ ] Generate strong random values for `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Switch `DATABASE_URL` from SQLite to PostgreSQL
- [ ] Set `CORS_ORIGINS` to your actual domain(s)
- [ ] Enable HTTPS (use nginx or a reverse proxy in front of gunicorn)
- [ ] Set `LOG_FILE=logs/sahaay_clinic.log`

---

## 6. Database Management

```bash
# Reset the database (drops all tables and recreates them)
python -c "from app import create_app; from database import reset_db; reset_db(create_app())"

# Re-run the seeder after reset
python seed_data.py
```

---

## 7. Testing API Manually

Install `httpie` for easy command-line testing:

```bash
pip install httpie

# Login
http POST http://localhost:5000/api/v1/auth/login \
  worker_id="HW-DEMO-001" pin="1234"

# Get patient queue (replace TOKEN with the token from login)
http GET http://localhost:5000/api/v1/patients/queue \
  "Authorization: Bearer TOKEN"

# Submit triage assessment
http POST http://localhost:5000/api/v1/assessment \
  patientId="SAH-MH-DEMO-001" \
  symptoms:='["Fever","Chills"]' \
  age:=45 gender="Male"
```

---

## 8. Clinical Safety Notes

- All AI assessments are labelled as `"source": "openai"` or `"source": "rule_based"` so the frontend can display the appropriate **amber ⚠️ "AI Draft (Unverified)"** badge.
- The doctor verification endpoint (`POST /api/v1/doctor/verify`) is the **green badge** event — only after a doctor explicitly approves a case should it be treated as clinically verified.
- AI prompts are engineered to be **conservative** — when in doubt, the AI recommends referral.
- The full OpenAI raw response is saved to `ai_raw_response` in the `assessments` table for audit purposes.
- All actions are logged to the `audit_logs` table for compliance and debugging.

---

*Sahaay Clinic Backend — Built for the AI-Powered Rural Health Hackathon*
