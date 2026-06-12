import requests
import json
OLLAMA_URL = 'http://host.docker.internal:11434/api/chat'
payload = {
    'model': 'qwen3.6:latest',
    'messages': [{'role': 'user', 'content': 'Translate these two names: ["שלום", "מפלגת הליכוד"]. Return strictly JSON: {"שלום": {"en": "...", "ru": "..."}, "מפלגת הליכוד": {"en": "...", "ru": "..."}}.'}],
    'stream': False
}
res = requests.post(OLLAMA_URL, json=payload, timeout=60)
print('Response Status:', res.status_code)
print('Response Body:', res.text)
