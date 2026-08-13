from services.ai_service import _run_gemini_via_rest
from config import config

sample = {
    'age': 30,
    'gender': 'female',
    'chiefComplaint': 'Fever and cough for 2 days',
    'symptoms': ['fever', 'cough', 'body aches'],
    'vitals': {'temperature': 38.8, 'bpSystolic': 120, 'bpDiastolic': 80, 'spo2': 96},
    'knownConditions': 'None',
    'additionalNotes': ''
}

try:
    res = _run_gemini_via_rest(sample, config)
    print('PARSED RESULT:')
    print(res)
except Exception as e:
    print('ERROR:', e)
    import traceback; traceback.print_exc()
