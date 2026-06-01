# KI-Bewerbungsagent – Single Source of Truth
 
> **Uni-Projektkurs | GenAI Track | Team Bewerbungsagent**
> Version 1.0 | Juni 2026 | Nächste Präsentation: P1 – 16.06.2026
 
Dieses Dokument ist die **verbindliche Single Source of Truth** für das gesamte Team.
Alle Architekturentscheidungen, Tools und Abgrenzungen gelten für alle Teammitglieder gleichermassen.
 
---
 
## Inhaltsverzeichnis
 
1. [Projektuebersicht](#1-projektuebersicht)
2. [Systemarchitektur](#2-systemarchitektur)
3. [Agenten-Beschreibung](#3-agenten-beschreibung)
4. [Verbindliche Technologieentscheidungen](#4-verbindliche-technologieentscheidungen)
5. [Datenquellen](#5-datenquellen)
6. [Projektstruktur](#6-projektstruktur)
7. [Vollständiger Tech Stack](#7-vollständiger-tech-stack)
8. [Gestrichene Komponenten](#8-gestrichene--zurückgestellte-komponenten)
9. [Erfolgskriterien](#9-erfolgskriterien)
10. [Offene Entscheidungen](#10-offene-entscheidungen-muss-klärungen)
11. [Zeitplan](#11-zeitplan--meilensteine)
12. [Risiken](#12-top-risiken)
13. [Installation](#13-installation--setup)
---
 
## 1. Projektuebersicht
 
Der KI-Bewerbungsagent ist ein autonomes, mehrschichtiges KI-System, das Bewerbern hilft, sich effizienter und gezielter auf dem Jobmarkt zu positionieren. Im Gegensatz zu einem einfachen Chatbot handelt das System proaktiv: Es beobachtet, lernt, analysiert und handelt.
 
> *„Unser System kennt den User besser als er sich selbst kennt – und wird mit der Zeit immer besser darin, ihn auf dem Jobmarkt zu positionieren."*
 
### Was das System tut
 
- Passives Skill-Tracking im Hintergrund (**Alleinstellungsmerkmal**)
- Aktive Skill-Extraktion aus Gesprächen und Dokumenten
- Automatisierte Bewerbungserstellung und -verwaltung
- Kontinuierliche Marktbeobachtung und Trendanalyse
- Proaktive Karriereempfehlungen
### Datenschutzprinzip
 
Privacy by Design ist ein Kernprinzip des Systems:
 
- Ollama läuft vollständig lokal – keine Daten verlassen den PC
- Das Skill-Profil wird lokal gespeichert (SQLite-Datenbank)
- Der passive Beobachter sendet keine Daten in die Cloud
- Claude API wird **nur** für Anschreiben-Generierung genutzt (kein Profil-Upload)
- Der User kann jederzeit sein Profil einsehen und löschen
---
 
## 2. Systemarchitektur
 
### 2.1 Agenten-Workflow
 
```
                        ┌─────────────────┐
                        │   User Input    │
                        │ CV + Wunschbereich│
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  Agent 1b –     │
                        │ Skill Extractor │  ◄── passiv/optional ── Agent 1a
                        │ Skills aus CV & │          (Passiver Beobachter,
                        │ PDFs → SQLite   │           trackt PC-Aktivität)
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │ SQLite Datenbank│
                        │ Gemeinsame DB   │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │   Agent 2 –     │
                        │ Bewerbungsagent │
                        │ Scrapt Stellen  │
                        │ Match-Score     │
                        │ Anschreiben     │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │ User Bestätigung│  ⚠️  IMMER erst bestätigen!
                        │ Bewerbung senden?│
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │   Bewerbungs-   │
                        │    Tracking     │
                        │ SQLite Tabelle  │
                        └────────┬────────┘
                                 │
          ┌──────────────────────▼──────────────────────┐
          │              Agent 3 –                      │
          │           Marktbeobachter                   │
          │  Analysiert Jobmarkt täglich                │
          │  Erkennt Skill-Trends (LinearRegression)    │
          │  Berechnet Gap-Score zum Nutzerprofil       │
          └───────────┬────────────────────┬────────────┘
                      │                    │
             ┌────────▼──────┐    ┌────────▼──────┐
             │Lernempfehlungen│    │  Streamlit UI │
             │"Kubernetes fehlt│   │ Zeigt Empf.  │
             │ bei 60% deiner │    │ & Status     │
             │ Zielstellen"   │    └───────────────┘
             └───────┬────────┘
                     │
          FEEDBACK LOOP (USP) ──────────────► zurück zu Agent 1b
```
 
### 2.2 Die 4 Agenten im Überblick
 
| Agent | Datei | Trigger | Kernaufgabe |
|---|---|---|---|
| Agent 1a – Passiver Beobachter | `agents/passive_observer.py` | Alle 30 Min (schedule) | PC-Aktivität beobachten, Skills inferieren |
| Agent 1b – Skill Extractor | `agents/skill_extractor.py` | Manuell / Datei-Upload | Skills aus Text + PDF extrahieren |
| Agent 2 – Bewerbungsagent | `agents/application_agent.py` | Manuell durch User | Stellen finden, abgleichen, Anschreiben generieren |
| Agent 3 – Marktbeobachter | `agents/market_agent.py` | Täglich automatisch | Jobmarkt scannen, Trends berechnen |
 
### 2.3 Datenfluss zwischen den Agenten
 
Alle Agenten kommunizieren **ausschliesslich** über definierte JSON-Schemas – kein direkter DB-Zugriff zwischen Agenten.
 
| Von | Nach | Payload (JSON) |
|---|---|---|
| Agent 1a | Agent 1b | `{aktivitaet, dauer_min, kontext}` |
| Agent 1b | SQLite (profil) | `{skill, level, kategorie, quelle}` |
| Agent 3 | Agent 1b | `{skill, trend, signal_staerke}` |
| Agent 2 | SQLite (bewerbungen) | `{jobtitel, unternehmen, match_score, status}` |
 
### 2.4 Der Feedback-Loop
 
Das System wächst mit dem User – das ist das zentrale Alleinstellungsmerkmal:
 
1. Agent 1a beobachtet kontinuierlich PC-Aktivität
2. Agent 1b aktualisiert das Profil wenn neue Skills erkannt werden
3. Agent 3 erkennt: „Jetzt passen X% mehr Stellen zum Profil"
4. Marktsignale fliessen zurück an Agent 1b → Profil wird neu priorisiert
5. Agent 2 schreibt bessere, passgenauere Bewerbungen
---
 
## 3. Agenten-Beschreibung
 
### Agent 1a – Passiver Beobachter
 
> ⚠️ **Status: Zurückgestellt** – Code behalten, aber NICHT in MVP einbinden. Privacy-Konzept erst mit Professor klären.
 
Läuft still im Hintergrund und beobachtet die PC-Aktivität des Users.
 
**Beobachtete Daten:**
- Welche Programme/Apps geöffnet sind (`psutil`, `pygetwindow`)
- Welche Dateien bearbeitet werden (`watchdog`)
- Browser-Aktivität (z.B. Stack Overflow → Debugging-Session)
**KI-Einsatz:**
- LLM (Ollama llama3.1:8b) interpretiert den Kontext der PC-Aktivität
- Beispiel: VS Code 2h + Stack Overflow = Python-Debugging-Session
- Erkannte Skills werden automatisch ins Profil gespeichert
**Edge Cases:**
- PC im Leerlauf → keine Skill-Erkennung, kein Eintrag
- Mehrere User am selben PC → Profil ist user-spezifisch (`nutzer_id`)
---
 
### Agent 1b – Skill Extractor
 
> ✅ **Status: Kernkomponente – vollständig implementiert für P1**
 
Ergänzt den passiven Beobachter: Der User kann aktiv von Erlebnissen erzählen oder Dokumente hochladen.
 
**Eingabequellen:**
- Freitext (z.B. „Heute habe ich eine Präsentation vor 20 Leuten gehalten")
- Hochgeladene Studienarbeiten oder Zeugnisse (PDF via PyMuPDF)
- Beschreibung vergangener Jobs oder Projekte
**Extrahierter Output (JSON):**
```json
{
  "hard_skills": ["Python", "Datenanalyse"],
  "soft_skills": ["Präsentationskompetenz", "Kommunikation"],
  "tools": ["PowerPoint", "Jupyter Notebook"],
  "erfahrungslevel": {"Python": 3, "Präsentation": 4}
}
```
 
**Profil-Merging-Logik:**
- Höherer Level gewinnt bei widersprüchlichen Quellen
- Quelle wird protokolliert (`passive_observer`, `skill_extractor`, `manuell`)
- Keine Duplikate – bestehende Skills werden nur aktualisiert
**Edge Cases:**
- Bild-PDF ohne Text → Fehlermeldung + Hinweis auf manuelle Eingabe
- Python Level 2 und Level 4 aus verschiedenen Quellen → Level 4 gewinnt
---
 
### Agent 2 – Bewerbungsagent
 
> 🟡 **Status: Ziel für P2 (30.06.). Schritte 1–2 für P1 als Prototyp.**
 
**Prozess in 4 Schritten:**
 
1. **Stellen finden** – Bundesagentur für Arbeit REST API
2. **Profil abgleichen** – Semantic Embedding-Matching (Stufe 1: Keywords, Stufe 2: Embeddings)
3. **Anschreiben generieren** – Claude API (`claude-sonnet-4-20250514`)
4. **Nutzerfreigabe + Absenden** – `smtplib` / Gmail API
> ⚠️ **IMMER erst Nutzerbestätigung einholen bevor eine Bewerbung abgesendet wird! (FR-007)**
 
**KI-Einsatz:**
 
| Schritt | KI? | Technik |
|---|---|---|
| Stellenanzeige lesen | ✅ | LLM |
| Profil abgleichen | ✅ | Embedding-Matching + LLM |
| Anschreiben schreiben | ✅ | Claude API |
| Mail absenden | ❌ | smtplib |
| Eintrag in SQLite | ❌ | sqlite3 |
 
**Edge Cases:**
- Stellenbörse ohne API → Fallback auf HTML-Scraping (BeautifulSoup)
- Bewerbungsportal nur über Website → Link + vorbereitetes Anschreiben, kein Auto-Versand
- Doppelte Bewerbung auf dieselbe Stelle → Warnung + Abbruch
---
 
### Agent 3 – Marktbeobachter
 
> 🟡 **Status: Ziel für P3 (14.07.). Trendanalyse-Logik aus bestehendem Code übernehmen.**
 
**Prozess in 5 Schritten:**
 
1. Stellen scrapen (täglich, min. 50 neue Anzeigen – SC-005)
2. Skills extrahieren via LLM aus jeder Stellenanzeige → SQLite
3. Trendanalyse mit `LinearRegression` (scikit-learn)
4. Abgleich mit Nutzerprofil (direkte Matches / Lücken / ableitbare Skills)
5. Proaktive Benachrichtigung + Marktsignale zurück an Agent 1b
---
 
## 4. Verbindliche Technologieentscheidungen
 
### 4.1 LLM-Strategie ✅ Entschieden
 
| Aufgabe | Modell | Begründung |
|---|---|---|
| Routineaufgaben (Skill-Extraktion, Marktanalyse) | Ollama `llama3.1:8b` | Kostenlos, läuft dauerhaft lokal |
| Anschreiben generieren | Claude API `claude-sonnet-4-20250514` | Nur hier zählt Qualität |
| Embeddings (Semantic Matching) | `sentence-transformers all-MiniLM-L6-v2` | Lokal, kostenlos |
| Embedding-Speicher | SQLite BLOB | Kein ChromaDB – unnötige Abhängigkeit |
 
**Zentraler LLM-Client** mit automatischem Switch:
 
```python
# utils/llm_client.py
def frage_ki(prompt: str, qualitaet: str = "normal") -> str:
    if qualitaet == "hoch":
        # Claude API – nur für Anschreiben
        return claude_api(prompt, model="claude-sonnet-4-20250514")
    else:
        # Ollama lokal – für alles andere
        return ollama_lokal(prompt, model="llama3.1:8b")
```
 
### 4.2 Agenten-Framework ⚠️ Offen (OP-01)
 
> Noch nicht entschieden – muss vor P1 im Team geklärt werden.
 
| Framework | Vorteile | Nachteile | Empfehlung |
|---|---|---|---|
| **LangGraph** | Exakte Kontrolle, gut für Feedback-Loops, bereits in requirements.txt | Komplexer Einstieg, mehr Boilerplate | Wenn Feedback-Loop im Vordergrund |
| **CrewAI** | Einfacher Einstieg, role-basierte Agenten, automatische Kontext-Weitergabe | Weniger Kontrolle, neues Framework für alle | Wenn schnelle Demo wichtiger |
| **Keine (pure Funktionen)** | Einfachstes, kein Overhead | Orchestrierung fragil, kein echter Feedback-Loop | Nur als letzter Ausweg |
 
### 4.3 Datenspeicherung ✅ Entschieden
 
> **Einheitlich in SQLite** – keine drei verschiedenen Speicherformate mehr!
 
| Daten | Speicherort | Format |
|---|---|---|
| Skill-Profil | `bewerbungsagent.db` | Tabelle: `skills` |
| Bewerbungen | `bewerbungsagent.db` | Tabelle: `applications` |
| Marktdaten | `bewerbungsagent.db` | Tabellen: `stellenanzeigen`, `skill_trends` |
| Skill-Embeddings | `bewerbungsagent.db` | BLOB-Spalte in `skills` |
| Excel-Export | `bewerbungen.xlsx` (optional) | openpyxl – nur Zusatzfunktion |
 
### 4.4 Stellenquelle ✅ Entschieden
 
> **Bundesagentur für Arbeit REST API** statt Indeed-Scraping.
> Indeed-Scraping ist der grösste Einzelrisikofaktor (Anti-Bot, HTML-Änderungen – R-01).
 
- Primär: `rest.arbeitsagentur.de` (offizielle API, kostenlos)
- Fallback: HTML-Scraping mit BeautifulSoup falls API nicht verfügbar
- ~~Indeed.de-Scraping~~: **gestrichen**
### 4.5 Skill-Matching ✅ Entschieden: Hybridansatz
 
- **Stufe 1:** Keyword-Matching (0ms, kein LLM) für direkte Treffer
- **Stufe 2:** Semantic Embeddings (`sentence-transformers`) für indirekte Treffer
- **Finale Bewertung:** LLM-Score für detaillierte Analyse (fehlende Skills, lernbare Skills)
- ~~Reiner LLM-Score~~: **gestrichen** – nicht reproduzierbar (R-05)
### 4.6 Frontend ✅ Entschieden
 
- **P1 (16.06.):** Streamlit – besteht bereits, visuell gut für Demo
- **P2 (30.06.):** Streamlit erweitern oder auf FastAPI + HTML umstellen
- CLI als Fallback – immer verfügbar
---
 
## 5. Datenquellen
 
### 5.1 Eingabedaten
 
| Datenquelle | Format | Liefert | Agent | Risiko |
|---|---|---|---|---|
| PC-Prozesse & aktives Fenster | Live (`psutil`, `pygetwindow`) | App-Namen, Aktivitätsdauer | 1a | Nur Windows |
| Bearbeitete Dateien | Dateipfade (`watchdog`) | Dateiendungen, Ordnerstruktur | 1a | Datenschutz klären |
| Studienarbeiten, Zeugnisse | PDF / DOCX | Rohtext → Skills (PyMuPDF) | 1b | Bild-PDFs nicht lesbar |
| Freitext des Nutzers | String (Streamlit UI) | Erlebnisse, Tätigkeitsbeschreibungen | 1b | Gering |
| Stellenanzeigen | Bundesagentur REST API + HTML | Jobtitel, Anforderungen, Ort, URL | 2 + 3 | Rate Limits möglich |
 
### 5.2 SQLite Datenbankschema
 
```sql
-- Skill-Profil
CREATE TABLE skills (
    id INTEGER PRIMARY KEY,
    nutzer_id TEXT,
    name TEXT,
    kategorie TEXT,          -- Hard Skill / Soft Skill / Tool
    level INTEGER,           -- 1-5
    quelle TEXT,             -- passive_observer / skill_extractor / manuell
    zuletzt_aktualisiert TEXT,
    embedding_blob BLOB
);
 
-- Erfahrungen
CREATE TABLE erfahrungen (
    id INTEGER PRIMARY KEY,
    nutzer_id TEXT,
    beschreibung TEXT,
    datum TEXT
);
 
-- Bewerbungs-Tracker
CREATE TABLE applications (
    id INTEGER PRIMARY KEY,
    jobtitel TEXT,
    unternehmen TEXT,
    match_score INTEGER,
    status TEXT,
    beworben_am TEXT,
    antwort_datum TEXT,
    link TEXT
);
 
-- Marktdaten
CREATE TABLE stellenanzeigen (
    id INTEGER PRIMARY KEY,
    jobtitel TEXT,
    unternehmen TEXT,
    ort TEXT,
    skills_json TEXT,
    datum TEXT,
    quelle_url TEXT
);
 
CREATE TABLE skill_trends (
    id INTEGER PRIMARY KEY,
    skill_name TEXT,
    datum TEXT,
    anzahl_nennungen INTEGER,
    region TEXT
);
```
 
---
 
## 6. Projektstruktur
 
```
bewerbungsagent/
│
├── agents/
│   ├── passive_observer.py     # Agent 1a – zurückgestellt (nicht im MVP)
│   ├── skill_extractor.py      # Agent 1b – Skill-Extraktion aus Text/PDF
│   ├── application_agent.py    # Agent 2  – Bewerbungsagent
│   └── market_agent.py         # Agent 3  – Marktbeobachter
│
├── utils/
│   ├── llm_client.py           # Zentraler LLM-Client (Ollama + Claude API)
│   ├── pdf_parser.py           # PDF-Textextraktion (PyMuPDF)
│   ├── excel_handler.py        # Excel-Export (optional)
│   └── bundesagentur_api.py    # Bundesagentur REST API Client (NEU)
│
├── data/
│   ├── bewerbungsagent.db      # SQLite – alle Daten
│   └── bewerbungen.xlsx        # optionaler Excel-Export
│
├── tests/
│   └── test_agents.py          # pytest Tests
│
├── app.py                      # Streamlit UI
├── database.py                 # SQLite Setup + Schema
└── requirements.txt
```
 
> ⚠️ **Keine numerischen Präfixe** (`01_`, `02_`, ...) – verursachen `importlib`-Hacks.
> **Kein `src/`-Layout** – flache Struktur wie im bestehenden Code.
 
---
 
## 7. Vollständiger Tech Stack
 
| Komponente | Tool / Library | Zweck |
|---|---|---|
| LLM Lokal | Ollama `llama3.1:8b` | Routineaufgaben (kostenlos, lokal) |
| LLM Qualität | Claude API `claude-sonnet-4-20250514` | Nur Anschreiben-Generierung |
| Embeddings | `sentence-transformers all-MiniLM-L6-v2` | Semantic Matching |
| Agenten-Framework | LangGraph **oder** CrewAI | TBD – OP-01 |
| Datenbank | SQLite | Alle lokalen Daten |
| UI | Streamlit | Benutzeroberfläche |
| PDF-Parsing | PyMuPDF (`fitz`) | Text aus Dokumenten extrahieren |
| Jobmarkt | requests + BeautifulSoup | Stellenanzeigen laden |
| Trendanalyse | pandas + scikit-learn | `LinearRegression` für Markttrends |
| Excel-Export | openpyxl | Optionaler Excel-Export |
| Mail-Versand | smtplib / Gmail API | Bewerbungen senden & Antworten tracken |
| Scheduling | schedule | Agenten automatisch starten |
| PC-Beobachtung | psutil, pygetwindow | Nur Agent 1a (zurückgestellt) |
| Datei-Monitoring | watchdog | Nur Agent 1a (zurückgestellt) |
| DOCX-Export | python-docx | Anschreiben als Word-Datei |
| Tests | pytest | Automatisierte Tests |
| Anthropic SDK | anthropic | Claude API Zugriff |
 
---
 
## 8. Gestrichene / Zurückgestellte Komponenten
 
| Komponente | Warum | Ersatz |
|---|---|---|
| ~~Indeed.de-Scraping~~ | Anti-Bot-Schutz, HTML-Änderungen – R-01 (Kritisch) | Bundesagentur für Arbeit API |
| ~~ChromaDB~~ | Wird nirgends benutzt, braucht C++ Compiler | Embeddings als BLOB in SQLite |
| ~~LangGraph / LangChain~~ (vorerst) | Wird nirgends benutzt – OP-01 noch offen | Entscheidung ausstehend |
| ~~profil.json~~ | Fragil bei gleichzeitigem Zugriff, nicht abfragbar | SQLite Tabelle `skills` |
| ~~pygetwindow + watchdog~~ (vorerst) | Nur für Agent 1a (zurückgestellt) | Wenn Agent 1a aktiviert wird |
| ~~Passiver Beobachter im MVP~~ | Privacy-Probleme, nur Windows | Code behalten, nicht einbinden |
 
---
 
## 9. Erfolgskriterien
 
| ID | Kriterium | Zielwert | Prüfmethode |
|---|---|---|---|
| SC-001 | Skill-Extraktion aus PDFs | ≥ 80% korrekt | Stichprobe n=10, manuell bewertet |
| SC-002 | Matching-Score Korrelation | ≥ 75% Übereinstimmung | n=20 Stellen manuell + automatisch |
| SC-003 | Stellensuche Response Time | ≤ 30 Sekunden für ≥ 5 Treffer | Zeitmessung im Test |
| SC-004 | Anschreiben-Qualität | 3 von 5 Testpersonen positiv | Nutzertest |
| SC-005 | Marktbeobachter Datenbasis | ≥ 50 neue Stellen täglich | Log-Auswertung |
| SC-006 | Tracking-Dashboard | Status korrekt ohne manuell | Demo-Prüfung |
| SC-007 | Time-to-first-Bewerbung | ≤ 10 Minuten nach Setup | Nutzertest |
 
---
 
## 10. Offene Entscheidungen (Muss-Klärungen)
 
> Diese Punkte müssen **VOR der Implementierung** im Team geklärt werden.
 
| ID | Frage | Optionen | Deadline |
|---|---|---|---|
| OP-01 | Agenten-Framework: LangGraph oder CrewAI? | LangGraph / CrewAI / Keine | Vor P1 (16.06.) |
| OP-02 | LLM: Hybridstrategie (Ollama + Claude) oder nur Claude API? | Hybrid / Nur Claude | Vor P1 |
| OP-03 | Passiver Beobachter: Mit Professor besprechen | Ja / Nein im MVP | Vor P1 |
| OP-04 | Demo-Computer: Hat er eine GPU? (sonst kein Ollama) | Klären wer den Laptop stellt | Vor P1 |
| OP-05 | Export-Format: Nur DOCX oder auch PDF? | Nur DOCX / DOCX + PDF | Vor P2 (30.06.) |
 
---
 
## 11. Zeitplan & Meilensteine
 
| Datum | Präsentation | Liefert |
|---|---|---|
| **16.06.2026** | P1 | Use Case, Architektur, Agent 1b Prototyp, Bundesagentur-API Test, SQLite Schema |
| **30.06.2026** | P2 | Agent 2 (Bewerbungsagent) funktionsfähig, Anschreiben-Generierung, Tracking |
| **14.07.2026** | P3 | Agent 3 (Marktbeobachter) + Feedback-Loop, Trendanalyse, Lernempfehlungen |
| **Final** | P4 | Vollständiges System, Live-Demo, alle Tests grün |
 
---
 
## 12. Top-Risiken
 
| ID | Risiko | Schwere | Massnahme |
|---|---|---|---|
| R-01 | Indeed-Scraping liefert keine Ergebnisse | 🔴 Kritisch | **ENTSCHIEDEN:** Bundesagentur-API |
| R-02 | Ollama nicht auf Demo-Rechner installiert | 🔴 Kritisch | OP-04 klären (GPU vorhanden?) |
| R-03 | LangGraph/ChromaDB installiert aber nicht benutzt | 🟡 Mittel | Aus `requirements.txt` entfernen |
| R-04 | JSON-Profil korrumpiert bei gleichzeitigem Zugriff | 🟡 Mittel | **ENTSCHIEDEN:** SQLite statt profil.json |
| R-05 | LLM-Match-Score nicht reproduzierbar | 🟡 Mittel | **ENTSCHIEDEN:** Hybridansatz Embedding + LLM |
| R-06 | Feedback-Loop nicht im Code implementiert | 🟡 Mittel | Expliziter Aufruf von Agent 1b durch Agent 3 |
| R-07 | Passiver Beobachter nur Windows | 🟡 Mittel | Zurückgestellt – nicht im MVP |
 
---
 
## 13. Installation & Setup
 
```bash
# 1. Ollama installieren: https://ollama.com/download
ollama pull llama3.1:8b
ollama pull nomic-embed-text
 
# 2. Repository klonen
git clone https://github.com/...
cd bewerbungsagent
 
# 3. Virtuelle Umgebung
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
 
# 4. Abhängigkeiten
pip install anthropic streamlit requests beautifulsoup4
pip install sentence-transformers python-docx pymupdf
pip install pandas scikit-learn openpyxl schedule pytest
 
# 5. Starten
streamlit run app.py
```
 
### Quick-Test ob Ollama läuft
 
```python
import ollama
r = ollama.chat(model='llama3.1:8b', messages=[{'role': 'user', 'content': 'Hallo!'}])
print(r['message']['content'])
```
 
---
 
*Single Source of Truth – Version 1.0 | Juni 2026 | Team Bewerbungsagent*
 