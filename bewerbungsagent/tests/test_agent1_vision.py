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
    """Legt eine In-Memory-Datenbank mit allen Tabellen an."""
    conn = sqlite3.connect(":memory:")
    database.erstelle_tabellen(conn)
    return conn


def erstelle_test_png(pfad):
    """Erstellt ein minimales 10x10 rotes PNG ohne externe Bibliotheken."""
    breite, hoehe = 10, 10

    # Rohdaten: Filter-Byte (0 = kein Filter) + RGB-Pixel pro Zeile
    rohdaten = b""
    for _ in range(hoehe):
        rohdaten += b"\x00"
        for _ in range(breite):
            rohdaten += b"\xFF\x00\x00"  # Rot

    def erstelle_chunk(typ, daten):
        laenge = struct.pack(">I", len(daten))
        inhalt = typ + daten
        pruefsumme = struct.pack(">I", zlib.crc32(inhalt) & 0xFFFFFFFF)
        return laenge + inhalt + pruefsumme

    # IHDR: Breite, Hoehe, Bittiefe=8, Farbtyp=2 (RGB), Kompression=0, Filter=0, Interlace=0
    ihdr = struct.pack(">IIBBBBB", breite, hoehe, 8, 2, 0, 0, 0)

    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + erstelle_chunk(b"IHDR", ihdr)
        + erstelle_chunk(b"IDAT", zlib.compress(rohdaten))
        + erstelle_chunk(b"IEND", b"")
    )

    with open(pfad, "wb") as f:
        f.write(png_bytes)


def _mock_claude_antwort(skills_dict):
    """Baut ein Mock-Objekt das eine Anthropic-API-Antwort simuliert."""
    mock_content = MagicMock()
    mock_content.text = json.dumps(skills_dict)
    mock_nachricht = MagicMock()
    mock_nachricht.content = [mock_content]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_nachricht
    return mock_client


# =====================================================================
# Test 1: Bild wird verarbeitet und Skills landen in der Datenbank
# =====================================================================

def test_verarbeite_ordner_bild_skills_in_db():
    """Prüft ob Skills aus einem Bild korrekt extrahiert und in der DB gespeichert werden."""
    erwartete_skills = {
        "hard_skills": ["Python", "Machine Learning"],
        "soft_skills": ["Problemlösung"],
        "tools": ["TensorFlow"],
        "erfahrungslevel": {"Python": 3, "Machine Learning": 2, "TensorFlow": 2},
    }

    mock_client = _mock_claude_antwort(erwartete_skills)

    with tempfile.TemporaryDirectory() as temp_ordner:
        png_pfad = os.path.join(temp_ordner, "lebenslauf.png")
        erstelle_test_png(png_pfad)

        conn = _test_db()

        with patch("agents.agent1.anthropic.Anthropic", return_value=mock_client), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_schluessel"}):
            anzahl = agent1.verarbeite_ordner(temp_ordner, "test_user", conn)

        assert anzahl == 1, "Genau eine Datei sollte verarbeitet worden sein"

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM skills WHERE nutzer_id = 'test_user'")
        gespeicherte_names = {zeile[0] for zeile in cursor.fetchall()}

        assert "Python" in gespeicherte_names
        assert "Machine Learning" in gespeicherte_names
        assert "TensorFlow" in gespeicherte_names
        assert "Problemlösung" in gespeicherte_names

        conn.close()


# =====================================================================
# Test 2: Erfahrungslevel wird korrekt gespeichert
# =====================================================================

def test_verarbeite_ordner_level_korrekt():
    """Prüft ob der Erfahrungslevel aus dem Bild korrekt in der DB landet."""
    mock_client = _mock_claude_antwort({
        "hard_skills": ["Docker"],
        "soft_skills": [],
        "tools": [],
        "erfahrungslevel": {"Docker": 3},
    })

    with tempfile.TemporaryDirectory() as temp_ordner:
        erstelle_test_png(os.path.join(temp_ordner, "skills.png"))
        conn = _test_db()

        with patch("agents.agent1.anthropic.Anthropic", return_value=mock_client), \
             patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_schluessel"}):
            agent1.verarbeite_ordner(temp_ordner, "test_user", conn)

        cursor = conn.cursor()
        cursor.execute(
            "SELECT level FROM skills WHERE nutzer_id = 'test_user' AND name = 'Docker'"
        )
        zeile = cursor.fetchone()

        assert zeile is not None, "Docker-Skill sollte gespeichert sein"
        assert zeile[0] == 3, "Level sollte 3 (Experte) sein"

        conn.close()


# =====================================================================
# Test 3: Nicht-Bilddateien werden ignoriert
# =====================================================================

def test_verarbeite_ordner_ignoriert_fremde_dateien():
    """Prüft ob .txt-Dateien übersprungen werden und nichts in der DB landet."""
    with tempfile.TemporaryDirectory() as temp_ordner:
        with open(os.path.join(temp_ordner, "notizen.txt"), "w") as f:
            f.write("Keine Skills hier.")

        conn = _test_db()

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_schluessel"}):
            anzahl = agent1.verarbeite_ordner(temp_ordner, "test_user", conn)

        assert anzahl == 0, "Keine Datei sollte verarbeitet worden sein"

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM skills WHERE nutzer_id = 'test_user'")
        assert cursor.fetchone()[0] == 0

        conn.close()


# =====================================================================
# Test 4: Fehlender API-Key gibt leeres Ergebnis zurück
# =====================================================================

def test_extrahiere_skills_aus_bild_kein_api_key(tmp_path):
    """Prüft ob bei fehlendem API-Key ein leeres Skills-Dict zurückgegeben wird."""
    png_pfad = tmp_path / "test.png"
    erstelle_test_png(str(png_pfad))

    # ANTHROPIC_API_KEY explizit leer setzen
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        ergebnis = agent1.extrahiere_skills_aus_bild(str(png_pfad))

    assert ergebnis["hard_skills"] == []
    assert ergebnis["soft_skills"] == []
    assert ergebnis["tools"] == []
