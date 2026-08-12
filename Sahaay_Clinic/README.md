# Sahaay Clinic

A beginner-friendly, offline-first frontend prototype for an AI-assisted rural virtual clinic.

## Core idea: the Sahaay Care Gate

Sahaay does not let a preliminary AI layer become the final medical decision.

**Health Worker → Patient Intake → Preliminary Sahaay Triage → Care Queue → Doctor Review → Verified Decision**

The key innovation is the visible separation between:

- **Preliminary layer:** structured patient summary + demo triage signal.
- **Verified layer:** doctor note and final approval/referral.

This is intentionally a frontend prototype. It does not diagnose, prescribe, call patients, or connect to external AI/telephony services.

## Files

- `index.html` — app shell and navigation
- `style.css` — responsive UI
- `app.js` — all frontend logic + IndexedDB
- `sw.js` — offline cache
- `manifest.json` — PWA metadata

## Run

For the best PWA/offline behavior, serve the folder through a local HTTP server.

Example with Python:

```bash
python -m http.server 8000
```

Then open:

`http://localhost:8000`

## No frontend APIs

There are no external fetch/API calls, API keys, cloud SDKs, telephony credentials, or AI service calls in the frontend.

Backend integrations can be connected later behind a Flask backend without exposing secrets to this frontend.

## Safety

This is a hackathon prototype, not a medical device or emergency service. The demo triage rule is only a UI demonstration and must not be used for real clinical decisions.
