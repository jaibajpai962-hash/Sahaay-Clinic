from services.ai_service import run_triage_assessment

sample = {
    'age': 30,
    'gender': 'female',
    'chiefComplaint': 'Fever and cough for 2 days',
    'symptoms': ['fever', 'cough', 'body aches'],
    'vitals': {'temperature': 38.8, 'bpSystolic': 120, 'bpDiastolic': 80, 'spo2': 96},
    'knownConditions': 'None',
    'additionalNotes': ''
}

res = run_triage_assessment(sample)
print(res)
