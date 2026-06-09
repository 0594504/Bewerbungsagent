import sqlite3
import os

# Datenbank liegt im data/-Unterordner
DB_PFAD = os.path.join(os.path.dirname(__file__), "data", "bewerbungsagent.db")


def verbinde_db():
    """Öffnet die SQLite-Datenbankverbindung und gibt sie zurück."""
    os.makedirs(os.path.dirname(DB_PFAD), exist_ok=True)
    conn = sqlite3.connect(DB_PFAD)
    # Spaltennamen als Keys bei fetchall() aktivieren
    conn.row_factory = sqlite3.Row
    return conn


def erstelle_tabellen(conn):
    """Legt alle 5 Tabellen an, falls sie noch nicht existieren."""
    cursor = conn.cursor()

    # Skill-Profil des Nutzers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nutzer_id TEXT NOT NULL,
            name TEXT NOT NULL,
            kategorie TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            quelle TEXT,
            zuletzt_aktualisiert TEXT,
            UNIQUE(nutzer_id, name)
        )
    """)

    # Berufserfahrungen des Nutzers (Freitext)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS erfahrungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nutzer_id TEXT NOT NULL,
            beschreibung TEXT,
            zeitraum TEXT,
            quelle TEXT,
            erstellt_am TEXT
        )
    """)

    # Gesendete und geplante Bewerbungen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nutzer_id TEXT NOT NULL,
            stellen_id INTEGER,
            job_titel TEXT,
            unternehmen TEXT,
            match_score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Entwurf',
            anschreiben_text TEXT,
            beworben_am TEXT,
            antwort TEXT,
            url TEXT,
            FOREIGN KEY(stellen_id) REFERENCES stellenanzeigen(id)
        )
    """)

    # Rohdaten von der Bundesagentur-API
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stellenanzeigen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titel TEXT,
            unternehmen TEXT,
            ort TEXT,
            beschreibung TEXT,
            url TEXT UNIQUE,
            datum TEXT
        )
    """)

    # Skill-Häufigkeiten pro Tag für Trendanalyse
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT,
            datum TEXT,
            anzahl_nennungen INTEGER,
            UNIQUE(skill_name, datum)
        )
    """)

    # beleg-Spalte nachrüsten falls sie in älteren Datenbanken fehlt
    try:
        cursor.execute("ALTER TABLE skills ADD COLUMN beleg TEXT")
        conn.commit()
    except Exception:
        pass  # Spalte existiert bereits

    conn.commit()