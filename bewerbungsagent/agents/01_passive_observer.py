import psutil
import os
import sys
import json
import time
import schedule
import importlib.util
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from utils.ollama_client import ask_ollama

# 02_skill_extractor.py per importlib laden (wegen numerischem Dateinamen)
_spec = importlib.util.spec_from_file_location(
    "skill_extractor",
    os.path.join(os.path.dirname(__file__), "02_skill_extractor.py")
)
skill_extractor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(skill_extractor)

# Zuhause-Verzeichnis des Benutzers beobachten
HOME_DIR = os.path.expanduser("~")

# Liste der zuletzt geänderten Dateien (globale Variable)
geaenderte_dateien = []


class DateiBeobachter(FileSystemEventHandler):
    """Watchdog-Handler: merkt sich geänderte Dateien."""

    def on_modified(self, event):
        if not event.is_directory:
            geaenderte_dateien.append(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            geaenderte_dateien.append(event.src_path)


def hole_aktive_prozesse():
    """Gibt eine Liste der aktuell laufenden Prozesse zurück."""

    prozesse = []
    for proc in psutil.process_iter(["name", "status"]):
        try:
            if proc.info["status"] == psutil.STATUS_RUNNING:
                prozesse.append(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Duplikate entfernen
    return list(set(prozesse))


def hole_aktives_fenster():
    """Versucht den Titel des aktiven Fensters zu lesen (Windows/Mac/Linux)."""

    # Windows: pygetwindow verwenden
    try:
        import pygetwindow as gw
        fenster = gw.getActiveWindow()
        if fenster:
            return fenster.title
    except Exception:
        pass

    # Mac: AppleScript als Fallback
    try:
        import subprocess
        script = 'tell application "System Events" to get name of first application process whose frontmost is true'
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    # Linux: xdotool als Fallback
    try:
        import subprocess
        result = subprocess.run(["xdotool", "getactivewindow", "getwindowname"], capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return "Unbekannt"


def ist_pc_idle():
    """Prüft ob der PC im Leerlauf ist (CPU-Auslastung sehr niedrig)."""

    cpu_auslastung = psutil.cpu_percent(interval=2)
    return cpu_auslastung < 5.0


def beobachtung_durchfuehren():
    """Hauptfunktion: sammelt Aktivitätsdaten und sendet sie an Ollama."""

    print(f"\n[{datetime.now().strftime('%H:%M')}] Starte Beobachtung...")

    # Leerlauf-Erkennung
    if ist_pc_idle():
        print("Leerlauf erkannt — Beobachtung übersprungen.")
        return

    # Aktuelle Aktivitätsdaten sammeln
    prozesse = hole_aktive_prozesse()
    aktives_fenster = hole_aktives_fenster()

    # Zuletzt geänderte Dateien (max. 20 merken)
    letzte_dateien = geaenderte_dateien[-20:] if geaenderte_dateien else []
    geaenderte_dateien.clear()

    # Aktivitätsdaten als Dict zusammenbauen
    aktivitaet = {
        "prozesse": prozesse[:30],  # Max. 30 Prozesse senden
        "aktives_fenster": aktives_fenster,
        "geaenderte_dateien": letzte_dateien,
        "zeitpunkt": datetime.now().isoformat()
    }

    # Prompt für Ollama erstellen
    prompt = f"""Welche Skills lassen sich aus dieser PC-Aktivität ableiten?
Antworte NUR mit JSON, kein anderer Text:
{{"hard_skills": [], "soft_skills": [], "tools": [], "erfahrungslevel": {{}}}}

Aktivitätsdaten:
{json.dumps(aktivitaet, ensure_ascii=False, indent=2)}"""

    # Ollama anfragen
    print("Sende Aktivitätsdaten an LLM...")
    antwort = ask_ollama(prompt)

    if antwort is None:
        print("Keine Antwort von Ollama erhalten.")
        return

    # JSON aus Antwort parsen
    try:
        start = antwort.find("{")
        ende = antwort.rfind("}") + 1
        if start == -1 or ende == 0:
            print("Kein JSON in der LLM-Antwort gefunden.")
            return

        skills = json.loads(antwort[start:ende])
        print(f"Skills erkannt: {skills.get('hard_skills', [])} | {skills.get('soft_skills', [])}")

        # Skills ins Profil schreiben
        skill_extractor.update_profil(skills)

    except json.JSONDecodeError:
        print("LLM hat kein gültiges JSON zurückgegeben.")


def starte_beobachter():
    """Startet den Watchdog-Observer für das Home-Verzeichnis."""

    handler = DateiBeobachter()
    observer = Observer()
    # Nur eine Ebene tief beobachten, um Performance zu schonen
    observer.schedule(handler, HOME_DIR, recursive=False)
    observer.start()
    return observer


def starte_agent():
    """Startet den passiven Beobachter-Agenten mit 30-Minuten-Intervall."""

    print("Passiver Beobachter gestartet. Läuft alle 30 Minuten.")

    # Watchdog starten
    observer = starte_beobachter()

    # Zeitplan festlegen
    schedule.every(30).minutes.do(beobachtung_durchfuehren)

    # Einmal sofort ausführen
    beobachtung_durchfuehren()

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nBeobachter gestoppt.")
        observer.stop()
        observer.join()


# Direkt ausführen
if __name__ == "__main__":
    starte_agent()