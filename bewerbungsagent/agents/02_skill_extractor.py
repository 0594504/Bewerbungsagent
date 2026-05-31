import json
import os
from datetime import date

# Andere Module einbinden
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.ollama_client import ask_ollama
from utils.pdf_parser import extract_text_from_pdf

# Pfad zum Benutzerprofil
PROFIL_PFAD = os.path.join(os.path.dirname(__file__), "..", "data", "profil.json")

# Prompt für die Skill-Extraktion
SKILL_PROMPT = """Extrahiere Skills aus dem folgenden Text. Antworte NUR mit JSON, kein anderer Text:
{{
  "hard_skills": [],
  "soft_skills": [],
  "tools": [],
  "erfahrungslevel": {{}}
}}

Text:
{text}"""


def _lade_profil():
    """Lädt das Profil aus profil.json oder erstellt ein leeres Profil."""

    if os.path.exists(PROFIL_PFAD):
        with open(PROFIL_PFAD, "r", encoding="utf-8") as f:
            return json.load(f)

    # Leeres Standard-Profil
    return {
        "version": 1,
        "nutzer_id": "user_001",
        "skills": [],
        "erfahrungen": [],
        "letztes_update": date.today().isoformat()
    }


def _speichere_profil(profil):
    """Speichert das Profil in profil.json."""

    os.makedirs(os.path.dirname(PROFIL_PFAD), exist_ok=True)
    with open(PROFIL_PFAD, "w", encoding="utf-8") as f:
        json.dump(profil, f, ensure_ascii=False, indent=2)


def update_profil(neue_skills):
    """Fügt neue Skills ins Profil ein. Bei Duplikaten wird der höhere Level behalten."""

    profil = _lade_profil()
    heute = date.today().isoformat()

    # Bestehende Skills als Lookup-Dictionary aufbauen (Name → Index)
    skill_index = {s["name"].lower(): i for i, s in enumerate(profil["skills"])}

    for kategorie, skill_liste in [("Hard Skill", neue_skills.get("hard_skills", [])),
                                    ("Soft Skill", neue_skills.get("soft_skills", [])),
                                    ("Tool", neue_skills.get("tools", []))]:
        for skill_name in skill_liste:
            if not skill_name:
                continue

            level = neue_skills.get("erfahrungslevel", {}).get(skill_name, 1)

            if skill_name.lower() in skill_index:
                # Skill existiert bereits → höheren Level behalten
                idx = skill_index[skill_name.lower()]
                if level > profil["skills"][idx]["level"]:
                    profil["skills"][idx]["level"] = level
                    profil["skills"][idx]["zuletzt_aktualisiert"] = heute
            else:
                # Neuen Skill hinzufügen
                neuer_skill = {
                    "name": skill_name,
                    "kategorie": kategorie,
                    "level": level,
                    "quelle": "skill_extractor",
                    "zuletzt_aktualisiert": heute
                }
                profil["skills"].append(neuer_skill)
                skill_index[skill_name.lower()] = len(profil["skills"]) - 1

    profil["letztes_update"] = heute
    _speichere_profil(profil)
    print(f"Profil aktualisiert: {len(profil['skills'])} Skills gesamt")


def _extrahiere_skills_mit_llm(text):
    """Schickt den Text an Ollama und gibt die extrahierten Skills als Dict zurück."""

    prompt = SKILL_PROMPT.format(text=text[:3000])  # Text kürzen falls zu lang
    antwort = ask_ollama(prompt)

    if antwort is None:
        return None

    # JSON aus der Antwort parsen
    try:
        # Manchmal gibt das LLM Text vor/nach dem JSON zurück → JSON-Block suchen
        start = antwort.find("{")
        ende = antwort.rfind("}") + 1
        if start == -1 or ende == 0:
            print("Kein JSON in der LLM-Antwort gefunden.")
            print(f"Rohe Antwort: {antwort}")
            return None

        return json.loads(antwort[start:ende])

    except json.JSONDecodeError:
        print("LLM hat kein gültiges JSON zurückgegeben.")
        print(f"Rohe Antwort: {antwort}")
        return None


def extract_from_text(text):
    """Extrahiert Skills aus einem Text und speichert sie ins Profil."""

    print("Extrahiere Skills aus Text...")
    skills = _extrahiere_skills_mit_llm(text)

    if skills:
        update_profil(skills)
    return skills


def extract_from_pdf(filepath):
    """Extrahiert Skills aus einer PDF-Datei und speichert sie ins Profil."""

    print(f"Lese PDF: {filepath}")
    text = extract_text_from_pdf(filepath)

    if text is None:
        return None

    print("Extrahiere Skills aus PDF-Text...")
    skills = _extrahiere_skills_mit_llm(text)

    if skills:
        update_profil(skills)
    return skills


# Direkt ausführen zum Testen
if __name__ == "__main__":
    beispieltext = "Ich habe 3 Jahre Python-Erfahrung und kenne Django und FastAPI gut. Außerdem arbeite ich teamorientiert."
    extract_from_text(beispieltext)