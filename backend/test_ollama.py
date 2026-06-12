import json
import requests

def test_ollama():
    url = "http://host.docker.internal:11434/api/generate"
    payload = {
        "model": "qwen2.5:32b",
        "prompt": "Translate 'שלום' to English and Russian. Respond in JSON format like {\"en\": \"...\", \"ru\": \"...\"}.",
        "stream": False,
        "format": "json"
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        print("Status Code:", response.status_code)
        print("Response:", response.json().get("response"))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_ollama()
