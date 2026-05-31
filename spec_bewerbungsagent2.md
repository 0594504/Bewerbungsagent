# Feature Specification: Bewerbungsagent (Multi-Agent-System)

**Feature Branch:** `001-bewerbungsagent`  
**Erstellt:** 2026-05-29  
**Zuletzt aktualisiert:** 2026-05-31  
**Status:** Draft v0.2  
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

Als Nutzer möchte ich, dass der Agent für mich relevante Stellenanzeigen findet und automatisch eine auf mein Profil zugeschnittene Bewerbung (Anschreiben + angepasster Lebenslauf) erstellt – damit ich weniger Zeit für administrative Aufgaben aufwenden muss.

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
3. **Given** eine Bewerbung ohne Rückmeldung nach 14 Tagen, **When** das System die Frist erkennt, **Then** wird dem Nutzer eine Nachfass-Option vorgeschlagen.

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

- Was passiert, wenn eine hochgeladene Datei keine extrahierbaren Skills enthält (z. B. ein Bild-PDF oder ein gescanntes Dokument ohne OCR)?
- Was passiert bei doppelter Bewerbung auf dieselbe Stelle – überschreiben oder neue Bewerbung anlegen?
- Wie geht das System mit widersprüchlichen Informationen im Skill-Profil um (z. B. gleicher Skill mit unterschiedlichen Erfahrungsstufen aus zwei Quellen)?
- Was passiert, wenn die Bundesagentur-API einen Rate-Limit-Fehler zurückgibt (HTTP 429)?
- Was passiert, wenn die E-Mail-Integration nicht verfügbar ist – stiller Fehler oder explizite Meldung?
- Wie verhält sich das Embedding-Matching, wenn das Skill-Profil noch sehr wenig Einträge hat (Kaltstart-Problem)?

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
- Abruf von Stellenanzeigen über die Bundesagentur für Arbeit REST API (`rest.arbeitsagentur.de`)
- Berechnung eines semantischen Matching-Scores via Embedding-Vergleich zwischen Skill-Profil und Stellenprofil
- Generierung individualisierter Anschreiben per LLM (Claude API)
- Verwaltung des Bewerbungs-Trackings (Status, Zeitstempel, Kontakte)
- Export von Bewerbungsunterlagen als PDF und DOCX
- Optional: automatisches Absenden per E-Mail (nach expliziter Nutzerfreigabe)

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
- **FR-002:** Der Skill Tracker MUSS Skills aus folgenden Dokumenttypen automatisch extrahieren: PDF-Dateien mit lesbarem Text (Hausarbeiten, Projektberichte, Zeugnisse) und Freitext-Eingaben (Tätigkeitsbeschreibungen, Werkstudentenjobs). Bild-PDFs ohne OCR-Schicht sind für den MVP explizit ausgeschlossen.
- **FR-003:** Der Bewerbungsagent MUSS Stellenanzeigen über die öffentliche Bundesagentur für Arbeit REST API abrufen können (`https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs`). Kein API-Key oder Registrierung erforderlich.
- **FR-004:** Das System MUSS einen semantischen Matching-Score (0–100%) zwischen Skill-Profil und Stellenanzeige berechnen, basierend auf Embedding-Vergleich (Cosine Similarity via Claude Embeddings API). Keyword-Matching allein ist nicht ausreichend.
- **FR-005:** Der Bewerbungsagent MUSS per Claude API ein individuelles Anschreiben generieren können, das konkrete Skill-Übereinstimmungen zwischen Profil und Stelle hervorhebt.
- **FR-006:** Das System MUSS alle Bewerbungen mit Status (Entwurf / Versandt / Einladung / Absage) und Zeitstempel nachverfolgen.
- **FR-007:** Das System MUSS den Nutzer vor dem automatischen Absenden einer Bewerbung um eine explizite Bestätigung bitten (kein automatisches Versenden ohne Nutzerinteraktion).
- **FR-008:** Der Marktbeobachter MUSS mindestens einmal täglich eine Marktanalyse auf Basis neuer Stellenanzeigen der Bundesagentur für Arbeit durchführen.
- **FR-009:** Das System MUSS Frühindikatoren für sinkende Skill-Nachfrage erkennen (relativer Rückgang >20% über 30 Tage) und den Nutzer mit einer Benachrichtigung plus Weiterbildungsempfehlung informieren.
- **FR-010:** Der Skill Tracker MUSS Marktsignale vom Marktbeobachter empfangen und die Relevanz-Gewichtung von Skills im Profil entsprechend anpassen.
- **FR-011:** Das System MUSS eine regionale Konfiguration unterstützen; Standard für den MVP ist Berlin & Brandenburg (entsprechend den Filterparametern der Bundesagentur-API).
- **FR-012:** Das System MUSS fertige Bewerbungsunterlagen (Anschreiben + Lebenslauf) in beiden Formaten exportieren können: DOCX (bearbeitbar) und PDF (versandfertig).
- **FR-013:** Alle Nutzerdaten (Skill-Profil, Bewerbungen, Marktberichte) MÜSSEN lokal auf dem Gerät des Nutzers gespeichert werden. Keine Cloud-Synchronisation. Datenhaltung erfolgt in einer SQLite-Datenbank.
- **FR-014:** Die Agenten MÜSSEN untereinander über definierte Schnittstellen kommunizieren; kein direkter Datenbankzugriff zwischen Agenten. Datenaustausch erfolgt als strukturierte Python-Objekte (Pydantic-Modelle) innerhalb des CrewAI-Frameworks.

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

### Stack & Architektur – Entscheidungen (final)

| Komponente | Entscheidung | Begründung |
|---|---|---|
| **Sprache** | Python 3.11+ | Standard für KI/ML, beste Bibliotheksunterstützung |
| **Agenten-Framework** | **CrewAI** | Einsteigerfreundlichstes Framework; role-basiertes Design passt exakt zu den 3 Agenten; schnellster Weg zum lauffähigen MVP |
| **LLM** | Claude (Anthropic API) | Anschreiben-Generierung, Skill-Extraktion, Embeddings |
| **Datenbank** | **SQLite** (lokale Datei) | Keine Installation, keine Konfiguration; eine Datei auf dem Rechner des Nutzers; ausreichend für MVP |
| **Agenten-Kommunikation** | **Direkte Python-Objektübergabe via Pydantic-Modelle** | CrewAI hat das eingebaut; kein Message-Broker nötig; kein Overhead |
| **Matching-Algorithmus** | **Semantisches Embedding-Matching** (Cosine Similarity) | Erkennt inhaltliche Übereinstimmungen auch ohne exakte Keyword-Treffer (z. B. „Pandas" → „Datenanalyse") |
| **Frontend – Phase 1 (MVP)** | **CLI-Interface** | Logik steht vor UI; einfachstes Debugging; sofortig lauffähig |
| **Frontend – Phase 2** | Web-UI (FastAPI + einfaches HTML/JS) | Erweiterung nach funktionierender CLI-Version |
| **Testing** | pytest | Standard |
| **Export-Formate** | DOCX (python-docx) + PDF (Konvertierung aus DOCX) | Beide Formate laut Anforderung |

### Externe Schnittstellen

| Schnittstelle | Zweck | Status | Details |
|---|---|---|---|
| Bundesagentur für Arbeit REST API | Abruf von Stellenanzeigen (Berlin & Brandenburg) | ✅ Kostenlos, kein API-Key nötig | `GET rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs` mit Header `X-API-Key: jobboerse-jobsuche` |
| Anthropic Claude API | Textgenerierung (Anschreiben), Skill-Extraktion, Embeddings | ✅ API-Key vorhanden | Modell: claude-sonnet-4-6 |
| PyMuPDF / pdfminer | PDF-Text-Extraktion | ✅ Bibliothek verfügbar | Nur für text-basierte PDFs; kein OCR |
| SMTP / Gmail API | Automatisches Versenden von Bewerbungen | 🔲 Noch nicht implementiert (P2) | Optional; nur nach expliziter Nutzerbestätigung |

### Kommunikationsschema zwischen Agenten

```
Nutzer (CLI-Input)
       │
       ▼
 ┌─────────────────┐        Skill-Profil (Pydantic)        ┌──────────────────┐
 │  Bewerbungsagent│◄──────────────────────────────────────│   Skill Tracker  │
 │  (CrewAI Agent) │                                        │  (CrewAI Agent)  │
 └────────┬────────┘                                        └────────▲─────────┘
          │                                                          │
          │ Suche-Auftrag                              Marktsignale  │
          │ (Ort, Jobtitel)                            (JSON)        │
          ▼                                                          │
 ┌─────────────────┐                                                 │
 │  Marktbeobachter│─────────────────────────────────────────────────┘
 │  (CrewAI Agent) │
 └─────────────────┘
          │
          ▼
  Bundesagentur API
  (rest.arbeitsagentur.de)
```

---

## Offene Fragen

| # | Frage | Status | Entscheidung / Nächster Schritt |
|---|---|---|---|
| OQ-01 | Welches Agenten-Framework wird eingesetzt? | ✅ Geklärt | **CrewAI** – einsteigerfreundlichstes Framework, am besten geeignet für role-basierte Multi-Agenten-Architektur |
| OQ-02 | Welche Stellenbörsen-APIs sind zugänglich? | ✅ Geklärt | **Bundesagentur für Arbeit REST API** – kostenlos, kein API-Key, über 1 Mio. Stellen, perfekt für Deutschland/Berlin |
| OQ-03 | Datenspeicherung – lokal oder Cloud? DSGVO? | ✅ Geklärt | **Lokal, SQLite.** Keine DSGVO-Anforderungen im Uni-Kontext. Nur Team-interne Nutzung. |
| OQ-04 | CLI oder Web-UI? | ✅ Geklärt | **Phase 1: CLI** (Logik zuerst). **Phase 2: Web-UI** mit FastAPI + HTML/JS nach funktionierendem MVP. |
| OQ-05 | Export-Format für Bewerbungsunterlagen? | ✅ Geklärt | **Beide Formate:** DOCX (python-docx, bearbeitbar) + PDF (Konvertierung aus DOCX) |
| OQ-06 | Granularität des Skill-Matchings? | ✅ Geklärt | **Semantisches Embedding-Matching** (Cosine Similarity via Claude Embeddings API) – versteht inhaltliche Ähnlichkeiten statt nur exakter Keyword-Treffer |
| OQ-07 | Soll ein Review-Agent die Specs/Code prüfen? | 🔲 Offen | Evaluierung nach erstem lauffähigen MVP |
| OQ-08 | Demonstrationsform für Professor-Review? | 🔲 Offen | Logs, CLI-Demo oder Jupyter Notebook – Entscheidung im Team |
| OQ-09 | Schwellenwert für Frühindikator-Logik? | ✅ Entschieden | **Relativer Rückgang >20% über 30 Tage** gilt als Frühindikator für sinkende Nachfrage |
| OQ-10 | Abgleich mit Reiseplanungs-Agenten-Team? | 🔲 Offen | Gemeinsame Architektur-Patterns (CrewAI, SQLite) sichern; Abstimmung im nächsten Team-Meeting |

---

## Assumptions

- Nutzer haben Zugang zu einem Anthropic Claude API-Key für LLM-Funktionalität (Textgenerierung + Embeddings).
- Der MVP wird auf einem lokalen Entwicklungsrechner betrieben; kein Cloud-Deployment.
- Als Agenten-Framework wird CrewAI eingesetzt; alle Agenten laufen im selben Python-Prozess.
- Die Bundesagentur für Arbeit REST API bleibt während der Projektlaufzeit kostenlos und ohne Authentifizierung zugänglich.
- Nur text-basierte PDFs werden verarbeitet; gescannte Dokumente ohne OCR sind im MVP ausgeschlossen.
- Automatisches E-Mail-Absenden ist für den MVP optional und wird nur demonstriert, nicht produktiv genutzt.
- Alle Nutzerdaten werden lokal in einer SQLite-Datei gespeichert; keine externen Server.
- Für die Review-Session beim Professor wird mit synthetischen oder selbst erstellten Testdaten demonstriert.
- Das andere Teilteam (Reiseplanungs-Agent) verwendet ebenfalls CrewAI und SQLite – Abgleich steht aus.

---

## Nächste Schritte

1. **Spec mit Team besprechen** – dieses Dokument als Basis für die nächste Teamdiskussion nutzen; verbleibende offene Fragen (OQ-07, OQ-08, OQ-10) klären.
2. **Implementierungsplan (`plan.md`) erstellen** – auf Basis der geklärten FRs und der Tech-Stack-Entscheidungen.
3. **CrewAI-Setup aufsetzen** – Projektstruktur anlegen, drei Agenten als CrewAI-Rollen definieren, Anthropic API einbinden.
4. **Bundesagentur-API testen** – ersten API-Call gegen `rest.arbeitsagentur.de` mit Filter auf Berlin ausführen; Datenqualität prüfen.
5. **Embedding-Matching prototypen** – Skill-Profil (JSON) und Stellenanzeige (Text) gegen Claude Embeddings API laufen lassen; ersten Cosine-Similarity-Score berechnen.
6. **Knackpunkte identifizieren** durch Vibe-Coding: Ist es ein **Datenproblem** (Qualität der Stellenanzeigen-Rohdaten), ein **Schnittstellenproblem** (API-Verfügbarkeit, Rate Limits) oder ein **Logikproblem** (Matching-Genauigkeit, Skill-Extraktion)?
7. **Review-Agent evaluieren** (OQ-07) – nach erstem lauffähigen MVP entscheiden.

---

*Dieses Dokument folgt der GitHub spec-kit Struktur (Spec-Driven Development). Version 0.2 – alle technischen Grundentscheidungen getroffen, bereit zur Teamdiskussion.*
