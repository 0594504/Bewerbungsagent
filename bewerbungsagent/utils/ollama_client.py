import requests
import json

# Ollama läuft standardmäßig auf diesem Port
OLLAMA_URL = "http://localhost:11434/api/generate"


def ask_ollama(prompt, model="llama3.1:8b"):
    """Sendet einen Prompt an Ollama und gibt die Antwort als Text zurück."""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    except requests.exceptions.ConnectionError:
        print("Ollama läuft nicht. Bitte starte Ollama zuerst.")
        return None

    except requests.exceptions.Timeout:
        print("Ollama hat nicht rechtzeitig geantwortet (Timeout nach 60 Sekunden).")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Fehler bei der Anfrage an Ollama: {e}")
        return None