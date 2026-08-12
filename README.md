# 🏥 Sahaay Clinic

> **AI-Powered Virtual Rural Clinic --- Offline-First Healthcare
> Assistance for Remote Communities**

Sahaay Clinic is an **offline-first virtual clinic platform** designed
for rural healthcare centres where qualified doctors may not be
available every day and internet connectivity can be unreliable.

The platform helps a trained health worker **capture patient
information, record vitals, organize medical records, perform
preliminary AI-assisted triage, follow protocol-based first-aid
guidance, and connect cases to a qualified remote doctor when
professional medical attention is required.**

> **Core Principle:** Sahaay assists healthcare workers --- it does
> **not** replace a qualified doctor.

------------------------------------------------------------------------

## 🌍 The Problem

Many rural communities have a basic health centre and a trained health
worker, but may not have a doctor available every day. A patient may
arrive with symptoms such as fever, weakness, or a minor injury, while
the nearest hospital may be several hours away.

The challenge is therefore not simply "providing an AI diagnosis."

The real challenge is building a system that can:

-   work in **low-network and offline environments**
-   help a health worker collect structured patient information
-   organize scattered medical documents and history
-   provide **preliminary, safety-checked assistance**
-   identify cases that should be escalated
-   preserve patient records locally until connectivity returns
-   make remote doctor review faster and more organized
-   clearly separate **AI suggestions from doctor-approved decisions**

Sahaay Clinic is designed around this workflow:

``` text
Patient
   ↓
Health Worker
   ↓
Patient Intake + Vitals
   ↓
Sahaay Preliminary Triage
   ↓
┌───────────────────────────────┐
│                               │
├── Low / Minor → Protocol Care │
│                               │
├── Moderate → Doctor Queue     │
│                               │
└── High Risk → Hospital Referral
                ↓
         Qualified Doctor
                ↓
       Verified Decision
```

------------------------------------------------------------------------

# 💡 What Makes Sahaay Different?

Sahaay Clinic is built around a **Care Gate** rather than treating AI
output as a final diagnosis.

### 🟡 AI Preliminary Layer

The system can generate:

-   structured patient summaries
-   preliminary triage signals
-   risk flags
-   protocol-based assistance
-   organized case information for doctor review

Every such output is clearly marked:

> **AI Draft --- Unverified**

### 🟢 Doctor-Verified Layer

A qualified doctor reviews the case and can:

-   modify the preliminary assessment
-   conduct a remote consultation
-   approve the medical decision
-   issue/authorize a prescription where appropriate
-   recommend hospital referral

The final state is clearly marked:

> **Doctor Approved --- Verified**

This visual boundary is one of the core safety features of Sahaay
Clinic.

------------------------------------------------------------------------

# ✨ Core Features

## 1. 👨‍⚕️ Health Worker Dashboard

The dashboard is the main working area for the village health worker.

### Includes

-   patient queue
-   patient status tracking
-   today's patient statistics
-   pending doctor reviews
-   high-risk/referral alerts
-   online/offline network status
-   quick access to new patient intake
-   callback/telephony requests as an integration point

### Example Patient States

``` text
Registered
    ↓
Vitals Recorded
    ↓
AI Assessed
    ↓
Pending Doctor Review
    ↓
Doctor Approved / Completed
```

Or:

``` text
High-Risk Detected
       ↓
Emergency / Hospital Referral
```

------------------------------------------------------------------------

# 📝 2. Patient Intake & Sahaay Assessment

The intake workflow allows a health worker to capture the information
required for a preliminary assessment.

### Patient Information

-   Patient name
-   Age
-   Relevant demographic information
-   Preferred language
-   Symptoms
-   Symptom duration
-   Basic medical history
-   Existing prescriptions
-   Previous medical reports

### Vitals

The system can collect information such as:

-   Temperature
-   Blood pressure
-   Pulse / heart rate
-   Oxygen saturation (SpO₂)
-   Other relevant observations

### Voice Input

The application can use the browser's native speech capabilities for
voice-based symptom entry where supported.

This is particularly useful when a health worker needs to quickly record
symptoms in a local language.

### Medical Documents

The planned intake workflow supports capturing:

-   prescriptions
-   medical reports
-   hospital documents
-   other relevant patient records

OCR can be used to extract text from supported documents.

### Visual Symptom Capture

The health worker can capture images of visible minor injuries or
symptoms for later review.

Images can be compressed before local storage/synchronization to reduce
storage and bandwidth requirements.

------------------------------------------------------------------------

# 🤖 3. AI-Assisted Preliminary Triage

Sahaay does not present its preliminary assessment as a doctor's
diagnosis.

The AI layer is intended to transform collected information into a
**structured case summary and preliminary risk assessment**.

### Example Output

``` text
PATIENT SUMMARY
Age: 42
Symptoms: Fever, weakness
Duration: 3 days
SpO₂: 97%
Pulse: Recorded
Temperature: Recorded

AI STATUS
🟡 AI Draft — Unverified

Preliminary Assessment:
Structured case summary generated for qualified doctor review.

NEXT ACTION
→ Continue protocol-based care where appropriate
→ OR request doctor consultation
→ OR escalate if risk indicators are detected
```

### Emergency Risk Layer

The system can apply defined rules to identify potentially high-risk
situations.

For example, the supplied project specification describes emergency
flags for critical vital-sign conditions and immediate referral prompts.

When a high-risk condition is detected, the system should prioritize:

> 🔴 **Professional medical attention / hospital referral**

rather than attempting to independently manage the condition.

------------------------------------------------------------------------

# 🩹 4. Protocol-Based First-Aid Guidance

Sahaay includes an offline reference area for trained health workers.

It can provide structured, step-by-step guidance for appropriate minor
conditions such as:

-   wound cleaning
-   dressing / bandage application
-   burns
-   dehydration-related support
-   fever/pain guidance
-   insect-related incidents
-   other locally defined first-aid protocols

The purpose is to help the health worker follow a **defined protocol**,
not to encourage unrestricted self-medication.

### OTC Safety

Where legally and clinically appropriate, the system can provide
safety-checked information for selected over-the-counter medicines.

The workflow should include:

-   age/weight checks where relevant
-   allergy/contraindication checks
-   warning messages
-   safety limits
-   clear escalation when the case is outside the supported protocol

Prescription-only medicines should remain behind the qualified-doctor
workflow.

------------------------------------------------------------------------

# 📞 5. Remote Doctor Consultation

When a case requires professional attention, Sahaay moves it into the
doctor workflow.

### Doctor Dashboard

A remote doctor can review:

-   patient details
-   current vitals
-   symptoms
-   medical history
-   previous records
-   uploaded documents
-   captured images
-   AI-generated preliminary summary
-   risk/severity status

### Consultation

The architecture supports remote communication using:

-   video/audio consultation where network conditions allow
-   audio-first communication for lower bandwidth
-   asynchronous voice notes / store-and-forward workflows when
    connectivity is unstable

The goal is to make the system useful even when a continuous
high-bandwidth video connection is not possible.

------------------------------------------------------------------------

# 🧾 6. Doctor Approval & Prescription Workflow

The doctor is the final decision-maker in the professional medical
workflow.

``` text
AI Draft
   ↓
Doctor Review
   ↓
Doctor Modification (if required)
   ↓
Doctor Approval
   ↓
Verified Medical Decision
```

### Safety Lock

Actions such as final prescription issuance/printing should remain
unavailable until the qualified doctor completes the required approval
workflow.

This prevents an **AI-generated preliminary suggestion from being
visually or functionally mistaken for an authorized medical decision.**

------------------------------------------------------------------------

# 🗂️ 7. Digital Patient Records (EHR)

Sahaay can maintain a searchable local patient history.

Records can be searched using supported identifiers such as:

-   Patient ID
-   Name
-   Phone number
-   QR-based patient identifier

### Patient Timeline

A patient record can organize:

``` text
Patient Profile
      ↓
Visit 1
  ├─ Symptoms
  ├─ Vitals
  ├─ Reports
  └─ Doctor Decision

Visit 2
  ├─ Symptoms
  ├─ Vitals
  └─ Doctor Decision

Visit 3
  └─ ...
```

This gives the health worker and doctor a clearer view of the patient's
previous interactions with the clinic.

------------------------------------------------------------------------

# 📱 8. "Snap & Sync" Offline QR Health ID

A key innovation in the Sahaay workflow is an **Offline QR Health ID**.

A patient can be associated with a unique local identifier represented
through a QR code.

### Workflow

``` text
Create Patient
      ↓
Generate Local Patient ID
      ↓
QR Health ID
      ↓
Patient Returns
      ↓
Scan QR
      ↓
Retrieve Local Record
```

The QR workflow is designed to help retrieve a locally stored patient
profile even when the clinic has no internet connection.

> The QR identifier should not expose unnecessary sensitive medical
> information directly inside the QR code. It should act primarily as an
> identifier for the locally stored record.

------------------------------------------------------------------------

# 📶 9. Offline-First Architecture

Offline support is not an optional feature in Sahaay.

It is a core design requirement because rural clinics may experience:

-   unstable connectivity
-   slow mobile networks
-   temporary internet outages
-   complete loss of internet access

### Service Worker

`sw.js` caches the application shell so that the core frontend can
continue loading offline.

### IndexedDB

IndexedDB stores local application data such as:

-   patient profiles
-   consultations
-   queue information
-   preliminary drafts
-   offline records
-   synchronization tasks

### Sync Queue

When the network is unavailable:

``` text
Health Worker Saves Record
          ↓
       IndexedDB
          ↓
      Sync Queue
          ↓
      WAIT OFFLINE
          ↓
Connection Returns
          ↓
     Backend Sync
```

This prevents the health worker from losing work simply because the
internet disappears.

------------------------------------------------------------------------

# 🔄 10. Low-Bandwidth & Store-and-Forward Design

Sahaay is designed with the assumption that connectivity may be
unreliable.

Instead of depending entirely on live communication, important case
information can be stored locally and synchronized later.

### Connection Strategy

``` text
GOOD CONNECTION
→ Live doctor communication

LOW CONNECTION
→ Audio-first / lightweight communication

NO CONNECTION
→ Local storage + sync queue

CONNECTION RETURNS
→ Automatic synchronization
```

This architecture makes the application more practical for rural
environments than a system that depends on continuous video
connectivity.

------------------------------------------------------------------------

# ☎️ 11. Villager Voice / Toll-Free Access --- Planned Integration

A future extension of Sahaay can allow villagers with ordinary keypad
phones to contact the village health worker through a toll-free/voice
system.

Possible workflow:

``` text
Villager's Keypad Phone
        ↓
   Voice / IVR System
        ↓
Basic Information / Voice Message
        ↓
Backend Processing
        ↓
Priority Detection
        ↓
Health Worker Queue
        ↓
Callback / Consultation
```

The supplied system design also considers:

-   multilingual IVR
-   DTMF keypad options
-   recorded voice messages
-   speech-to-text
-   priority tagging
-   health-worker callback requests
-   emergency call routing

This is an **integration concept**, not part of the current
frontend-only prototype.

------------------------------------------------------------------------

# 🏗️ System Architecture

``` text
                 ┌───────────────────────────┐
                 │       Sahaay Clinic       │
                 │   HTML + CSS + Vanilla JS │
                 └─────────────┬─────────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
        Web APIs          IndexedDB         Service Worker
      Camera / Voice       Local EHR        Offline Cache
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                        Offline / Low Net
                               │
                               ▼
                      ┌─────────────────┐
                      │   Sync Queue    │
                      └────────┬────────┘
                               │
                         When Online
                               │
                               ▼
                   ┌──────────────────────┐
                   │ Python / Flask       │
                   │ Backend (Planned)    │
                   └──────────┬───────────┘
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
        AI Services       Central EHR      Doctor Portal
        / AI Engine       / Database       / Consultation
```

The current frontend prototype deliberately avoids putting secrets or
third-party service credentials in browser code.

------------------------------------------------------------------------

# 📄 Application Pages

Sahaay's functional modules are organized into user-facing workflows
rather than making every technical module a separate page.

## Page 1 --- Clinic Queue & Health Worker Dashboard

**Primary user:** Village Health Worker

Includes:

-   clinic queue
-   patient status
-   network status
-   emergency flags
-   pending doctor reviews
-   new patient registration
-   callback requests

**Modules:** EHR & Queue Management + Offline Sync

------------------------------------------------------------------------

## Page 2 --- Patient Intake & AI Assessment

**Primary user:** Village Health Worker

Includes:

-   patient details
-   symptoms
-   vitals
-   voice input
-   document/image capture
-   QR workflow
-   preliminary AI summary
-   risk flags
-   doctor consultation request

**Modules:** Intake + AI/Risk + EHR + Offline Sync

------------------------------------------------------------------------

## Page 3 --- First-Aid & Protocol Guide

**Primary user:** Village Health Worker

Includes:

-   protocol search
-   first-aid steps
-   supported OTC safety guidance
-   warning/contraindication checks
-   offline access

**Modules:** First-Aid/OTC + Offline Sync

------------------------------------------------------------------------

## Page 4 --- Patient Health Records

**Primary users:** Health Worker / Clinic Administrator

Includes:

-   patient search
-   QR lookup
-   patient timeline
-   previous visits
-   reports
-   doctor notes
-   approved prescription/record printing

**Modules:** EHR + Offline Sync

------------------------------------------------------------------------

## Page 5 --- Remote Doctor Portal

**Primary user:** Qualified Remote Doctor

Includes:

-   patient review queue
-   risk severity filtering
-   full patient summary
-   medical history
-   AI preliminary assessment
-   reports/images
-   consultation interface
-   prescription/decision workflow
-   doctor approval

**Modules:** AI/Risk + Doctor Consultation + EHR + Offline Sync

------------------------------------------------------------------------

# 🔗 Module-to-Page Mapping

  -----------------------------------------------------------------------
  Module                  Main Purpose            Pages
  ----------------------- ----------------------- -----------------------
  Patient Intake & Data   Collect patient         Page 2
  Capture                 information             

  AI Diagnostic / Risk    Preliminary summary &   Pages 2, 5
  Engine                  risk signals            

  First-Aid / OTC         Protocol-based support  Page 3
  Guidance                                        

  Remote Doctor           Professional review     Page 5
  Consultation                                    

  EHR & Queue Management  Records and patient     Pages 1, 2, 4, 5
                          flow                    

  Offline Sync Engine     Offline storage and     Background across the
                          synchronization         app
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 🛠️ Technology Stack

## Frontend

-   **HTML5**
-   **CSS3**
-   **Vanilla JavaScript**

The project intentionally avoids frontend frameworks such as:

-   React
-   Vue
-   Angular
-   TypeScript
-   Tailwind
-   Bootstrap
-   Firebase

## Offline Technologies

-   Service Worker
-   Cache Storage
-   IndexedDB
-   Browser Web APIs

## Backend Architecture

A **Python/Flask backend** is planned for server-side communication.

Frontend communication should use relative routes such as:

``` javascript
fetch('/api/v1/assessment')
```

No API secrets should be placed inside frontend JavaScript.

------------------------------------------------------------------------

# 📁 Project Structure

``` text
sahaay-clinic/
│
├── index.html
├── intake.html
├── firstaid.html
├── doctor.html
│
├── manifest.json
├── sw.js
│
├── css/
│   └── style.css
│
├── js/
│   ├── app.js
│   └── api.js
│
└── data/
    └── protocols.json
```

### File Responsibilities

  -----------------------------------------------------------------------
  File                                Responsibility
  ----------------------------------- -----------------------------------
  `index.html`                        Login/dashboard/queue interface

  `intake.html`                       Patient intake, vitals, QR and
                                      preliminary assessment

  `firstaid.html`                     Offline protocol and first-aid
                                      guidance

  `doctor.html`                       Remote doctor review and approval

  `style.css`                         Responsive dark UI

  `app.js`                            UI logic + IndexedDB operations

  `api.js`                            Centralized backend request
                                      wrappers

  `sw.js`                             Offline application-shell caching

  `manifest.json`                     PWA configuration

  `protocols.json`                    Offline protocol data
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 🎨 UI/UX Design

Sahaay uses a **simple dark-theme interface** designed for long working
sessions.

### Design Goals

-   high readability
-   clear hierarchy
-   large touch targets
-   responsive layouts
-   minimal visual clutter
-   obvious warning states
-   mobile-first health-worker workflow
-   desktop-friendly doctor dashboard

### Responsive Layout

``` text
Mobile
< 600px
→ Single-column workflow

Tablet
600–1024px
→ Two-column workflow

Desktop
> 1024px
→ Multi-pane doctor dashboard
```

------------------------------------------------------------------------

# 🌐 Multilingual Accessibility

Rural healthcare requires language accessibility.

The application can provide multilingual support through the specified
translation approach and browser speech capabilities.

The goal is to make patient intake and instructions easier to understand
for health workers and patients who may not be comfortable using
English.

------------------------------------------------------------------------

# 🔐 Security & Privacy Principles

Sahaay handles sensitive healthcare information, so privacy must be
treated as a first-class requirement.

### Frontend Rules

-   No hardcoded API keys
-   No exposed backend secrets
-   No cloud credentials in JavaScript
-   Use HTTPS when deployed
-   Store only necessary local data
-   Restrict access to authorized health workers/doctors in the
    production backend
-   Treat locally stored patient data as sensitive
-   Avoid placing full medical information inside QR codes

### AI Safety

The system must clearly communicate:

> **AI output is preliminary and unverified.**

A qualified doctor remains responsible for professional medical
decisions.

------------------------------------------------------------------------

# ⚠️ Clinical Safety Boundary

Sahaay Clinic is an **AI-assisted healthcare support prototype**, not an
autonomous medical professional.

The application should:

-   assist trained health workers
-   organize information
-   highlight defined risk conditions
-   provide protocol-based guidance
-   facilitate professional review

It should **not**:

-   present AI output as a confirmed diagnosis
-   independently authorize prescriptions
-   replace qualified medical professionals
-   delay emergency referral when defined high-risk conditions are
    detected
-   encourage unsafe self-medication

The current frontend prototype's triage logic is a demonstration of the
workflow and must not be used for real-world clinical decision-making
without appropriate clinical validation.

------------------------------------------------------------------------

# 🔄 Complete Patient Journey

``` text
┌───────────────────────┐
│ Patient Arrives       │
└──────────┬────────────┘
           ↓
┌───────────────────────┐
│ Health Worker Intake  │
│ Symptoms + History    │
│ Vitals + Documents    │
└──────────┬────────────┘
           ↓
┌───────────────────────┐
│ Sahaay Preliminary    │
│ Assessment            │
└──────────┬────────────┘
           ↓
      ┌────┴─────┐
      ↓          ↓
   Minor      Risk / Need
      ↓        Doctor
Protocol Care    ↓
      │      Doctor Queue
      │          ↓
      │    Remote Consultation
      │          ↓
      │    Doctor Verification
      │          ↓
      └──────┬───┘
             ↓
      Verified Record
             ↓
      Patient History
```

------------------------------------------------------------------------

# 📡 Offline Patient Journey

Even when the clinic loses internet:

``` text
Patient Intake
     ↓
Local IndexedDB
     ↓
AI / Rule-Based Local Assistance
     ↓
Local Queue
     ↓
Record Saved
     ↓
Internet Returns
     ↓
Sync Queue
     ↓
Backend
     ↓
Doctor / Central System
```

This **offline-first approach** is central to the project's
rural-healthcare design.

------------------------------------------------------------------------

# 🚀 Local Development

For the frontend prototype, serve the project through a local HTTP
server rather than opening HTML files directly.

Example:

``` bash
python -m http.server 8000
```

Then open:

``` text
http://localhost:8000
```

A local HTTP server is important for browser features such as Service
Workers and PWA behavior.

------------------------------------------------------------------------

# 🧪 Prototype vs Production

### Current Prototype

The current Sahaay frontend focuses on:

-   interface and workflow
-   local IndexedDB storage
-   offline caching
-   patient queue
-   intake workflow
-   preliminary assessment UI
-   first-aid protocol UI
-   doctor review UI
-   safety-state visualization

### Future Production Integrations

A production system could connect a secure backend to:

-   validated AI services
-   central EHR/database
-   authenticated doctor accounts
-   secure teleconsultation
-   cloud synchronization
-   OCR services
-   speech processing
-   approved telephony/IVR infrastructure

These integrations should remain **server-side** so credentials and
sensitive service keys are not exposed in frontend code.

------------------------------------------------------------------------

# 🏆 Why Sahaay Clinic Matters

Sahaay is not just another AI chatbot.

Its goal is to create a **complete rural-care workflow**:

``` text
CAPTURE
   ↓
UNDERSTAND
   ↓
TRIAGE
   ↓
ASSIST
   ↓
ESCALATE
   ↓
CONSULT
   ↓
VERIFY
   ↓
RECORD
   ↓
SYNC
```

The strongest part of the concept is the combination of:

**AI assistance + human health workers + qualified doctors +
offline-first technology + structured records + safety guardrails.**

Instead of asking:

> "Can AI replace a doctor?"

Sahaay asks:

> **"How can technology help a rural health worker reach the right level
> of care faster and more reliably?"**

------------------------------------------------------------------------

# 🧭 Future Roadmap

## Phase 1 --- Frontend Prototype

-   [x] Responsive interface
-   [x] Health-worker workflow
-   [x] Patient intake
-   [x] Preliminary AI-state UI
-   [x] Doctor review workflow
-   [x] Offline architecture

## Phase 2 --- Backend

-   [ ] Flask API
-   [ ] Authentication and authorization
-   [ ] Secure central database
-   [ ] Patient synchronization
-   [ ] Doctor accounts
-   [ ] Secure audit logs

## Phase 3 --- Intelligence

-   [ ] Validated clinical AI services
-   [ ] Medical document processing
-   [ ] Multilingual speech processing
-   [ ] Improved patient-history summarization
-   [ ] Clinically validated risk rules

## Phase 4 --- Rural Connectivity

-   [ ] Low-bandwidth teleconsultation
-   [ ] Voice-first communication
-   [ ] Toll-free/IVR integration
-   [ ] SMS fallback
-   [ ] Store-and-forward consultation

------------------------------------------------------------------------

# 👥 Intended Users

### 🧑‍⚕️ Village Health Worker

Primary field user who:

-   registers patients
-   records symptoms and vitals
-   captures documents/images
-   follows supported protocols
-   manages the local queue
-   requests doctor review

### 👨‍⚕️ Qualified Remote Doctor

Professional reviewer who:

-   reviews patient cases
-   checks AI preliminary summaries
-   consults the health worker
-   modifies assessments
-   approves medical decisions
-   handles escalation/referral

### 🧑 Villager / Patient

The patient benefits from:

-   faster initial assessment
-   better organization of health information
-   access to remote professional review
-   improved continuity of records
-   potential voice/toll-free access in future versions

------------------------------------------------------------------------

# 🧩 Design Philosophy

Sahaay follows five principles:

### 1. Offline First

If the network disappears, the core workflow should not disappear with
it.

### 2. Human in the Loop

AI assists; qualified professionals make medical decisions.

### 3. Safety Before Automation

High-risk cases should be escalated instead of being unnecessarily
automated.

### 4. Simple for the Field

The health worker interface should be understandable without requiring
advanced technical knowledge.

### 5. Build for Real Constraints

The system is designed around rural realities: limited connectivity,
limited devices, multilingual users, and limited access to doctors.

------------------------------------------------------------------------

# 📜 Project Status

**Sahaay Clinic is currently a hackathon/academic frontend prototype.**

The project demonstrates the intended user experience, offline-first
architecture, patient workflow, AI-assistance boundary, and
remote-doctor workflow.

It is **not a certified medical device, emergency service, or
replacement for professional medical care.**

------------------------------------------------------------------------

# ❤️ Built for Accessible Rural Healthcare

> **Sahaay Clinic --- From the first symptom to the right level of
> care.**

Built with:

**HTML5 • CSS3 • Vanilla JavaScript • IndexedDB • Service Worker • PWA
Architecture • Python/Flask-ready API Design**
