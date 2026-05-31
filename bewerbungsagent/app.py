import streamlit as st
import json
import os
import importlib.util
import sys
import tempfile
import pandas as pd

# Agenten per importlib laden (wegen numerischen Dateinamen)
def _lade_modul(name, pfad):
    spec = importlib.util.spec_from_file_location(name, pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul

AGENTS_ORDNER = os.path.join(os.path.dirname(__file__), "agents")

skill_extractor = _lade_modul("skill_extractor", os.path.join(AGENTS_ORDNER, "02_skill_extractor.py"))
application_agent = _lade_modul("application_agent", os.path.join(AGENTS_ORDNER, "03_application_agent.py"))
market_agent = _lade_modul("market_agent", os.path.join(AGENTS_ORDNER, "04_market_agent.py"))

# Pfad zum Profil
PROFIL_PFAD = os.path.join(os.path.dirname(__file__), "data", "profil.json")


def lade_profil():
    """Lädt das Benutzerprofil oder gibt None zurück."""
    if not os.path.exists(PROFIL_PFAD):
        return None
    with open(PROFIL_PFAD, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Seiteneinstellungen ---
st.set_page_config(
    page_title="KI-Bewerbungsagent",
    page_icon="💼",
    layout="wide"
)

st.title("KI-Bewerbungsagent")
st.caption("Dein lokaler, datenschutzfreundlicher Bewerbungsassistent")

# --- Navigation mit Tabs ---
tab_profil, tab_text, tab_pdf, tab_jobs, tab_trends = st.tabs([
    "Mein Profil",
    "Skills eingeben",
    "PDF hochladen",
    "Jobs suchen",
    "Markttrends"
])


# =====================================================================
# TAB 1: Mein Profil
# =====================================================================
with tab_profil:
    st.header("Mein Skill-Profil")

    profil = lade_profil()

    if profil is None:
        st.info("Noch kein Profil vorhanden. Gib deine Skills unter 'Skills eingeben' ein oder lade eine PDF hoch.")
    else:
        # Metadaten anzeigen
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Anzahl Skills", len(profil["skills"]))
        with col2:
            st.metric("Letztes Update", profil.get("letztes_update", "–"))

        # Skills als Tabelle
        if profil["skills"]:
            skills_df = pd.DataFrame(profil["skills"])
            # Spalten umbenennen für bessere Lesbarkeit
            skills_df = skills_df.rename(columns={
                "name": "Skill",
                "kategorie": "Kategorie",
                "level": "Level (1-5)",
                "quelle": "Quelle",
                "zuletzt_aktualisiert": "Aktualisiert"
            })
            st.dataframe(skills_df, use_container_width=True)

        # Rohdaten optional anzeigen
        with st.expander("Rohdaten (JSON)"):
            st.json(profil)


# =====================================================================
# TAB 2: Skills aus Text eingeben
# =====================================================================
with tab_text:
    st.header("Skills aus Text extrahieren")
    st.write("Beschreibe was du gemacht hast — der Agent erkennt deine Skills automatisch.")

    beispiel = "Beispiel: Ich habe eine REST API mit FastAPI und PostgreSQL entwickelt und das Team bei der Einführung von Docker-Containern unterstützt."
    text_eingabe = st.text_area("Beschreibe deine Erfahrungen:", placeholder=beispiel, height=200)

    if st.button("Skills extrahieren", type="primary"):
        if not text_eingabe.strip():
            st.warning("Bitte gib einen Text ein.")
        else:
            with st.spinner("Analysiere Text mit KI..."):
                skills = skill_extractor.extract_from_text(text_eingabe)

            if skills:
                st.success("Skills erfolgreich extrahiert!")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**Hard Skills**")
                    for s in skills.get("hard_skills", []):
                        st.write(f"• {s}")
                with col2:
                    st.write("**Soft Skills**")
                    for s in skills.get("soft_skills", []):
                        st.write(f"• {s}")
                with col3:
                    st.write("**Tools**")
                    for s in skills.get("tools", []):
                        st.write(f"• {s}")
                st.info("Profil wurde aktualisiert.")
            else:
                st.error("Konnte keine Skills extrahieren. Läuft Ollama?")


# =====================================================================
# TAB 3: PDF hochladen
# =====================================================================
with tab_pdf:
    st.header("Skills aus PDF extrahieren")
    st.write("Lade deinen Lebenslauf oder ein Zertifikat hoch.")

    hochgeladene_datei = st.file_uploader("PDF-Datei auswählen", type=["pdf"])

    if hochgeladene_datei and st.button("PDF analysieren", type="primary"):
        with st.spinner("Lese PDF und extrahiere Skills..."):
            # Temporäre Datei erstellen
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(hochgeladene_datei.read())
                tmp_pfad = tmp.name

            skills = skill_extractor.extract_from_pdf(tmp_pfad)
            os.unlink(tmp_pfad)  # Temporäre Datei löschen

        if skills:
            st.success("Skills aus PDF extrahiert!")
            st.json(skills)
            st.info("Profil wurde aktualisiert.")
        else:
            st.error("Konnte keine Skills aus der PDF lesen.")


# =====================================================================
# TAB 4: Jobs suchen
# =====================================================================
with tab_jobs:
    st.header("Jobs suchen & matchen")

    col1, col2 = st.columns(2)
    with col1:
        jobtitel = st.text_input("Jobtitel", placeholder="z.B. Python Entwickler")
    with col2:
        ort = st.text_input("Ort", placeholder="z.B. Berlin")

    if st.button("Jobs suchen", type="primary"):
        if not jobtitel.strip():
            st.warning("Bitte gib einen Jobtitel ein.")
        else:
            with st.spinner(f"Suche Jobs für '{jobtitel}'..."):
                jobs = application_agent.find_jobs(jobtitel, ort or "Deutschland")

            if not jobs:
                st.warning("Keine Jobs gefunden. Prüfe deine Internetverbindung.")
            else:
                st.success(f"{len(jobs)} Jobs gefunden!")

                # Für jeden Job Match-Score berechnen
                for job in jobs:
                    with st.expander(f"{job['titel']} — {job['unternehmen']} ({job['ort']})"):
                        col_info, col_match = st.columns([3, 1])

                        with col_info:
                            st.write(job.get("beschreibung", ""))
                            if job.get("url"):
                                st.markdown(f"[Zur Stellenanzeige]({job['url']})")

                        with col_match:
                            with st.spinner("Berechne Match..."):
                                match = application_agent.match_profile(job)

                            if match:
                                score = match.get("match_score", 0)
                                # Farbe je nach Score
                                farbe = "green" if score >= 70 else "orange" if score >= 40 else "red"
                                st.markdown(f"**Match: :{farbe}[{score}%]**")

                                if match.get("fehlende_skills"):
                                    st.write("**Fehlende Skills:**")
                                    for s in match["fehlende_skills"][:5]:
                                        st.write(f"• {s}")


# =====================================================================
# TAB 5: Markttrends
# =====================================================================
with tab_trends:
    st.header("Skill-Markttrends")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Marktdaten aktualisieren"):
            with st.spinner("Scrape Stellenanzeigen (dauert ca. 1-2 Minuten)..."):
                anzahl = market_agent.scrape_jobs("Software Entwickler", "Deutschland", anzahl=50)
                market_agent.aktualisiere_skill_trends()
            st.success(f"{anzahl} neue Stellenanzeigen gespeichert.")

    with col2:
        if st.button("Trends analysieren"):
            with st.spinner("Analysiere Trends..."):
                signale = market_agent.analyze_trends()

            if signale:
                # Tabelle der Top-Trends anzeigen
                df = pd.DataFrame(signale)
                df = df.rename(columns={
                    "skill": "Skill",
                    "trend": "Trend",
                    "signal_staerke": "Signal-Stärke",
                    "durchschnitt_nennungen": "Ø Nennungen/Tag"
                })
                st.dataframe(df.head(20), use_container_width=True)

    # Balkendiagramm der häufigsten Skills
    st.subheader("Top Skills der letzten 7 Tage")
    trend_daten = market_agent.hole_trend_daten_fuer_chart()

    if trend_daten.empty:
        st.info("Noch keine Marktdaten. Klicke auf 'Marktdaten aktualisieren'.")
    else:
        trend_daten = trend_daten.set_index("skill_name")
        st.bar_chart(trend_daten["gesamt"])