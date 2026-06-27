import streamlit as st

from database import DatabaseManager
from study import Study
from log_in import Login
from studienleiter import render_studienleiter
from proband import render_proband

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
st.set_page_config(page_title="EKG-Studienauswertung", layout="wide")

DB_PATH = "data/ekg_study.db"


def init_session_state():
    if "db" not in st.session_state:
        st.session_state.db = DatabaseManager(DB_PATH)

    # Study immer neu laden – sichert frische DB-Daten bei jedem Reload
    study = Study()
    study.load_from_db(st.session_state.db)
    st.session_state.study = study

    if "login" not in st.session_state:
        st.session_state.login = Login(st.session_state.db)

    if "user" not in st.session_state:
        st.session_state.user = None

    if "reg_success" not in st.session_state:
        st.session_state.reg_success = False


init_session_state()
db: DatabaseManager = st.session_state.db
study: Study = st.session_state.study
login: Login = st.session_state.login


# ---------------------------------------------------------------------------
# Sidebar: Logout wenn eingeloggt
# ---------------------------------------------------------------------------

def render_sidebar():
    st.sidebar.image("data/pictures/ekg_logo.svg", use_container_width=True)
    st.sidebar.markdown("---")

    if st.session_state.user is not None:
        user = st.session_state.user
        role_label = "Studienleiter" if user.role == "leiter" else "Proband"
        st.sidebar.success(f"**{user.username}** ({role_label})")
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.session_state.reg_success = False
            st.rerun()


render_sidebar()

# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

if st.session_state.user is not None:
    user = st.session_state.user

    if user.role == "leiter":
        render_studienleiter(study, db)
    elif user.role == "proband":
        render_proband(study, db, user)
    else:
        st.error("Unbekannte Rolle. Bitte neu einloggen.")

else:
    # -----------------------------------------------------------------------
    # Startseite: Login + Registrierung
    # -----------------------------------------------------------------------
    st.image("data/pictures/ekg_logo.svg", width=320)
    st.markdown(
        "<p style='color:#64748b; font-size:16px; margin-top:-8px;'>"
        "Willkommen! Bitte melden Sie sich an oder registrieren Sie sich.</p>",
        unsafe_allow_html=True,
    )

    col_login, col_reg = st.columns(2)

    # --- Login ---
    with col_login:
        st.subheader("Anmelden")
        with st.form("login_form"):
            username = st.text_input("Benutzername")
            password = st.text_input("Passwort", type="password")
            submitted = st.form_submit_button("Einloggen", type="primary")

        if submitted:
            user = login.login(username, password)
            if user is None:
                st.error("Benutzername oder Passwort falsch.")
            elif user.role == "proband" and user.person_id:
                person = db.get_person_by_id(user.person_id)
                if person and person.status == "pending":
                    st.warning(
                        f"Hallo **{person.firstname}**, deine Registrierung wird noch geprüft. "
                        "Sobald die Studienleitung deinen Account freischaltet, kannst du dich einloggen."
                    )
                elif person and person.status == "rejected":
                    st.error(
                        f"Hallo **{person.firstname}**, deine Registrierung wurde leider abgelehnt. "
                        "Bitte wende dich direkt an die Studienleitung für weitere Informationen."
                    )
                else:
                    st.session_state.user = user
                    st.rerun()
            else:
                st.session_state.user = user
                st.rerun()

        if st.session_state.reg_success:
            st.success(
                "Registrierung eingereicht! Die Studienleitung prüft deine Anfrage. "
                "Du kannst dich mit deinen gewählten Zugangsdaten einloggen, "
                "sobald dein Account freigeschalten wurde."
            )

    # --- Registrierung ---
    with col_reg:
        st.subheader("Neu registrieren")
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            firstname = col1.text_input("Vorname *")
            lastname = col2.text_input("Nachname *")

            email = st.text_input("E-Mail-Adresse *")

            col3, col4 = st.columns(2)
            birth_year = col3.number_input(
                "Geburtsjahr *", min_value=1900, max_value=2010, value=1990, step=1
            )
            gender = col4.selectbox(
                "Geschlecht *", ["Männlich", "Weiblich", "Divers"]
            )

            col5, col6 = st.columns(2)
            weight = col5.number_input("Körpergewicht (kg)", min_value=20.0, max_value=300.0, value=70.0, step=0.5)
            fitness_level = col6.selectbox(
                "Sportlicher Zustand", ["aktiv", "gelegentlich", "inaktiv"]
            )

            st.markdown("---")
            col7, col8 = st.columns(2)
            new_username = col7.text_input("Benutzername *")
            new_password = col8.text_input("Passwort *", type="password")

            reg_submitted = st.form_submit_button("Registrierung absenden")

        if reg_submitted:
            errors = []
            if not firstname.strip():
                errors.append("Vorname fehlt.")
            if not lastname.strip():
                errors.append("Nachname fehlt.")
            if not email.strip():
                errors.append("E-Mail fehlt.")
            if not new_username.strip():
                errors.append("Benutzername fehlt.")
            if not new_password.strip():
                errors.append("Passwort fehlt.")

            gender_map = {"Männlich": "Male", "Weiblich": "Female", "Divers": "Divers"}

            if errors:
                for e in errors:
                    st.error(e)
            else:
                person = login.register(
                    firstname=firstname.strip(),
                    lastname=lastname.strip(),
                    date_of_birth=int(birth_year),
                    email=email.strip(),
                    gender=gender_map[gender],
                    weight=float(weight),
                    fitness_level=fitness_level,
                    username=new_username.strip(),
                    password=new_password.strip(),
                )
                if person is None:
                    st.error("Dieser Benutzername ist bereits vergeben. Bitte wählen Sie einen anderen.")
                else:
                    study.load_from_db(db)
                    st.session_state.reg_success = True
                    st.rerun()
