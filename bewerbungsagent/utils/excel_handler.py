import pandas as pd
import os


def exportiere_bewerbungen(conn, dateipfad="data/bewerbungen.xlsx"):
    """Liest alle Bewerbungen aus SQLite und schreibt sie als Excel-Datei."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT job_titel, unternehmen, match_score, status, beworben_am, antwort, url
        FROM applications
        ORDER BY beworben_am DESC
    """)
    zeilen = cursor.fetchall()

    spalten = ["Job Titel", "Unternehmen", "Match %", "Status", "Beworben am", "Antwort", "Link"]
    df = pd.DataFrame(zeilen, columns=spalten)

    # Ordner anlegen falls nötig
    ordner = os.path.dirname(dateipfad)
    if ordner:
        os.makedirs(ordner, exist_ok=True)

    df.to_excel(dateipfad, index=False)
    print(f"Bewerbungen exportiert nach: {dateipfad}")
