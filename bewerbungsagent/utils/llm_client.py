import os
import requests

# Ollama läuft lokal auf diesem Port
OLLAMA_URL = "http://localhost:11434/api/generate"


def frage_ki(prompt, qualitaet="normal"):
    """Schickt einen Prompt an die KI und gibt die Antwort als String zurück.

    qualitaet='normal' → Ollama lokal (llama3.1:8b)
    qualitaet='hoch'   → Claude API (nur für Anschreiben)
    """
    if qualitaet == "hoch":
        return _frage_claude(prompt)
    return _frage_ollama(prompt)


def _frage_ollama(prompt):
    """Sendet Prompt an lokales Ollama-Modell."""
    payload = {
        "model": "llama3.1:8b",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "")

    except requests.exceptions.ConnectionError:
        print("Ollama läuft nicht. Bitte starte Ollama mit: ollama serve")
        return ""

    except requests.exceptions.Timeout:
        print("Ollama hat nicht geantwortet (Timeout nach 60s).")
        return ""

    except requests.exceptions.RequestException as e:
        print(f"Ollama Fehler: {e}")
        return ""


def _frage_claude(prompt):
    """Sendet Prompt an Claude API (Anthropic)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ANTHROPIC_API_KEY ist nicht gesetzt. Bitte in .env eintragen.")
        return ""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        nachricht = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return nachricht.content[0].text

    except Exception as e:
        print(f"Claude API Fehler: {e}")
        return ""
