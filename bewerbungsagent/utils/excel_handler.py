import openpyxl
from datetime import date
import os

# Pfad zur Excel-Datei
EXCEL_PFAD = os.path.join(os.path.dirname(__file__), "..", "data", "bewerbungen.xlsx")

# Spaltenüberschriften
HEADERS = ["Job Titel", "Unternehmen", "Match %", "Status", "Beworben am", "Antwort", "Link"]


def _get_oder_erstelle_workbook():
    """Lädt die Excel-Datei oder erstellt sie mit Header-Zeile, falls sie nicht existiert."""

    if os.path.exists(EXCEL_PFAD):
        wb = openpyxl.load_workbook(EXCEL_PFAD)
        ws = wb.active
    else:
        # Neue Datei mit Header-Zeile erstellen
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Bewerbungen"
        ws.append(HEADERS)

    return wb, ws


def add_bewerbung(titel, unternehmen, match_score, status, url):
    """Fügt eine neue Bewerbung als Zeile in die Excel-Datei ein."""

    wb, ws = _get_oder_erstelle_workbook()

    # Neue Zeile mit heutigem Datum einfügen
    neue_zeile = [
        titel,
        unternehmen,
        match_score,
        status,
        date.today().isoformat(),
        "",  # Antwort bleibt zunächst leer
        url
    ]
    ws.append(neue_zeile)

    # Datei speichern
    os.makedirs(os.path.dirname(EXCEL_PFAD), exist_ok=True)
    wb.save(EXCEL_PFAD)
    print(f"Bewerbung gespeichert: {titel} bei {unternehmen}")