import streamlit as st
import sys
import os
import tempfile
import pandas as pd

# Projektwurzel zum Suchpfad hinzufügen
sys.path.insert(0, os.path.dirname(__file__))

import database
from agents import agent1 as skill_extractor, application_agent, market_agent
from utils import excel_handler

# Fester Nutzer-ID für den MVP
NUTZER_ID = "user_001"

# Datenbank einmal pro Session aufbauen (Streamlit-Cache)
@st.cache_resource
def get_db():
    conn = database.verbinde_db()
    database.erstelle_tabellen(conn)
    return conn


# =====================================================================
# Tab-Funktionen
# =====================================================================

def tab_profil(conn):
    st.header("Mein Profil")

    # Freitext-Eingabe für Skills
    text = st.text_area(
        "Beschreibe deine Erfahrungen und Skills:",
        placeholder="z.B. Ich habe 2 Jahre Python-Erfahrung und kenne Django und PostgreSQL.",
        height=150
    )
    if st.button("Skills extrahieren", type="primary"):
        if not text.strip():
            st.warning("Bitte gib einen Text ein.")
        else:
            with st.spinner("Analysiere mit Ollama..."):
                skills = skill_extractor.extrahiere_skills_aus_text(text)
            if skills.get("hard_skills") or skills.get("soft_skills") or skills.get("tools"):
                skill_extractor.speichere_skills(skills, NUTZER_ID, "freitext", conn)
                st.success("Skills extrahiert und gespeichert!")
                st.json(skills)
            else:
                st.warning("Keine Skills erkannt. Läuft Ollama? (ollama serve)")

    st.divider()

    # PDF-Upload
    pdf_datei = st.file_uploader("PDF hochladen (Lebenslauf, Zertifikat)", type="pdf")
    if pdf_datei:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_datei.read())
            tmp_pfad = tmp.name

        with st.spinner("Lese PDF und extrahiere Skills..."):
            skills = skill_extractor.extrahiere_skills_aus_pdf(tmp_pfad)
        os.unlink(tmp_pfad)

        if skills.get("hard_skills") or skills.get("soft_skills") or skills.get("tools"):
            skill_extractor.speichere_skills(skills, NUTZER_ID, "pdf", conn)
            st.success("Skills aus PDF extrahiert und gespeichert!")
            st.json(skills)
        else:
            st.warning("Kein lesbarer Text im PDF oder Ollama läuft nicht.")

    st.divider()

    # Gespeichertes Profil anzeigen
    profil = skill_extractor.lade_profil(NUTZER_ID, conn)
    if profil:
        st.subheader(f"Gespeicherte Skills ({len(profil)})")
        df = pd.DataFrame(profil)
        df.columns = ["Skill", "Kategorie", "Level (1-5)", "Quelle", "Aktualisiert"]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Noch keine Skills gespeichert.")


def tab_stellen_suchen(conn):
    st.header("Stellen suchen")

    col1, col2 = st.columns(2)
    with col1:
        jobtitel = st.text_input("Jobtitel", "Python Entwickler")
    with col2:
        ort = st.text_input("Ort", "Berlin")

    if st.button("Suchen", type="primary"):
        with st.spinner(f"Suche Stellen für '{jobtitel}' in '{ort}'..."):
            stellen = application_agent.suche_passende_stellen(jobtitel, ort, NUTZER_ID, conn)
        if stellen:
            st.session_state.stellen = stellen
            st.session_state.anschreiben = ""
            st.session_state.senden_bestaetigt = False
        else:
            st.warning("Keine Stellen gefunden. Netzwerk prüfen.")

    # Ergebnisse und Anschreiben-Flow nur anzeigen wenn Suche gelaufen ist
    stellen = st.session_state.get("stellen", [])
    if not stellen:
        return

    st.success(f"{len(stellen)} Stellen gefunden.")

    # Stelle auswählen
    optionen = [f"{s['titel']} – {s['unternehmen']} ({s['match_score']}%)" for s in stellen]
    idx = st.selectbox("Stelle auswählen:", range(len(optionen)), format_func=lambda i: optionen[i])
    stelle = stellen[idx]

    col_info, col_meta = st.columns([3, 1])
    with col_info:
        with st.expander("Stellenbeschreibung anzeigen"):
            st.write(stelle.get("beschreibung") or "–")
    with col_meta:
        st.metric("Match-Score", f"{stelle['match_score']} %")
        if stelle.get("url"):
            st.markdown(f"[Zur Anzeige]({stelle['url']})")

    st.divider()

    # Anschreiben generieren
    if st.button("Anschreiben generieren (Claude API)", type="primary"):
        profil = skill_extractor.lade_profil(NUTZER_ID, conn)
        with st.spinner("Generiere Anschreiben mit Claude..."):
            anschreiben = application_agent.generiere_anschreiben(stelle, profil, NUTZER_ID)
        if anschreiben:
            st.session_state.anschreiben = anschreiben
            st.session_state.anschreiben_stelle = stelle
            st.session_state.senden_bestaetigt = False
        else:
            st.error("Anschreiben konnte nicht generiert werden. ANTHROPIC_API_KEY gesetzt?")

    # Anschreiben anzeigen und Aktionen
    anschreiben = st.session_state.get("anschreiben", "")
    if not anschreiben:
        return

    st.subheader("Generiertes Anschreiben")
    anschreiben_text = st.text_area("Anschreiben (bearbeitbar):", value=anschreiben, height=350, key="anschreiben_inhalt")

    col_save, col_send = st.columns(2)

    with col_save:
        if st.button("Als Entwurf speichern"):
            application_agent.speichere_bewerbung(stelle, stelle.get("match_score", 0), "Entwurf", conn)
            st.success("Als Entwurf gespeichert.")

    with col_send:
        empfaenger = st.text_input("Empfänger-E-Mail:", key="empfaenger_email")
        if st.button("Bewerbung absenden"):
            if not empfaenger:
                st.error("Bitte zuerst eine E-Mail-Adresse eingeben.")
            else:
                st.session_state.senden_bestaetigt = True

        # Zweiter Schritt – explizite Letztbestätigung in der UI
        if st.session_state.get("senden_bestaetigt"):
            st.warning(f"Wirklich an **{empfaenger}** senden? Diese Aktion kann nicht rückgängig gemacht werden.")
            if st.button("Ja, jetzt senden", type="primary"):
                with st.spinner("Sende Bewerbung..."):
                    erfolg = application_agent.sende_bewerbung(
                        stelle, anschreiben_text, empfaenger, bestaetigt=True
                    )
                if erfolg:
                    application_agent.speichere_bewerbung(stelle, stelle.get("match_score", 0), "Versandt", conn)
                    st.success("Bewerbung gesendet und im Tracking gespeichert!")
                    st.session_state.senden_bestaetigt = False
                else:
                    st.error("Versand fehlgeschlagen. SMTP_USER / SMTP_PASSWORT prüfen.")


def tab_bewerbungen(conn):
    st.header("Bewerbungen")

    cursor = conn.cursor()
    cursor.execute("""
        SELECT job_titel, unternehmen, match_score, status, beworben_am, antwort, url
        FROM applications ORDER BY beworben_am DESC
    """)
    zeilen = cursor.fetchall()

    if zeilen:
        spalten = ["Job Titel", "Unternehmen", "Match %", "Status", "Beworben am", "Antwort", "Link"]
        df = pd.DataFrame(zeilen, columns=spalten)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Noch keine Bewerbungen vorhanden.")

    if st.button("Als Excel exportieren"):
        excel_handler.exportiere_bewerbungen(conn, "data/bewerbungen.xlsx")
        st.success("Exportiert nach data/bewerbungen.xlsx")


def tab_marktanalyse(conn):
    st.header("Marktanalyse")

    col1, col2 = st.columns(2)
    with col1:
        jobtitel = st.text_input("Jobtitel für Analyse", "Software Entwickler", key="markt_titel")
    with col2:
        ort = st.text_input("Ort", "Berlin", key="markt_ort")

    if st.button("Marktdaten aktualisieren", type="primary"):
        with st.spinner("Sammle Stellenanzeigen und analysiere Skills..."):
            market_agent.sammle_marktdaten(jobtitel, ort, conn)
        st.success("Marktdaten aktualisiert!")

    trends = market_agent.berechne_trends(conn)
    if not trends:
        st.info("Noch keine Trenddaten. Bitte zuerst Marktdaten aktualisieren.")
        return

    # --- Trendtabelle ---
    st.subheader("Top-10 Skills (letzte 30 Tage)")
    df = pd.DataFrame(trends)
    df = df.rename(columns={
        "skill": "Skill",
        "trend": "Trend",
        "steigung": "Steigung",
        "veraenderung_prozent": "Änderung %",
        "nennungen_aktuell": "Nennungen",
        "fruehindikator": "Frühindikator"
    })
    st.dataframe(df, use_container_width=True)

    # Frühindikator-Warnungen separat hervorheben
    frueh = [t for t in trends if t.get("fruehindikator")]
    for t in frueh:
        st.warning(
            f"Frühindikator: **{t['skill']}** verliert Nachfrage "
            f"({t['veraenderung_prozent']}% in 30 Tagen). Weiterbildung empfohlen."
        )

    st.divider()

    # --- Feedback-Loop: Marktsignal an Skill Tracker ---
    st.subheader("Marktsignal an Skill Tracker senden")
    st.caption("Fügt wachsende Skills als Lernziele ins Profil ein und gibt Warnungen für sinkende Skills aus.")

    if st.button("Marktsignal senden"):
        signal_dict = {
            "wachsende_skills": [t for t in trends if t["trend"] == "wachsend"],
            "sinkende_skills": [t for t in trends if t["trend"] == "sinkend"]
        }
        ergebnis = market_agent.sende_marktsignal_an_skill_extractor(signal_dict, conn)

        if ergebnis["hinzugefuegt"]:
            st.success(f"Als Lernziele ins Profil eingetragen: {', '.join(ergebnis['hinzugefuegt'])}")
        for warnung in ergebnis["warnungen"]:
            st.warning(warnung)
        if not ergebnis["hinzugefuegt"] and not ergebnis["warnungen"]:
            st.info("Keine Änderungen – alle wachsenden Skills sind bereits im Profil.")

    st.divider()

    # --- Skill-Lücken ---
    st.subheader("Skill-Lückenanalyse")
    luecken = market_agent.erkenne_skill_luecken(NUTZER_ID, conn)

    col_fehlt, col_lern = st.columns(2)
    with col_fehlt:
        st.markdown("**Fehlende Skills** (Markt braucht, Profil hat nicht)")
        fehlende = luecken.get("fehlende_skills", [])
        if fehlende:
            st.dataframe(pd.DataFrame(fehlende), use_container_width=True)
        else:
            st.info("Keine Lücken – alle Top-Skills sind im Profil.")

    with col_lern:
        st.markdown("**Lernpotenzial** (vorhanden, aber Level ≤ 2)")
        lernbare = luecken.get("lernbare_skills", [])
        if lernbare:
            st.dataframe(pd.DataFrame(lernbare), use_container_width=True)
        else:
            st.info("Kein Lernpotenzial identifiziert.")


# =====================================================================
# App-Start
# =====================================================================

st.set_page_config(page_title="KI-Bewerbungsagent", layout="wide")
st.title("KI-Bewerbungsagent")
st.caption("Lokal, datenschutzfreundlich, KI-gestützt")

conn = get_db()

tab1, tab2, tab3, tab4 = st.tabs([
    "Mein Profil",
    "Stellen suchen",
    "Bewerbungen",
    "Marktanalyse"
])

with tab1:
    tab_profil(conn)
with tab2:
    tab_stellen_suchen(conn)
with tab3:
    tab_bewerbungen(conn)
with tab4:
    tab_marktanalyse(conn)
