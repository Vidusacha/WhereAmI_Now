import requests
import sys

OLLAMA_URL = 'http://host.docker.internal:11434/api/chat'
payload = {
    'model': 'qwen3.6:latest',
    'messages': [{'role': 'user', 'content': 'Hello, are you there? Reply with YES.'}],
    'stream': True
}
try:
    print("Sending request to Ollama...", flush=True)
    res = requests.post(OLLAMA_URL, json=payload, timeout=60, stream=True)
    for line in res.iter_lines():
        if line:
            print(line.decode('utf-8'))
except Exception as e:
    print("Error:", e)
