import os, requests, json
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
from services.ai_service import _build_patient_context

sample = {
    'age': 30,
    'gender': 'female',
    'chiefComplaint': 'Fever and cough for 2 days',
    'symptoms': ['fever', 'cough', 'body aches'],
    'vitals': {'temperature': 38.8, 'bpSystolic': 120, 'bpDiastolic': 80, 'spo2': 96},
    'knownConditions': 'None',
    'additionalNotes': ''
}
user_message = _build_patient_context(sample)
rest_system = ('Provide ONLY a single valid JSON object with keys: '
               'condition, urgency, confidence, recommendations, reasoning, '
               'red_flags_present, refer_immediately. Use double quotes, no extra text.')
model = os.getenv('GEMINI_MODEL')
key = os.getenv('GEMINI_API_KEY')
url = f'https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={key}'

payload = {
    "contents": [
        {"parts": [{"text": rest_system + "\n\n" + user_message}], "role": "user"}
    ],
    "generationConfig": {"temperature": float(os.getenv('GEMINI_TEMPERATURE', '0.2')), "maxOutputTokens": int(os.getenv('GEMINI_MAX_TOKENS', '600'))}
}
print('Posting to', url)
resp = requests.post(url, json=payload, timeout=30)
print('Status', resp.status_code)
print(resp.text[:2000])
