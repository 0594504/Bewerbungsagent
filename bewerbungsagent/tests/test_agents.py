import json
import os
import sys
import sqlite3
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Projektwurzel zum Suchpfad hinzufügen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database
from agents import skill_extractor, application_agent
from utils import pdf_parser


# Hilfsfunktion: In-Memory-Datenbank für Tests (kein echter Dateizugriff)
def _test_db():
    conn = sqlite3.connect(":memory:")
    database.erstelle_tabellen(conn)
    return conn


# =====================================================================
# Test 1: Skill-Extraktion aus Text
# =====================================================================

def test_skill_extraktion_aus_text():
    """Prüft ob JSON korrekt geparst wird wenn das LLM eine gültige Antwort liefert."""
    antwort_mock = json.dumps({
        "hard_skills": ["Python", "Django"],
        "soft_skills": ["Teamwork"],
        "tools": ["Git"],
        "erfahrungslevel": {"Python": 3, "Django": 2}
    })

    with patch("agents.skill_extractor.frage_ki", return_value=antwort_mock):
        ergebnis = skill_extractor.extrahiere_skills_aus_text("Ich programmiere Python und nutze Git.")

    assert "Python" in ergebnis["hard_skills"]
    assert "Teamwork" in ergebnis["soft_skills"]
    assert "Git" in ergebnis["tools"]
    assert ergebnis["erfahrungslevel"]["Python"] == 3


# =====================================================================
# Test 2: Duplikat-Skill – höherer Level gewinnt
# =====================================================================

def test_duplikat_skill_level():
    """Prüft ob beim Speichern eines doppelten Skills der höhere Level behalten wird."""
    conn = _test_db()

    # Skill zuerst mit Level 2 speichern
    skills_v1 = {
        "hard_skills": ["Python"],
        "soft_skills": [],
        "tools": [],
        "erfahrungslevel": {"Python": 2}
    }
    skill_extractor.speichere_skills(skills_v1, "test_user", "test", conn)

    # Gleichen Skill mit Level 4 speichern
    skills_v2 = {
        "hard_skills": ["Python"],
        "soft_skills": [],
        "tools": [],
        "erfahrungslevel": {"Python": 4}
    }
    skill_extractor.speichere_skills(skills_v2, "test_user", "test", conn)

    profil = skill_extractor.lade_profil("test_user", conn)
    python_skill = next(s for s in profil if s["name"] == "Python")

    assert python_skill["level"] == 4, "Level 4 sollte den Level 2 ersetzen"
    conn.close()


# =====================================================================
# Test 3: Match-Score Berechnung
# =====================================================================

def test_match_score_berechnung():
    """Prüft das Keyword-Matching mit Beispiel-Skills und Beschreibung."""
    profil_skills = [
        {"name": "Python", "kategorie": "Hard Skill", "level": 3},
        {"name": "SQL", "kategorie": "Hard Skill", "level": 2},
        {"name": "Docker", "kategorie": "Tool", "level": 1}
    ]

    # Stelle erwähnt 2 von 3 Skills → Score ca. 66%
    beschreibung = "Wir suchen einen Entwickler mit Python und SQL-Kenntnissen."
    score = application_agent.berechne_match_score(beschreibung, profil_skills)

    assert 0 < score <= 100, "Score muss zwischen 0 und 100 liegen"
    assert score >= 60, "2 von 3 Skills sollten einen Score von mindestens 60 ergeben"


# =====================================================================
# Test 4: PDF-Parser – kein Text (Bild-PDF)
# =====================================================================

def test_pdf_parser_kein_text():
    """Prüft ob leerer String zurückkommt wenn das PDF keinen lesbaren Text hat."""
    mock_doc = MagicMock()
    mock_seite = MagicMock()
    mock_seite.get_text.return_value = ""
    mock_doc.__iter__ = MagicMock(return_value=iter([mock_seite]))
    mock_doc.close = MagicMock()

    with patch("utils.pdf_parser.fitz.open", return_value=mock_doc):
        ergebnis = pdf_parser.extrahiere_text("dummy.pdf")

    assert ergebnis == "", "Bild-PDF soll leeren String zurückgeben"


# =====================================================================
# Test 5: Datenbank – alle 5 Tabellen werden angelegt
# =====================================================================

def test_datenbank_tabellen():
    """Prüft ob alle 5 Tabellen korrekt in der In-Memory-Datenbank angelegt werden."""
    conn = sqlite3.connect(":memory:")
    database.erstelle_tabellen(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabellen = {zeile[0] for zeile in cursor.fetchall()}

    assert "skills" in tabellen
    assert "erfahrungen" in tabellen
    assert "applications" in tabellen
    assert "stellenanzeigen" in tabellen
    assert "skill_trends" in tabellen

    conn.close()
