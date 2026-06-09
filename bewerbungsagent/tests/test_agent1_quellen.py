import json
import os
import sqlite3
import struct
import sys
import tempfile
import zlib
from unittest.mock import MagicMock, patch

import pytest

# Projektwurzel zum Suchpfad hinzufügen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database
from agents import agent1


def _test_db():
    """In-Memory-Datenbank mit allen Tabellen (inkl. beleg-Spalte)."""
    conn = sqlite3.connect(":memory:")
    database.erstelle_tabellen(conn)
    return conn


def erstelle_test_png(pfad):
    """Minimales 10x10 rotes PNG ohne externe Bibliotheken."""
    breite, hoehe = 10, 10
    rohdaten = b""
    for _ in range(hoehe):
        rohdaten += b"\x00"
        for _ in range(breite):
            rohdaten += b"\xFF\x00\x00"

    def chunk(typ, daten):
        laenge = struct.pack(">I", len(daten))
        inhalt = typ + daten
        crc = struct.pack(">I", zlib.crc32(inhalt) & 0xFFFFFFFF)
        return laenge + inhalt + crc

    ihdr = struct.pack(">IIBBBBB", breite, hoehe, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(rohdaten))
        + chunk(b"IEND", b"")
    )
    with open(pfad, "wb") as f:
        f.write(png)


def _mock_client(antwort_text):
    """Erstellt einen Mock-Anthropic-Client der antwort_text zurückgibt."""
    mock_content = MagicMock()
    mock_content.text = antwort_text
    mock_msg = MagicMock()
    mock_msg.content = [mock_content]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client


# =====================================================================
# Test 1: LinkedIn-Screenshot – spezieller Prompt wird verwendet
# =====================================================================

def test_linkedin_screenshot_skills_in_db():
    """Prüft ob LinkedIn-Screenshot korrekt erkannt und Skills gespeichert werden."""
    linkedin_skills = {
        "hard_skills": ["Senior Software Engineer", "Python", "Kubernetes"],
        "soft_skills": ["Teamführung", "Kommunikation"],
        "tools": ["GitHub Actions"],
        "erfahrungslevel": {
            "Senior Software Engineer": 3,
            "Python": 3,
            "Kubernetes": 2,
            "GitHub Actions": 2,
        },
    }

    mock_cl = _mock_client(json.dumps(linkedin_skills))

    with tempfile.TemporaryDirectory() as ordner:
        erstelle_test_png(os.path.join(ordner, "linkedin_profil.png"))
        conn = _test_db()

        with patch("agents.agent1.anthropic.Anthropic", return_value=mock_cl), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
            anzahl = agent1.verarbeite_ordner(ordner, "user1", conn)

        assert anzahl == 1

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM skills WHERE nutzer_id = 'user1'")
        namen = {z[0] for z in cursor.fetchall()}

        assert "Senior Software Engineer" in namen
        assert "Python" in namen
        assert "GitHub Actions" in namen
        assert "Teamführung" in namen

        conn.close()


def test_linkedin_verwendet_linkedin_prompt():
    """Prüft ob bei LinkedIn-Dateinamen extrahiere_skills_aus_linkedin aufgerufen wird."""
    mock_cl = _mock_client(json.dumps({
        "hard_skills": ["Java"],
        "soft_skills": [],
        "tools": [],
        "erfahrungslevel": {"Java": 2},
    }))

    with tempfile.TemporaryDirectory() as ordner:
        erstelle_test_png(os.path.join(ordner, "linkedin_screenshot.png"))
        conn = _test_db()

        with patch("agents.agent1.anthropic.Anthropic", return_value=mock_cl), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
            agent1.verarbeite_ordner(ordner, "user1", conn)

        # Der gesendete Prompt muss das Wort "LinkedIn" enthalten
        aufruf_kwargs = mock_cl.messages.create.call_args
        gesendeter_inhalt = str(aufruf_kwargs)
        assert "LinkedIn" in gesendeter_inhalt or "linkedin" in gesendeter_inhalt.lower()

        conn.close()


# =====================================================================
# Test 2: Zertifikat-Bild – beleg-Spalte wird korrekt befüllt
# =====================================================================

def test_zertifikat_bild_beleg_in_db():
    """Prüft ob Zertifikat als Hard Skill Level 3 mit beleg gespeichert wird."""
    zert_antwort = {
        "zertifikatsname": "AWS Certified Developer – Associate",
        "aussteller": "Amazon Web Services",
        "jahr": "2024",
        "zusaetzliche_skills": [],
    }

    mock_cl = _mock_client(json.dumps(zert_antwort))

    with tempfile.TemporaryDirectory() as ordner:
        erstelle_test_png(os.path.join(ordner, "zertifikat_aws.png"))
        conn = _test_db()

        with patch("agents.agent1.anthropic.Anthropic", return_value=mock_cl), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
            anzahl = agent1.verarbeite_ordner(ordner, "user1", conn)

        assert anzahl == 1

        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, level, beleg FROM skills WHERE nutzer_id = 'user1'"
        )
        zeilen = {z[0]: (z[1], z[2]) for z in cursor.fetchall()}

        assert "AWS Certified Developer – Associate" in zeilen
        level, beleg = zeilen["AWS Certified Developer – Associate"]
        assert level == 3, "Zertifikat muss Level 3 haben"
        assert "Amazon Web Services" in beleg
        assert "2024" in beleg

        conn.close()


def test_zertifikat_bild_level_drei():
    """Prüft ob extrahiere_skills_aus_zertifikat immer Level 3 zurückgibt."""
    zert_antwort = {
        "zertifikatsname": "Google Cloud Professional",
        "aussteller": "Google",
        "jahr": "2023",
        "zusaetzliche_skills": ["Cloud Computing"],
    }

    mock_cl = _mock_client(json.dumps(zert_antwort))

    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "test.png")
        erstelle_test_png(png)

        with patch("agents.agent1.anthropic.Anthropic", return_value=mock_cl), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
            skills, beleg = agent1.extrahiere_skills_aus_zertifikat(png)

    assert skills["erfahrungslevel"]["Google Cloud Professional"] == 3
    assert skills["erfahrungslevel"]["Cloud Computing"] == 3
    assert "Google" in beleg
    assert "2023" in beleg


# =====================================================================
# Test 3: certificate im Dateinamen (englisch) wird ebenfalls erkannt
# =====================================================================

def test_certificate_englischer_dateiname():
    """Prüft ob 'certificate' (englisch) im Dateinamen korrekt erkannt wird."""
    mock_cl = _mock_client(json.dumps({
        "zertifikatsname": "Scrum Master Certified",
        "aussteller": "Scrum Alliance",
        "jahr": "2022",
        "zusaetzliche_skills": [],
    }))

    with tempfile.TemporaryDirectory() as ordner:
        erstelle_test_png(os.path.join(ordner, "certificate_scrum.png"))
        conn = _test_db()

        with patch("agents.agent1.anthropic.Anthropic", return_value=mock_cl), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
            anzahl = agent1.verarbeite_ordner(ordner, "user1", conn)

        assert anzahl == 1

        cursor = conn.cursor()
        cursor.execute("SELECT name, level FROM skills WHERE nutzer_id = 'user1'")
        zeilen = {z[0]: z[1] for z in cursor.fetchall()}
        assert "Scrum Master Certified" in zeilen
        assert zeilen["Scrum Master Certified"] == 3

        conn.close()


# =====================================================================
# Test 4: Gemischter Ordner – alle drei Quellen zusammen
# =====================================================================

def test_gemischter_ordner_alle_quellen():
    """Prüft ob ein Ordner mit LinkedIn, Zertifikat und normalem Bild korrekt verarbeitet wird."""
    linkedin_mock = json.dumps({
        "hard_skills": ["DevOps Engineer"],
        "soft_skills": [],
        "tools": ["Docker"],
        "erfahrungslevel": {"DevOps Engineer": 2, "Docker": 2},
    })
    zertifikat_mock = json.dumps({
        "zertifikatsname": "Kubernetes Administrator",
        "aussteller": "CNCF",
        "jahr": "2025",
        "zusaetzliche_skills": [],
    })
    bild_mock = json.dumps({
        "hard_skills": ["SQL"],
        "soft_skills": [],
        "tools": [],
        "erfahrungslevel": {"SQL": 1},
    })

    # Antwort anhand des gesendeten Prompts bestimmen (reihenfolge-unabhängig)
    def mock_create(**kwargs):
        nachrichten = kwargs.get("messages", [])
        prompt_text = ""
        for inhalt in nachrichten[0].get("content", []):
            if isinstance(inhalt, dict) and inhalt.get("type") == "text":
                prompt_text = inhalt.get("text", "")

        if "LinkedIn" in prompt_text:
            antwort = linkedin_mock
        elif "zertifikatsname" in prompt_text.lower() or "Zertifikat" in prompt_text:
            antwort = zertifikat_mock
        else:
            antwort = bild_mock

        mock_content = MagicMock()
        mock_content.text = antwort
        mock_msg = MagicMock()
        mock_msg.content = [mock_content]
        return mock_msg

    mock_cl = MagicMock()
    mock_cl.messages.create.side_effect = mock_create

    with tempfile.TemporaryDirectory() as ordner:
        erstelle_test_png(os.path.join(ordner, "linkedin_profil.png"))
        erstelle_test_png(os.path.join(ordner, "zertifikat_k8s.png"))
        erstelle_test_png(os.path.join(ordner, "lebenslauf.png"))
        conn = _test_db()

        with patch("agents.agent1.anthropic.Anthropic", return_value=mock_cl), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
            anzahl = agent1.verarbeite_ordner(ordner, "user1", conn)

        assert anzahl == 3

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM skills WHERE nutzer_id = 'user1'")
        namen = {z[0] for z in cursor.fetchall()}

        assert "DevOps Engineer" in namen
        assert "Kubernetes Administrator" in namen
        assert "SQL" in namen

        conn.close()


# =====================================================================
# Test 5: beleg-Spalte existiert nach erstelle_tabellen()
# =====================================================================

def test_beleg_spalte_vorhanden():
    """Prüft ob die beleg-Spalte nach erstelle_tabellen korrekt angelegt wurde."""
    conn = sqlite3.connect(":memory:")
    database.erstelle_tabellen(conn)

    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(skills)")
    spalten = {zeile[1] for zeile in cursor.fetchall()}

    assert "beleg" in spalten, "beleg-Spalte muss in der skills-Tabelle vorhanden sein"
    conn.close()


# =====================================================================
# Test 6: Bestehende Tests bleiben funktionsfähig (Regression)
# =====================================================================

def test_normales_bild_unveraendert():
    """Prüft ob extrahiere_skills_aus_bild noch wie vorher funktioniert."""
    mock_cl = _mock_client(json.dumps({
        "hard_skills": ["React"],
        "soft_skills": [],
        "tools": ["Webpack"],
        "erfahrungslevel": {"React": 2, "Webpack": 1},
    }))

    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "test.png")
        erstelle_test_png(png)

        with patch("agents.agent1.anthropic.Anthropic", return_value=mock_cl), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
            ergebnis = agent1.extrahiere_skills_aus_bild(png)

    assert "React" in ergebnis["hard_skills"]
    assert "Webpack" in ergebnis["tools"]
    assert ergebnis["erfahrungslevel"]["React"] == 2
