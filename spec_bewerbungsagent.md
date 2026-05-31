# Feature Specification: Bewerbungsagent (Multi-Agent-System)

**Feature Branch:** `001-bewerbungsagent`  
**Erstellt:** 2026-05-29  
**Status:** Draft  
**Autor:** Uni-Projektteam – Teilbereich Bewerbungsagent  
**Kontext:** KI-Projektkurs, Review-Session mit Professor steht bevor

---

## Projektübersicht

Der Bewerbungsagent ist ein Multi-Agent-System, das Studierende und Berufseinsteiger dabei unterstützt, sich datenbasiert und effizient auf dem Arbeitsmarkt zu bewerben. Das System besteht aus drei spezialisierten Subagenten: **Skill Tracker**, **Bewerbungsagent** und **Marktbeobachter**. Ziel der aktuellen Phase ist es, den Use Case so weit wie möglich zu implementieren, um konkrete Knackpunkte zu identifizieren – ob es sich um ein Daten-, Schnittstellen- oder Logikproblem handelt.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Skill-Profil erstellen und automatisch aktualisieren (Priority: P1)

Als Nutzer möchte ich ein digitales Skill-Profil anlegen, das automatisch auf Basis meiner Studienarbeiten, Werkstudententätigkeiten und anderen Aktivitäten aktuell gehalten wird – damit ich beim Bewerben immer ein realistisches Bild meiner Fähigkeiten habe.

**Why this priority:** Ohne ein gepflegtes Skill-Profil können weder der Bewerbungsagent noch der Marktbeobachter sinnvoll arbeiten. Es ist die Datenbasis für das gesamte System.

**Independent Test:** Nutzer lädt eine Studienarbeit (PDF) hoch → Agent extrahiert Skills → Skill-Profil wird aktualisiert und dem Nutzer zur Bestätigung angezeigt.

**Acceptance Scenarios:**

1. **Given** ein bestehendes Skill-Profil und eine hochgeladene Studienarbeit, **When** der Skill Tracker die Datei verarbeitet, **Then** werden neu erkannte Skills dem Profil hinzugefügt und bestehende Skills in ihrer Gewichtung angepasst.
2. **Given** eine Beschreibung einer Werkstudententätigkeit (Freitext), **When** der Skill Tracker die Beschreibung analysiert, **Then** werden relevante Hard und Soft Skills extrahiert und kategorisiert.
3. **Given** ein Skill-Profil mit veralteten Skills, **When** der Marktbeobachter eine Marktanalyse liefert, **Then** werden weniger gefragte Skills im Profil entsprechend markiert.

---

### User Story 2 – Passende Stellenanzeigen finden und Bewerbung generieren (Priority: P1)

Als Nutzer möchte ich, dass der Agent für mich relevante(Relevant besser definieren?) Stellenanzeigen findet und automatisch eine auf mein Profil zugeschnittene Bewerbung (Anschreiben + angepasster Lebenslauf) erstellt – damit ich weniger Zeit für administrative Aufgaben aufwenden muss.

**Why this priority:** Das ist die Kernfunktionalität des Systems und der direkte Nutzwert für den Anwender.

**Independent Test:** Nutzer gibt Berufsbezeichnung und Ort ein → Agent liefert Top-5-Stellenanzeigen → Nutzer wählt eine aus → Agent generiert ein Anschreiben.

**Acceptance Scenarios:**

1. **Given** ein vollständiges Skill-Profil und ein gewünschter Jobtyp, **When** der Bewerbungsagent eine Suche startet, **Then** werden mindestens 5 passende Stellenanzeigen mit Matching-Score zurückgegeben.
2. **Given** eine ausgewählte Stellenanzeige, **When** der Nutzer eine Bewerbung anfordert, **Then** generiert der Agent ein individuell formuliertes Anschreiben, das Skill-Übereinstimmungen hervorhebt.
3. **Given** ein generiertes Anschreiben, **When** der Nutzer es überarbeitet und freigibt, **Then** wird es im Tracking-System als „versandt" markiert.


---

### User Story 3 – Bewerbung automatisch absenden und Rückmeldungen tracken (Priority: P2)

Als Nutzer möchte ich, dass der Agent freigegebene Bewerbungen automatisch absendet und alle Statusänderungen (z. B. Eingangsbestätigung, Einladung, Absage) für mich nachverfolgt – damit ich den Überblick behalte.

**Why this priority:** Reduziert manuellen Aufwand erheblich; setzt aber eine funktionierende Bewerbungsgenerierung voraus (P1).

**Independent Test:** Agent schickt eine Test-Bewerbung per E-Mail ab → Status wird als „versandt" im Dashboard angezeigt → simulierte Antwort-E-Mail ändert Status auf „Einladung erhalten".

**Acceptance Scenarios:**

1. **Given** eine freigegebene Bewerbung mit Kontaktdaten, **When** der Nutzer das automatische Absenden bestätigt, **Then** wird die Bewerbung per E-Mail versendet und der Versandzeitpunkt gespeichert.
2. **Given** eine versendete Bewerbung, **When** eine Antwort-E-Mail eingeht, **Then** erkennt der Agent den Status (Eingangsbestätigung / Einladung / Absage) und aktualisiert das Tracking-Dashboard.
3. **Given** eine Bewerbung ohne Rückmeldung nach 14 Tagen, **When** das System die Frist erkennt, **Then** wird dem Nutzer eine Nachfass-Option vorgeschlagen. ---> Nachfass-Option? Spezifizieren

### Proposed Changes: 
1. Was wenn die Bewerbung nur über dem Arbeitsgeber Portal abgesendet werden kann oder nur über LinkedIn, Stepstone usw...?
2. Tracking Dashboard? Gibt es schon in der .md Datei eine Beschreibung woher die daten für Tracking borad genommen werden sollte und wie das tracking Dashboard visuell aussehen sollte/ Welche metriken

---

### User Story 4 – Kontinuierliche Marktbeobachtung mit Frühindikatoren (Priority: P2)

Als Nutzer möchte ich regelmäßige, datenbasierte Berichte über den Arbeitsmarkt in meiner Region (z. B. Berlin) erhalten, inklusive Hinweisen darauf, welche Skills an Bedeutung gewinnen oder verlieren – damit ich meine Weiterbildung strategisch planen kann.

**Why this priority:** Langfristiger Mehrwert; ermöglicht proaktives Handeln statt reaktives Bewerben.

**Independent Test:** Marktbeobachter läuft einmal täglich → gibt Bericht aus: Top-5-wachsende Skills, Top-5-schrumpfende Skills, aktuelle Nachfrage für Profil-Match in Berlin.

**Acceptance Scenarios:**

1. **Given** ein konfigurierter Standort (Berlin), **When** der Marktbeobachter aktuelle Stellenanzeigen aus öffentlichen Quellen auswertet, **Then** wird ein strukturierter Bericht mit Skill-Nachfragetrends erstellt.
2. **Given** ein Skill-Profil des Nutzers, **When** ein neuer Marktbericht vorliegt, **Then** wird angezeigt, wie gut das Profil aktuell zum Markt passt (Matching-Score in %).
3. **Given** ein Frühindikator für sinkende Nachfrage nach einem Kern-Skill des Nutzers, **When** der Schwellenwert unterschritten wird, **Then** erhält der Nutzer eine proaktive Benachrichtigung mit Weiterbildungsempfehlung.

---

### Edge Cases

- Was passiert, wenn eine hochgeladene Datei keine extrahierbaren Skills enthält (z. B. ein Bild-PDF)?
- Wie verhält sich das System, wenn eine Stellenbörse keine API anbietet und nur Scraping möglich wäre?
- Was passiert bei doppelter Bewerbung auf dieselbe Stelle?
- Wie geht das System mit widersprüchlichen Informationen im Skill-Profil um (z. B. gleicher Skill mit unterschiedlichen Erfahrungsstufen)?
- Was passiert, wenn die E-Mail-Integration nicht verfügbar ist (automatisches Absenden schlägt fehl)?
- Wie werden Datenschutzanforderungen (DSGVO) beim Speichern von Bewerbungsdaten eingehalten?

---

## Agentenbeschreibungen

### Agent 1: Skill Tracker

**Verantwortung:** Verwaltung und automatische Aktualisierung des Skill-Profils.

**Aufgaben:**
- Extraktion von Skills aus hochgeladenen Dokumenten (PDFs, Texte)
- Kategorisierung in Hard Skills, Soft Skills, Tools/Technologien
- Aktualisierung von Erfahrungslevel und Relevanz-Gewichtung
- Empfang von Signalen des Marktbeobachters zur Anpassung der Skill-Priorisierung

**Inputs:** Studienarbeiten (PDF), Stellenbeschreibungen bisheriger Jobs (Freitext), Zertifikate, manuelles Nutzer-Feedback  
**Outputs:** Strukturiertes Skill-Profil (JSON), Änderungsprotokoll, Benachrichtigungen bei relevanten Profiländerungen

---

### Agent 2: Bewerbungsagent

**Verantwortung:** Suche, Matching und Generierung von Bewerbungsunterlagen.

**Aufgaben:**
- Abruf von Stellenanzeigen aus konfigurierten Quellen (z. B. LinkedIn, Stepstone, Indeed)
- Berechnung eines Matching-Scores zwischen Skill-Profil und Stellenprofil
- Generierung individualisierter Anschreiben per LLM
- Verwaltung des Bewerbungs-Trackings (Status, Zeitstempel, Kontakte)
- Optional: automatisches Absenden per E-Mail (nach Nutzerfreigabe)

**Inputs:** Skill-Profil (vom Skill Tracker), Jobtitel, Ort, Freitext-Suchparameter  
**Outputs:** Rangliste passender Stellen, generierte Bewerbungsunterlagen, Tracking-Einträge

---

### Agent 3: Marktbeobachter

**Verantwortung:** Kontinuierliche, datenbasierte Analyse des Arbeitsmarkts.

**Aufgaben:**
- Regelmäßiges Einlesen und Auswerten von Stellenanzeigen (z. B. täglich)
- Identifikation von Trends: wachsende und schrumpfende Skill-Nachfrage
- Regionaler Fokus (konfigurierbar, Standard: Berlin)
- Erkennung von Frühindikatoren (z. B. Technologiewechsel, neue Jobtitel)
- Weitergabe von Marktsignalen an den Skill Tracker

**Inputs:** Rohdaten aus Stellenbörsen, historische Trenddaten  
**Outputs:** Marktbericht (strukturiert), Frühindikator-Alerts, Profil-Matching-Score

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001:** Das System MUSS ein persistentes Skill-Profil pro Nutzer verwalten können.
- **FR-002:** Der Skill Tracker MUSS Skills aus PDF-Dokumenten automatisch extrahieren können.
- **FR-003:** Der Bewerbungsagent MUSS Stellenanzeigen aus mindestens einer externen Quelle abrufen können.
- **FR-004:** Das System MUSS einen Matching-Score (0–100%) zwischen Skill-Profil und Stellenanzeige berechnen.
- **FR-005:** Der Bewerbungsagent MUSS per LLM ein individuelles Anschreiben generieren können.
- **FR-006:** Das System MUSS alle Bewerbungen mit Status und Zeitstempel nachverfolgen.
- **FR-007:** Das System MUSS Nutzer vor dem automatischen Absenden einer Bewerbung um explizite Bestätigung bitten.
- **FR-008:** Der Marktbeobachter MUSS mindestens einmal täglich eine Marktanalyse durchführen.
- **FR-009:** Das System MUSS Frühindikatoren für sinkende Skill-Nachfrage erkennen und den Nutzer benachrichtigen.
- **FR-010:** Der Skill Tracker MUSS Marktsignale vom Marktbeobachter empfangen und das Skill-Profil entsprechend anpassen.
- **FR-011:** Das System MUSS eine regionale Konfiguration unterstützen (Berlin & Brandenburg).
- **FR-012:** Das System MUSS Bewerbungsunterlagen (Anschreiben, Lebenslauf) als bearbeitbares Dokument(DOCX) exportieren können.
- **FR-013:** Die Daten MÜSSEN lokal gespeichert. 
- **FR-014:** Die Agenten MÜSSEN untereinander über definierte Schnittstellen kommunizieren (kein direkter Datenbankzugriff zwischen Agenten).

### Key Entities

- **Skill:** Name, Kategorie (Hard/Soft/Tool), Erfahrungslevel (1–5), Zuletzt aktualisiert, Quelle
- **SkillProfil:** Nutzer-ID, Liste von Skills, Erstellungsdatum, Versionsnummer
- **Stellenanzeige:** Titel, Unternehmen, Ort, Beschreibung, Anforderungsliste, Quelle-URL, Einlesedatum
- **Bewerbung:** Nutzer-ID, Stellenanzeigen-ID, Status (Entwurf/Versandt/Einladung/Absage), Anschreiben-Text, Zeitstempel, Kontaktperson
- **Marktbericht:** Datum, Region, Top-Skills (wachsend), Top-Skills (sinkend), Datenbasis (Anzahl ausgewerteter Stellen)
- **Frühindikator:** Skill-Name, Trendrichtung, Signalstärke, Ausgelöst am

---

## Success Criteria *(mandatory)*

### Messbare Erfolgskriterien

- **SC-001:** Der Skill Tracker extrahiert aus mindestens 80% der hochgeladenen PDFs korrekte Skills (validiert durch manuelle Stichprobe von 10 Dokumenten).
- **SC-002:** Der Matching-Score korreliert mit manueller Einschätzung in mindestens 75% der Testfälle (n=20 Stellen).
- **SC-003:** Der Bewerbungsagent liefert innerhalb von 30 Sekunden nach Eingabe eines Jobtitels mindestens 5 passende Stellenanzeigen.
- **SC-004:** Ein generiertes Anschreiben erhält von mindestens 3 von 5 Testpersonen eine positive Bewertung (bezüglich Individualität und Relevanz).
- **SC-005:** Der Marktbeobachter erstellt täglich einen Bericht auf Basis von mindestens 50 neuen Stellenanzeigen aus dem konfigurierten Markt.
- **SC-006:** Das Tracking-Dashboard zeigt den aktuellen Status aller Bewerbungen ohne manuelle Aktualisierung korrekt an.
- **SC-007:** Der Nutzer kann innerhalb von 10 Minuten nach Erstkonfiguration eine vollständige Bewerbung generieren lassen.

---

## Technische Anforderungen

### Stack & Architektur

- **Sprache:** Python 3.11+
- **Agenten-Framework:** `[NEEDS CLARIFICATION: LangGraph, CrewAI, AutoGen oder eigene Implementierung?]`
- **LLM:** ChatGPT für Textgenerierung (Anschreiben, Skill-Extraktion)
- **Datenbank:** `[NEEDS CLARIFICATION: SQLite für MVP, PostgreSQL für Production?]`
- **Kommunikation zwischen Agenten:** Klar definierte JSON-Schemas über interne API-Calls oder Message Queue
- **Frontend:** `[NEEDS CLARIFICATION: CLI-basiert für MVP oder einfaches Web-UI?]`
- **Testing:** pytest

### Externe Schnittstellen

| Schnittstelle | Zweck | Status |
|---|---|---|
| Stellenbörsen-API (LinkedIn/Stepstone/Indeed) | Abruf von Stellenanzeigen | `[NEEDS CLARIFICATION: Welche APIs sind zugänglich? Gibt es API-Keys?]` |
| E-Mail-API (SMTP / Gmail API) | Automatisches Versenden von Bewerbungen | Noch nicht implementiert |
| PDF-Parser (z. B. PyMuPDF, pdfminer) | Extraktion von Text aus Dokumenten | Bibliothek verfügbar |
| Anthropic Claude API | LLM-basierte Textgenerierung | API-Key vorhanden |

### Kommunikationsschema zwischen Agenten

```
Nutzer
  │
  ▼
Bewerbungsagent ◄──────────────── Skill Tracker
  │                                      ▲
  │                                      │ Marktsignale
  ▼                                      │
Marktbeobachter ────────────────────────►│
```

---

## Offene Fragen

| # | Frage | Priorität | Verantwortlich |
|---|---|---|---|
| OQ-01 | Welches Agenten-Framework wird eingesetzt (LangGraph, CrewAI, AutoGen)? | Hoch | Team |
| OQ-02 | Welche Stellenbörsen-APIs sind für den MVP zugänglich? Gibt es Zugangsbeschränkungen? | Hoch | Team |
| OQ-03 | Wo werden Nutzerdaten gespeichert – lokal oder Cloud? Wie wird DSGVO-Konformität sichergestellt? | Hoch | Team + Professor |
| OQ-04 | Soll der MVP ein CLI-Interface haben oder ein einfaches Web-UI? | Mittel | Team |
| OQ-05 | In welchem Format sollen Bewerbungsunterlagen exportiert werden (PDF, DOCX, beide)? | Mittel | Team |
| OQ-06 | Wie granular soll das Skill-Matching sein? (Keyword-Matching vs. semantisches Embedding-Matching) | Hoch | Team |
| OQ-07 | Soll ein Review-Agent die generierten Specs und den Code eigenständig prüfen? | Mittel | Einzeln |
| OQ-08 | Wie werden die Subagenten für den Professor-Review am besten demonstriert (Logs, UI, Notebook)? | Mittel | Team |
| OQ-09 | Welche Frühindikatoren-Logik wird verwendet? Schwellenwerte basierend auf absolutem oder relativem Rückgang? | Mittel | Team |
| OQ-10 | Wie wird das System mit dem Reiseplanungs-Agenten des anderen Teilteams abgeglichen (gemeinsame Architektur-Patterns)? | Niedrig | Beide Teams |

---

## Assumptions

- Nutzer haben Zugang zu einem Anthropic Claude API-Key für die LLM-Funktionalität.
- Der MVP wird auf einem lokalen Entwicklungsrechner (nicht Cloud-deployed) betrieben.
- Für die Review-Session reicht eine Demo mit synthetischen oder anonymisierten Testdaten.
- Die Kommunikation zwischen den Agenten erfolgt synchron im MVP (kein Message-Broker nötig).
- Automatisches E-Mail-Absenden ist für den MVP optional und wird nur demonstriert, nicht produktiv eingesetzt.
- Der regionale Fokus des Marktbeobachters ist für die Demo auf Berlin beschränkt.
- Das Team hat Schreib-/Lesezugriff auf mindestens eine Stellenbörse (API oder öffentliche HTML-Seite).
- Datenschutz (DSGVO) wird für den Uni-Kurs pragmatisch behandelt; keine echten Nutzer außer dem Team selbst.

---

## Nächste Schritte

1. **Offene Fragen klären** (OQ-01, OQ-02, OQ-06) im Teamgespräch – Grundlage für den Implementierungsplan.
2. **Implementierungsplan (`plan.md`) erstellen** auf Basis dieses Spec Documents.
3. **Claude Subagents nutzen** zur Code-Generierung auf Basis der FR-Anforderungen.
4. **Review-Agent evaluieren** (OQ-07): Lohnt sich ein eigenständiger Agent zur Spec-Prüfung?
5. **Knackpunkte identifizieren** durch Vibe-Coding: Ist es ein Datenproblem (Stellenanzeigen-Rohdaten), ein Schnittstellenproblem (API-Zugang) oder ein Logikproblem (Matching-Algorithmus)?

---

*Dieses Dokument folgt der GitHub spec-kit Struktur (Spec-Driven Development). Version 0.1 – zur Diskussion in der nächsten Review-Session.*
