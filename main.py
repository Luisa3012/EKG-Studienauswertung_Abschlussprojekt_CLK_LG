import json
import streamlit as st
import pandas as pd

from study import Study
from log_in import Login
from person import Person


# ---------------------------------------------------------------------------
# Grundkonfiguration
# --------------------------------------------------------------------------
st.set_page_config(page_title="EKG-Studienauswertung", layout="wide")
st.title("EKG-Studienauswertung")
st.write("Willkommen zur EKG-Studienauswertung! Bitte melden Sie sich an, um fortzufahren.")



DB_PATH = "data/person_db.json"


def init_session_state():
    """Sorgt dafür, dass Study/Login/User über Re-Runs hinweg erhalten bleiben."""
    if "study" not in st.session_state:
        study = Study()
        study.load_from_json(DB_PATH)
        st.session_state.study = study

    if "login" not in st.session_state:
        st.session_state.login = Login()

    if "user" not in st.session_state:
        st.session_state.user = None  # eingeloggter User (oder None)


init_session_state()
study: Study = st.session_state.study
login: Login = st.session_state.login


# ---------------------------------------------------------------------------
# Sidebar: Login / Logout
# ---------------------------------------------------------------------------

def render_sidebar():
    st.sidebar.title("EKG-Studienauswertung")

    if st.session_state.user is None:
        st.sidebar.subheader("Login")
        username = st.sidebar.text_input("Benutzername")
        password = st.sidebar.text_input("Passwort", type="password")

        if st.sidebar.button("Einloggen"):
            user = login.login(username, password)
            if user is None:
                st.sidebar.error("Login fehlgeschlagen. Bitte Benutzername/Passwort prüfen.")
            else:
                st.session_state.user = user
                st.rerun()

        st.sidebar.divider()
        st.sidebar.caption("Noch kein Account? Siehe Tab 'Registrierung' weiter unten.")

    else:
        user = st.session_state.user
        st.sidebar.success(f"Eingeloggt als: {user.username} ({user.role})")
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.rerun()


# ---------------------------------------------------------------------------
# Studienleiter-Ansicht
# ---------------------------------------------------------------------------

def tab_uebersicht():
    st.header("Übersicht")

    col1, col2, col3 = st.columns(3)
    col1.metric("Probanden gesamt", study.get_total_persons())
    col2.metric("Tests gesamt", study.get_total_tests())

    avg_hr_all = study.get_average_hr_all_tests()
    col3.metric("Ø HR (alle Tests)", f"{avg_hr_all:.1f}" if avg_hr_all is not None else "–")

    st.subheader("Alle Probanden")
    rows = []
    for p in study.get_all_persons():
        rows.append({
            "ID": p.id,
            "Name": p.get_full_name(),
            "Alter": p.calc_age(),
            "Geschlecht": p.gender,
            "Status": p.status,
            "Anzahl Tests": len(study.get_tests_by_person(p.id))
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Noch keine Probanden vorhanden.")


def tab_registrierungen_verwalten():
    st.header("Neue Registrierungen verwalten")

    pending = study.get_pending_persons()

    if not pending:
        st.info("Aktuell keine offenen Registrierungen.")
        return

    for p in pending:
        with st.container(border=True):
            col_img, col_info, col_actions = st.columns([1, 3, 2])

            with col_img:
                try:
                    st.image(p.get_image(), width=120)
                except Exception:
                    st.write("(Kein Foto)")

            with col_info:
                st.markdown(f"*{p.get_full_name()}*")


render_sidebar()
tab_uebersicht()
