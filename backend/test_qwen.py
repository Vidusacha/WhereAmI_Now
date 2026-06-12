import requests
import json
OLLAMA_URL = 'http://host.docker.internal:11434/api/generate'
payload = {
    'model': 'qwen3.6:latest',
    'prompt': 'Translate these two Israeli political party names into English and Russian. Return strictly JSON: {"שלום": {"en": "...", "ru": "..."}, "מפלגת הליכוד": {"en": "...", "ru": "..."}}.',
    'stream': False
}
res = requests.post(OLLAMA_URL, json=payload, timeout=60)
print('Response Status:', res.status_code)
print('Response Body:', res.text)
