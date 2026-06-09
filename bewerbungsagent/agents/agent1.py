import json
import os
import requests
import sys
from datetime import date

# Projektwurzel zum Suchpfad hinzufügen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.pdf_parser import extrahiere_text

# ─────────────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────────────

# Allgemeiner Text-Prompt (kein {text}-Platzhalter – wird in den Aufruf eingebettet)
TEXT_SKILL_PROMPT = """Extrahiere Skills aus dem folgenden Text. Antworte NUR mit JSON, kein anderer Text:
{
  "hard_skills": [],
  "soft_skills": [],
  "tools": [],
  "erfahrungslevel": {}
}
Erfahrungslevel: 1=Grundkenntnisse, 2=Fortgeschritten, 3=Experte"""

# Allgemeiner Bild-Prompt für Lebensläufe, Zeugnisse etc.
BILD_PROMPT = """Analysiere dieses Bild und extrahiere alle sichtbaren Skills, Tools und Technologien.
Antworte NUR mit JSON, kein anderer Text:
{
  "hard_skills": [],
  "soft_skills": [],
  "tools": [],
  "erfahrungslevel": {}
}
Erfahrungslevel: 1=Grundkenntnisse, 2=Fortgeschritten, 3=Experte"""

# Auf LinkedIn-Profile zugeschnittener Prompt
LINKEDIN_PROMPT = """Analysiere dieses LinkedIn-Profil-Screenshot.
Erkenne Jobtitel, Berufserfahrung in Jahren, Zertifikate, Empfehlungen sowie alle
genannten Technologien und Fähigkeiten.
Antworte NUR mit JSON, kein anderer Text:
{
  "hard_skills": [],
  "soft_skills": [],
  "tools": [],
  "erfahrungslevel": {}
}
Hinweise:
- Jobtitel → hard_skills mit passendem Erfahrungslevel (Jahre / 3 ≈ Level)
- Zertifikate → hard_skills mit Level 3
- Empfehlungen → soft_skills
- Erfahrungslevel: 1=Grundkenntnisse, 2=Fortgeschritten, 3=Experte"""

# Prompt für Zertifikate – erwartet ein abweichendes JSON-Format
ZERTIFIKAT_PROMPT = """Analysiere dieses Zertifikat.
Extrahiere den genauen Zertifikatsname, den Aussteller und das Ausstellungsjahr.
Antworte NUR mit JSON, kein anderer Text:
{
  "zertifikatsname": "",
  "aussteller": "",
  "jahr": "",
  "zusaetzliche_skills": []
}"""

# Unterstützte Bildformate und ihre MIME-Typen
BILD_ENDUNGEN = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}

# Leeres Ergebnis-Template für Fehlerfall
_LEERES_ERGEBNIS = {"hard_skills": [], "soft_skills": [], "tools": [], "erfahrungslevel": {}}


# ─────────────────────────────────────────────────────────────────────────────
# Interne Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_json(antwort):
    """Schneidet den JSON-Block aus einer LLM-Antwort heraus und parst ihn."""
    try:
        start = antwort.find("{")
        ende = antwort.rfind("}") + 1
        if start == -1 or ende == 0:
            print("Kein JSON in der Antwort gefunden.")
            return None
        return json.loads(antwort[start:ende])
    except json.JSONDecodeError:
        print("Kein gültiges JSON in der Antwort.")
        return None


def _ruf_ollama(prompt_text):
    """Schickt einen Prompt an Ollama (llama3.2) und gibt die Antwort zurück."""
    try:
        antwort = requests.post("http://localhost:11434/api/generate", json={
            "model": "llama3.2",
            "prompt": prompt_text,
            "stream": False
        })
        return antwort.json().get("response", "")
    except Exception as e:
        print(f"Ollama API Fehler: {e}")
        return ""


def _ruf_ollama_vision(dateipfad, prompt):
    """Vision nicht verfügbar mit Ollama"""
    print("Vision nicht verfügbar mit Ollama")
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Skill-Extraktion
# ─────────────────────────────────────────────────────────────────────────────

def extrahiere_skills_aus_text(text):
    """Schickt Freitext an Ollama und gibt extrahierte Skills als Dict zurück."""
    antwort = _ruf_ollama(f"{TEXT_SKILL_PROMPT}\n\nText:\n{text[:3000]}")
    if not antwort:
        return dict(_LEERES_ERGEBNIS)
    return _parse_json(antwort) or dict(_LEERES_ERGEBNIS)


def extrahiere_skills_aus_pdf(dateipfad):
    """Liest PDF-Text und extrahiert daraus Skills via Claude."""
    text = extrahiere_text(dateipfad)
    if not text:
        return dict(_LEERES_ERGEBNIS)
    return extrahiere_skills_aus_text(text)


def extrahiere_skills_aus_bild(dateipfad):
    """Bildverarbeitung nicht verfügbar mit Ollama."""
    antwort = _ruf_ollama_vision(dateipfad, BILD_PROMPT)
    if not antwort:
        return dict(_LEERES_ERGEBNIS)
    return _parse_json(antwort) or dict(_LEERES_ERGEBNIS)


def extrahiere_skills_aus_linkedin(dateipfad):
    """LinkedIn-Screenshot-Verarbeitung nicht verfügbar mit Ollama."""
    antwort = _ruf_ollama_vision(dateipfad, LINKEDIN_PROMPT)
    if not antwort:
        return dict(_LEERES_ERGEBNIS)
    return _parse_json(antwort) or dict(_LEERES_ERGEBNIS)


def extrahiere_skills_aus_zertifikat(dateipfad):
    """Zertifikat (Bild oder PDF) analysieren.

    Gibt ein Tupel (skills_dict, beleg) zurück:
    - skills_dict: Zertifikatsname als Hard Skill mit level=3
    - beleg: String "Aussteller, Jahr" für die beleg-Spalte in SQLite
    """
    endung = os.path.splitext(dateipfad)[1].lower()

    if endung == ".pdf":
        text = extrahiere_text(dateipfad)
        if not text:
            return dict(_LEERES_ERGEBNIS), None
        antwort = _ruf_ollama(f"{ZERTIFIKAT_PROMPT}\n\nText:\n{text[:3000]}")
    else:
        antwort = _ruf_ollama_vision(dateipfad, ZERTIFIKAT_PROMPT)

    if not antwort:
        return dict(_LEERES_ERGEBNIS), None

    zert = _parse_json(antwort)
    if not zert:
        return dict(_LEERES_ERGEBNIS), None

    zertname = zert.get("zertifikatsname", "").strip()
    aussteller = zert.get("aussteller", "").strip()
    jahr = str(zert.get("jahr", "")).strip()

    if not zertname:
        return dict(_LEERES_ERGEBNIS), None

    # Zertifikatsname → Hard Skill, Level 3 (nachweisliche Qualifikation)
    hard_skills = [zertname] + zert.get("zusaetzliche_skills", [])
    erfahrungslevel = {s: 3 for s in hard_skills}

    skills_dict = {
        "hard_skills": hard_skills,
        "soft_skills": [],
        "tools": [],
        "erfahrungslevel": erfahrungslevel,
    }

    beleg = f"{aussteller}, {jahr}".strip(", ") if (aussteller or jahr) else None
    return skills_dict, beleg


# ─────────────────────────────────────────────────────────────────────────────
# Datenbank-Funktionen
# ─────────────────────────────────────────────────────────────────────────────

def speichere_skills(skills_dict, nutzer_id, quelle, conn, beleg=None):
    """Speichert Skills in SQLite. Bei Duplikaten gewinnt der höhere Level."""
    cursor = conn.cursor()
    heute = date.today().isoformat()

    kategorien = [
        ("Hard Skill", skills_dict.get("hard_skills", [])),
        ("Soft Skill", skills_dict.get("soft_skills", [])),
        ("Tool",       skills_dict.get("tools", [])),
    ]

    for kategorie, skill_liste in kategorien:
        for skill_name in skill_liste:
            if not skill_name:
                continue

            level = skills_dict.get("erfahrungslevel", {}).get(skill_name, 1)

            cursor.execute(
                "SELECT id, level FROM skills WHERE nutzer_id = ? AND name = ?",
                (nutzer_id, skill_name)
            )
            vorhanden = cursor.fetchone()

            if vorhanden:
                # Höherer Level gewinnt; beleg immer aktualisieren wenn übergeben
                if level > vorhanden[1]:
                    cursor.execute(
                        "UPDATE skills SET level = ?, zuletzt_aktualisiert = ? WHERE id = ?",
                        (level, heute, vorhanden[0])
                    )
                if beleg is not None:
                    cursor.execute(
                        "UPDATE skills SET beleg = ? WHERE id = ?",
                        (beleg, vorhanden[0])
                    )
            else:
                cursor.execute(
                    """INSERT INTO skills
                           (nutzer_id, name, kategorie, level, quelle, zuletzt_aktualisiert, beleg)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (nutzer_id, skill_name, kategorie, level, quelle, heute, beleg)
                )

    conn.commit()


def lade_profil(nutzer_id, conn):
    """Liest alle Skills des Nutzers aus SQLite und gibt sie als Liste von Dicts zurück."""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT name, kategorie, level, quelle, zuletzt_aktualisiert
           FROM skills WHERE nutzer_id = ? ORDER BY name""",
        (nutzer_id,)
    )
    zeilen = cursor.fetchall()
    return [
        {"name": z[0], "kategorie": z[1], "level": z[2], "quelle": z[3], "zuletzt_aktualisiert": z[4]}
        for z in zeilen
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Ordner-Scanner mit dateinamen-basierter Erkennung
# ─────────────────────────────────────────────────────────────────────────────

def verarbeite_ordner(ordner_pfad, nutzer_id, conn):
    """Scannt einen Ordner und extrahiert Skills aus PDFs und Bildern.

    Dateinamen-Routing:
    - 'linkedin' im Namen              → LinkedIn-optimierter Prompt
    - 'zertifikat' oder 'certificate'  → Zertifikat-Extraktion mit beleg
    - alles andere                     → allgemeiner Prompt
    """
    verarbeitet = 0

    for dateiname in os.listdir(ordner_pfad):
        dateipfad = os.path.join(ordner_pfad, dateiname)
        endung = os.path.splitext(dateiname)[1].lower()
        name_klein = dateiname.lower()

        if endung == ".pdf":
            if "zertifikat" in name_klein or "certificate" in name_klein:
                print(f"Verarbeite Zertifikat-PDF: {dateiname}")
                skills, beleg = extrahiere_skills_aus_zertifikat(dateipfad)
                speichere_skills(skills, nutzer_id, dateiname, conn, beleg=beleg)
            else:
                print(f"Verarbeite PDF: {dateiname}")
                skills = extrahiere_skills_aus_pdf(dateipfad)
                speichere_skills(skills, nutzer_id, dateiname, conn)
            verarbeitet += 1

        elif endung in BILD_ENDUNGEN:
            if "linkedin" in name_klein:
                print(f"Verarbeite LinkedIn-Screenshot: {dateiname}")
                skills = extrahiere_skills_aus_linkedin(dateipfad)
                speichere_skills(skills, nutzer_id, dateiname, conn)
            elif "zertifikat" in name_klein or "certificate" in name_klein:
                print(f"Verarbeite Zertifikat-Bild: {dateiname}")
                skills, beleg = extrahiere_skills_aus_zertifikat(dateipfad)
                speichere_skills(skills, nutzer_id, dateiname, conn, beleg=beleg)
            else:
                print(f"Verarbeite Bild: {dateiname}")
                skills = extrahiere_skills_aus_bild(dateipfad)
                speichere_skills(skills, nutzer_id, dateiname, conn)
            verarbeitet += 1

    print(f"{verarbeitet} Datei(en) verarbeitet.")
    return verarbeitet


if __name__ == "__main__":
    import sqlite3

    conn = sqlite3.connect("profile.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nutzer_id INTEGER,
        name TEXT,
        kategorie TEXT,
        level INTEGER,
        quelle TEXT,
        zuletzt_aktualisiert TEXT,
        beleg TEXT
    )""")
    conn.commit()

    verarbeite_ordner("./input", nutzer_id=1, conn=conn)

    print("\n=== Skill Profil ===")
    for skill in lade_profil(nutzer_id=1, conn=conn):
        print(f"  {skill['kategorie']:10} | Level {skill['level']} | {skill['name']}")

    conn.close()
