import os
import requests
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
key = os.getenv('GEMINI_API_KEY')
model = os.getenv('GEMINI_MODEL', 'models/gemini-3.1-flash-lite')
for ver in ['v1','v1beta2']:
    for method in ['generateText','generateContent']:
        url = f'https://generativelanguage.googleapis.com/{ver}/models/{model}:{method}?key={key}'
        print('\nTRY', url)
        # try two payload shapes to cover different API shapes
        payloads = [
            {'prompt': {'text': 'Hello'}, 'maxOutputTokens': 50},
            {'content': [{'type': 'text', 'text': 'Hello'}], 'maxOutputTokens': 50},
            {'contents': [{'parts': [{'text': 'Hello'}], 'role': 'user'}], 'generationConfig': {'maxOutputTokens': 50, 'temperature': 0.2}}
        ]
        for p in payloads:
            try:
                r = requests.post(url, json=p, timeout=15)
                print(method, '->', r.status_code)
                print(r.text[:800])
            except Exception as e:
                print('ERR', e)
