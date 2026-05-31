import sqlite3
import json
import os
import sys
import time
import re
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Datenbankpfad
DB_PFAD = os.path.join(os.path.dirname(__file__), "..", "data", "marktdaten.db")


def _verbinde_db():
    """Erstellt eine Datenbankverbindung und legt Tabellen an, falls nötig."""

    os.makedirs(os.path.dirname(DB_PFAD), exist_ok=True)
    conn = sqlite3.connect(DB_PFAD)
    cursor = conn.cursor()

    # Tabelle für Stellenanzeigen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stellenanzeigen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jobtitel TEXT,
            unternehmen TEXT,
            ort TEXT,
            skills_json TEXT,
            datum TEXT,
            url TEXT UNIQUE
        )
    """)

    # Tabelle für Skill-Trends
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skill_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_name TEXT,
            datum TEXT,
            anzahl_nennungen INTEGER,
            UNIQUE(skill_name, datum)
        )
    """)

    conn.commit()
    return conn


def _extrahiere_skills_aus_text(text):
    """Einfache Keyword-Erkennung für gängige Tech-Skills."""

    # Liste bekannter Skills (einfacher als LLM für Batch-Verarbeitung)
    bekannte_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "React", "Vue", "Angular",
        "Node.js", "Django", "FastAPI", "Flask", "Spring", "Docker", "Kubernetes",
        "AWS", "Azure", "GCP", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
        "Git", "CI/CD", "DevOps", "Machine Learning", "Deep Learning", "TensorFlow",
        "PyTorch", "Pandas", "Spark", "Kafka", "REST", "GraphQL", "Microservices",
        "Linux", "Agile", "Scrum", "Jira", "Confluence", "Excel", "Power BI",
        "Tableau", "R", "Scala", "Go", "Rust", "C++", "C#", ".NET", "PHP"
    ]

    gefunden = []
    text_lower = text.lower()

    for skill in bekannte_skills:
        if skill.lower() in text_lower:
            gefunden.append(skill)

    return gefunden


def scrape_jobs(jobtitel="Software Entwickler", ort="Deutschland", anzahl=50):
    """Scrapt Stellenanzeigen von Indeed und speichert sie in der Datenbank."""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    conn = _verbinde_db()
    cursor = conn.cursor()
    gespeichert = 0
    seite = 0

    print(f"Starte Job-Scraping für '{jobtitel}' in '{ort}'...")

    # Mehrere Seiten durchsuchen bis Zielanzahl erreicht
    while gespeichert < anzahl:
        such_url = (
            f"https://de.indeed.com/jobs"
            f"?q={requests.utils.quote(jobtitel)}"
            f"&l={requests.utils.quote(ort)}"
            f"&start={seite * 10}"
        )

        try:
            response = requests.get(such_url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Scraping (Seite {seite}): {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        karten = soup.find_all("div", class_="job_seen_beacon")

        if not karten:
            print(f"Keine weiteren Ergebnisse auf Seite {seite}.")
            break

        for karte in karten:
            try:
                titel_el = karte.find("h2", class_="jobTitle")
                titel = titel_el.get_text(strip=True) if titel_el else "Unbekannt"

                firma_el = karte.find("span", {"data-testid": "company-name"})
                firma = firma_el.get_text(strip=True) if firma_el else "Unbekannt"

                ort_el = karte.find("div", {"data-testid": "text-location"})
                job_ort = ort_el.get_text(strip=True) if ort_el else ort

                beschreibung_el = karte.find("div", class_="job-snippet")
                beschreibung = beschreibung_el.get_text(strip=True) if beschreibung_el else ""

                link_el = karte.find("a", class_="jcs-JobTitle")
                job_url = "https://de.indeed.com" + link_el["href"] if link_el and link_el.get("href") else ""

                # Skills aus Beschreibung extrahieren
                skills = _extrahiere_skills_aus_text(f"{titel} {beschreibung}")
                skills_json = json.dumps(skills, ensure_ascii=False)

                # In Datenbank speichern (URL als eindeutiger Schlüssel)
                cursor.execute("""
                    INSERT OR IGNORE INTO stellenanzeigen
                    (jobtitel, unternehmen, ort, skills_json, datum, url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (titel, firma, job_ort, skills_json, date.today().isoformat(), job_url))

                if cursor.rowcount > 0:
                    gespeichert += 1

            except Exception:
                continue

        conn.commit()
        seite += 1

        # Kurze Pause zwischen Anfragen
        time.sleep(2)

        if seite > 10:
            break

    conn.close()
    print(f"{gespeichert} neue Stellenanzeigen gespeichert.")
    return gespeichert


def aktualisiere_skill_trends():
    """Zählt Skill-Nennungen aus den gespeicherten Stellenanzeigen und schreibt sie in skill_trends."""

    conn = _verbinde_db()
    cursor = conn.cursor()
    heute = date.today().isoformat()

    # Alle Stellenanzeigen von heute laden
    cursor.execute("SELECT skills_json FROM stellenanzeigen WHERE datum = ?", (heute,))
    zeilen = cursor.fetchall()

    # Skills zählen
    skill_zaehler = {}
    for (skills_json,) in zeilen:
        try:
            skills = json.loads(skills_json)
            for skill in skills:
                skill_zaehler[skill] = skill_zaehler.get(skill, 0) + 1
        except json.JSONDecodeError:
            continue

    # In Datenbank speichern
    for skill, anzahl in skill_zaehler.items():
        cursor.execute("""
            INSERT INTO skill_trends (skill_name, datum, anzahl_nennungen)
            VALUES (?, ?, ?)
            ON CONFLICT(skill_name, datum) DO UPDATE SET anzahl_nennungen = excluded.anzahl_nennungen
        """, (skill, heute, anzahl))

    conn.commit()
    conn.close()
    print(f"Skill-Trends aktualisiert: {len(skill_zaehler)} Skills gezählt.")


def analyze_trends():
    """Analysiert Skill-Trends mit LinearRegression und gibt Signale zurück."""

    conn = _verbinde_db()

    # Letzte 30 Tage laden
    vor_30_tagen = (date.today() - timedelta(days=30)).isoformat()
    df = pd.read_sql_query(
        "SELECT skill_name, datum, anzahl_nennungen FROM skill_trends WHERE datum >= ? ORDER BY datum",
        conn,
        params=(vor_30_tagen,)
    )
    conn.close()

    if df.empty:
        print("Keine Trenddaten vorhanden. Bitte erst scrape_jobs() ausführen.")
        return []

    signale = []

    # Jeden Skill einzeln analysieren
    for skill_name in df["skill_name"].unique():
        skill_df = df[df["skill_name"] == skill_name].copy()

        if len(skill_df) < 3:
            # Zu wenig Datenpunkte für sinnvolle Trendanalyse
            continue

        # Datum als Zahl kodieren (Tage seit erstem Eintrag)
        skill_df["tag_nr"] = range(len(skill_df))
        X = skill_df[["tag_nr"]].values
        y = skill_df["anzahl_nennungen"].values

        # Lineare Regression anpassen
        modell = LinearRegression()
        modell.fit(X, y)
        steigung = modell.coef_[0]

        # R² als Signalstärke nutzen
        r_squared = modell.score(X, y)
        signal_staerke = round(abs(r_squared), 2)

        # Trend bestimmen
        if steigung > 0.5:
            trend = "wachsend"
        elif steigung < -0.5:
            trend = "sinkend"
        else:
            trend = "stagnierend"

        signale.append({
            "skill": skill_name,
            "trend": trend,
            "signal_staerke": signal_staerke,
            "durchschnitt_nennungen": round(float(y.mean()), 1)
        })

    # Nach Signalstärke sortieren
    signale.sort(key=lambda x: x["signal_staerke"], reverse=True)
    print(f"Trendanalyse abgeschlossen: {len(signale)} Skills analysiert.")
    return signale


def hole_trend_daten_fuer_chart():
    """Gibt aggregierte Trenddaten für die Streamlit-Visualisierung zurück."""

    conn = _verbinde_db()
    vor_7_tagen = (date.today() - timedelta(days=7)).isoformat()

    df = pd.read_sql_query(
        "SELECT skill_name, SUM(anzahl_nennungen) as gesamt FROM skill_trends WHERE datum >= ? GROUP BY skill_name ORDER BY gesamt DESC LIMIT 20",
        conn,
        params=(vor_7_tagen,)
    )
    conn.close()
    return df


# Direkt ausführen zum Testen
if __name__ == "__main__":
    scrape_jobs("Python Entwickler", "Berlin", anzahl=10)
    aktualisiere_skill_trends()
    signale = analyze_trends()
    for s in signale[:5]:
        print(f"{s['skill']}: {s['trend']} (Stärke: {s['signal_staerke']})")