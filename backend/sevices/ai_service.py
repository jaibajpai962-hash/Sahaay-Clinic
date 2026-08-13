"""
==============================================================================
FILE: backend/services/ai_service.py  —  AI Triage Assessment Engine
==============================================================================
This service handles AI triage requests. It supports Google Gemini (preferred
when `GEMINI_API_KEY` is present, with a deterministic rule-based fallback
for offline operation.

Design notes:
- All AI outputs are considered drafts and must be verified by a clinician.
- The AI is instructed to return a single JSON object in a strict schema.
- Gemini client library is optional; a lightweight REST fallback is provided
  to avoid pulling heavy transitive dependencies when not desired.
"""

import json
import logging
import re
from dotenv import load_dotenv

# Ensure .env values are loaded into the environment (override any existing)
load_dotenv(override=True)

logger = logging.getLogger('sahaay.ai')


# SYSTEM PROMPT: instruct the model and require a strict JSON response
SYSTEM_PROMPT = """You are a clinical decision support AI assistant for Sahaay Clinic, an AI-powered rural health clinic in India.

YOUR ROLE:
- You help health workers (ASHAs, ANMs) perform initial patient triage in under-resourced rural settings.
- You are a DECISION SUPPORT TOOL only — NOT a replacement for a licensed doctor.
- Your output is always labelled as an "AI Draft (Unverified)" and must be reviewed by a doctor before any treatment.

CLINICAL GUIDELINES:
- Be CONSERVATIVE. When in doubt, recommend referral to a higher facility.
- Prioritise patient safety over making a confident diagnosis.
- Use standard WHO/MOHFW guidelines relevant to rural India.
- Consider the limited resources available at a primary health centre.
- Flag any red-flag symptoms immediately.

OUTPUT FORMAT:
You MUST respond ONLY with a valid JSON object in exactly this structure:
{
  "condition": "Most likely condition name (or 'Insufficient information')",
  "urgency": "critical" | "high" | "moderate" | "low",
  "confidence": "High (>80%)" | "Medium (50-80%)" | "Low (<50%)",
  "recommendations": ["action 1", "action 2", "action 3"],
  "medicine_suggestions": ["general supportive/OTC option to discuss with a doctor; no prescription or dosage"],
  "reasoning": "Brief clinical reasoning in 2-3 sentences. Mention which symptoms drove the assessment.",
  "red_flags_present": ["list any red-flag symptoms found"],
  "refer_immediately": true | false,
  "key_points": ["3-5 brief bullet points summarising the case for the reviewing doctor"]
}

URGENCY DEFINITIONS:
- critical: Life-threatening. Immediate emergency transport required.
- high:     Urgent. Doctor review within 1 hour. May need higher facility.
- moderate: Non-urgent but needs attention today. OTC management possible.
- low:      Routine. Preventive/supportive care. Follow-up in 1-2 weeks.

Do NOT include any text outside the JSON object. Do NOT add markdown code fences."""


# ------------------------------
# Main triage entrypoint
# ------------------------------
def run_triage_assessment(triage_data: dict) -> dict:
    """
    Run an AI triage assessment. Preference order:
      1) Gemini API (GEMINI_API_KEY)
      2) Rule-based fallback (always available)

    Returns the structured assessment dict.
    """
    from config import config

    # Prefer Gemini when present
    if getattr(config, 'GEMINI_API_KEY', None):
        try:
            return _run_gemini_assessment(triage_data, config)
        except Exception as exc:
            # HTTP client exceptions can include a query string containing the
            # Gemini key. Do not write exception text to application logs.
            logger.warning("Gemini assessment failed (%s); using offline fallback.", type(exc).__name__)

    # Always available offline fallback
    return _run_rule_based_assessment(triage_data)


# ------------------------------
# Gemini adapter (client library preferred, REST fallback available)
# ------------------------------
def _run_gemini_assessment(triage_data: dict, config) -> dict:
    """Call Gemini through the stable REST API. Handles both `models/x` and `x`."""
    return _run_gemini_via_rest(triage_data, config)


def _run_gemini_via_rest(triage_data: dict, config) -> dict:
    import requests
    import os

    api_key = os.getenv('GEMINI_API_KEY') or getattr(config, 'GEMINI_API_KEY', '')
    if not api_key:
        raise RuntimeError('GEMINI_API_KEY is not configured')

    model = (os.getenv('GEMINI_MODEL') or getattr(config, 'GEMINI_MODEL', '')).strip()
    if not model:
        model = 'models/gemini-3.1-flash-lite'
    if model.startswith('https://'):
        url = model
    else:
        model_path = model if model.startswith('models/') else f'models/{model}'
        url = f'https://generativelanguage.googleapis.com/v1beta/{model_path}:generateContent'

    user_message = _build_patient_context(triage_data)
    payload = {
        'systemInstruction': {'parts': [{'text': SYSTEM_PROMPT}]},
        'contents': [{'role': 'user', 'parts': [{'text': user_message}]}],
        'generationConfig': {
            'temperature': float(getattr(config, 'GEMINI_TEMPERATURE', 0.1)),
            'maxOutputTokens': int(getattr(config, 'GEMINI_MAX_TOKENS', 700)),
            'responseMimeType': 'application/json',
        },
    }

    logger.info('Calling Gemini REST model: %s', model)
    resp = requests.post(url, params={'key': api_key}, json=payload, timeout=int(getattr(config, 'GEMINI_TIMEOUT', 45)))
    if not resp.ok:
        # Never leak the API key. Keep the response status for diagnostics.
        raise RuntimeError(f'Gemini HTTP {resp.status_code}')
    data = resp.json()

    candidates = data.get('candidates') or []
    if not candidates:
        raise RuntimeError('Gemini returned no candidates')
    parts = ((candidates[0].get('content') or {}).get('parts') or [])
    raw_text = ''.join(p.get('text', '') for p in parts if isinstance(p, dict)).strip()
    if not raw_text:
        raise RuntimeError('Gemini returned an empty response')

    match = re.search(r'\{[\s\S]*\}', raw_text)
    result = json.loads(match.group(0) if match else raw_text)
    _validate_ai_response(result)
    result['source'] = 'gemini'
    result['raw_response'] = {'model': model, 'finish_reason': candidates[0].get('finishReason')}
    return result


# ------------------------------
# Helpers
# ------------------------------
def _build_patient_context(data: dict) -> str:
    vitals = data.get('vitals', {}) or {}

    lines = [
        "PATIENT TRIAGE REQUEST",
        "=" * 40,
        f"Age: {data.get('age', 'Unknown')} years",
        f"Gender: {data.get('gender', 'Unknown')}",
        f"Chief Complaint: {data.get('chiefComplaint', 'Not specified')}",
        "",
        "SYMPTOMS:",
    ]

    symptoms = data.get('symptoms', [])
    if symptoms:
        for sym in symptoms:
            lines.append(f"  • {sym}")
    else:
        lines.append("  • None reported")

    lines.append("")
    lines.append("VITAL SIGNS:")

    vital_map = [
        ('temperature',      'Temperature',      '°C'),
        ('bpSystolic',       'BP Systolic',      'mmHg'),
        ('bpDiastolic',      'BP Diastolic',     'mmHg'),
        ('spo2',             'SpO₂',             '%'),
        ('pulseRate',        'Pulse Rate',        'bpm'),
        ('respiratoryRate',  'Respiratory Rate', '/min'),
        ('weight',           'Weight',           'kg'),
    ]

    any_vital = False
    for key, label, unit in vital_map:
        val = vitals.get(key)
        if val is not None and str(val).strip():
            lines.append(f"  {label}: {val} {unit}")
            any_vital = True
    if not any_vital:
        lines.append("  No vitals recorded")

    lines += [
        "",
        f"Known Conditions : {data.get('knownConditions', 'None') or 'None'}",
        f"Current Medications: {data.get('currentMedications', 'None') or 'None'}",
        f"Allergies        : {data.get('allergies', 'NKDA') or 'NKDA'}",
        f"Duration of symptoms: {data.get('symptomDuration', 'Unknown') or 'Unknown'}",
    ]

    additional = data.get('additionalNotes', '').strip()
    if additional:
        lines.append(f"Additional notes : {additional}")

    lines.append("")
    lines.append("Please provide your triage assessment as a JSON object.")

    return '\n'.join(lines)


def _validate_ai_response(result: dict) -> None:
    required = ['condition', 'urgency', 'recommendations', 'reasoning']
    missing = [k for k in required if k not in result]
    if missing:
        raise ValueError(f"AI response missing required fields: {missing}")

    valid_urgencies = {'critical', 'high', 'moderate', 'low'}
    if result.get('urgency', '').lower() not in valid_urgencies:
        result['urgency'] = 'moderate'

    if not isinstance(result.get('recommendations'), list):
        result['recommendations'] = [str(result.get('recommendations', 'Consult a doctor.'))]
    if not isinstance(result.get('medicine_suggestions'), list):
        result['medicine_suggestions'] = []
    if not isinstance(result.get('red_flags_present'), list):
        result['red_flags_present'] = []
    if not isinstance(result.get('key_points'), list):
        result['key_points'] = []


# ------------------------------
# Rule-based fallback (deterministic)
# ------------------------------
def _run_rule_based_assessment(data: dict) -> dict:
    symptoms = [s.lower() for s in (data.get('symptoms') or [])]
    vitals = data.get('vitals') or {}
    complaint = (data.get('chiefComplaint') or '').lower()
    age = int(data.get('age') or 0)

    def _v(key):
        try:
            return float(vitals.get(key))
        except (TypeError, ValueError):
            return None

    temp = _v('temperature')
    spo2 = _v('spo2')
    pulse = _v('pulseRate')
    bp_sys = _v('bpSystolic')
    rr = _v('respiratoryRate')

    urgency = 'low'
    condition = 'General illness / Further assessment required'
    confidence = 'Low (<50%)'
    recommendations = ['Record detailed history and physical examination.',
                       'Refer to doctor for confirmed diagnosis.']
    reasoning = 'Insufficient data for a specific diagnosis. Rule-based fallback engine used.'
    red_flags = []
    refer_immediately = False

    if spo2 is not None and spo2 < 90:
        urgency = 'critical'; refer_immediately = True
        condition = 'Respiratory failure / Severe hypoxia'
        red_flags.append(f'SpO₂ critically low: {spo2}%')
        recommendations = ['Administer supplemental oxygen immediately if available.',
                           'EMERGENCY transport to hospital — do not delay.',
                           'Monitor breathing continuously.']
        reasoning = f'SpO₂ of {spo2}% indicates critical oxygen desaturation. Immediate intervention required.'
        confidence = 'High (>80%)'

    elif temp is not None and temp >= 40:
        urgency = 'critical'; refer_immediately = True
        condition = 'Hyperpyrexia (Extreme Fever)'
        red_flags.append(f'Temperature critically high: {temp}°C')
        recommendations = ['Cool the patient immediately with damp cloths.',
                           'Paracetamol 500mg–1g orally if conscious.',
                           'IV fluids if available. EMERGENCY transport to hospital.']
        reasoning = f'Temperature of {temp}°C constitutes hyperpyrexia with risk of febrile seizures and organ damage.'
        confidence = 'High (>80%)'

    elif bp_sys is not None and bp_sys > 180:
        urgency = 'critical'; refer_immediately = True
        condition = 'Hypertensive Crisis'
        red_flags.append(f'Blood pressure critically high: {bp_sys} mmHg systolic')
        recommendations = ['Keep patient calm and at rest — no sudden movements.',
                           'EMERGENCY transport to hospital for IV antihypertensives.',
                           'Do NOT give oral antihypertensives without doctor instruction.']
        reasoning = f'Systolic BP of {bp_sys} mmHg indicates hypertensive crisis with risk of stroke and organ damage.'
        confidence = 'High (>80%)'

    elif bp_sys is not None and bp_sys < 90:
        urgency = 'critical'; refer_immediately = True
        condition = 'Hypotension / Shock'
        red_flags.append(f'Blood pressure critically low: {bp_sys} mmHg systolic')
        recommendations = ['Lay patient flat. Raise legs if no respiratory distress.',
                           'IV fluids (Normal Saline) if available.',
                           'EMERGENCY transport to hospital.']
        reasoning = f'Systolic BP of {bp_sys} mmHg suggests hypotension — assess for septic, hypovolaemic, or cardiogenic shock.'
        confidence = 'High (>80%)'

    elif urgency == 'low':
        if any(k in complaint for k in ['snake', 'bite', 'sting']) or 'snake' in symptoms:
            urgency = 'critical'; refer_immediately = True
            condition = 'Snake Bite (suspected envenomation)'
            recommendations = ['Immobilise bitten limb BELOW heart level.',
                               'DO NOT cut wound, suck venom, or apply tourniquet.',
                               'EMERGENCY transport to hospital for anti-venom.',
                               'Mark swelling edge with pen and note time.']
            reasoning = 'Snake bite requires immediate hospital admission for anti-venom — time-critical.'
            confidence = 'High (>80%)'

        elif 'choking' in symptoms or ('difficulty breathing' in symptoms and 'cough' in symptoms):
            urgency = 'critical'; refer_immediately = True
            condition = 'Possible Airway Obstruction'
            recommendations = ['Perform back blows and abdominal thrusts if complete obstruction.',
                               'If cleared, assess for partial obstruction.',
                               'EMERGENCY transport if obstruction persists.']
            reasoning = 'Difficulty breathing with cough may indicate partial or complete airway obstruction.'
            confidence = 'Medium (50-80%)'

        elif 'fever' in symptoms or (temp is not None and temp >= 38.5):
            temp_str = f'{temp}°C' if temp else 'reported'

            if any(k in complaint for k in ['chills', 'shivering', 'malaria']):
                urgency = 'high'; condition = 'Suspected Malaria'
                recommendations = ['Perform Rapid Diagnostic Test (RDT) for malaria.',
                                   'Give Paracetamol for fever management.',
                                   'Ensure adequate hydration (ORS/water).',
                                   'Refer to doctor for confirmed anti-malarial treatment.',
                                   'Do NOT start anti-malarials without confirmed diagnosis.']
                reasoning = f'Fever ({temp_str}) with chills/rigors is classic for malaria. RDT confirmation required before treatment.'
                confidence = 'Medium (50-80%)'

            else:
                urgency = 'moderate'; condition = 'Fever — cause undetermined'
                recommendations = ['Paracetamol 500mg–1g every 4–6 hours for fever.',
                                   'Ensure adequate fluid intake (ORS/water).',
                                   'Monitor temperature every 30 minutes.',
                                   'Refer to doctor if fever persists > 3 days or any red flags develop.']
                reasoning = f'Elevated temperature ({temp_str}). Cause unclear from available data. Symptomatic management and monitoring.'
                confidence = 'Low (<50%)'

        elif 'diarrhoea' in symptoms or 'vomiting' in symptoms:
            urgency = 'moderate'; condition = 'Gastroenteritis / Dehydration risk'
            recommendations = ['Initiate ORS immediately — 200-400ml after each loose stool.',
                               'ORS preparation: 1L safe water + 6 tsp sugar + 0.5 tsp salt.',
                               'Monitor for signs of severe dehydration (sunken eyes, no urine).',
                               'Zinc 20mg daily for 10–14 days (children under 5 only).',
                               'Refer if bloody diarrhoea or no improvement in 24 hours.']
            reasoning = 'Diarrhoea and/or vomiting create dehydration risk. ORS is first-line. Monitor closely.'
            confidence = 'Medium (50-80%)'

        elif any(k in complaint for k in ['wound', 'cut', 'injury', 'burn', 'bleeding']):
            urgency = 'moderate'; condition = 'Wound / Trauma'
            recommendations = ['Clean wound with clean water and antiseptic.',
                               'Apply pressure dressing to control bleeding.',
                               "Check tetanus vaccination status.",
                               "Refer to doctor if deep wound, won't stop bleeding, or shows infection."]
            reasoning = 'Wound or trauma reported. Assess depth, bleeding, and infection risk. Refer for sutures if needed.'
            confidence = 'Medium (50-80%)'

    if urgency == 'low' and condition == 'General illness / Further assessment required':
        recommendations = ['Complete a thorough physical examination.',
                           'Record detailed patient history.',
                           'Refer to attending doctor for assessment.']
        reasoning = 'Insufficient symptom data for pattern matching. Rule-based fallback used. Doctor review required.'

    return {
        'condition': condition,
        'urgency': urgency,
        'confidence': confidence,
        'recommendations': recommendations,
        'medicine_suggestions': [],
        'reasoning': reasoning,
        'red_flags_present': red_flags,
        'refer_immediately': refer_immediately,
        'source': 'rule_based',
        'raw_response': None,
    }
