import streamlit as st
import pandas as pd


@st.cache_data(show_spinner=False)
def _load_ekg_cached(result_link: str, test_id: int):
    """Cached: EKG-Datei einmalig laden und als DataFrame zurückgeben."""
    from ekgdata import EKGdata
    try:
        return EKGdata({"id": test_id, "date": "", "result_link": result_link})
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def _anomalie_count(result_link: str, date_of_birth: int, gender: str) -> int:
    """Cached: Anomalien für eine EKG-Datei + Personenprofil zählen.

    Wird nur beim ersten Aufruf berechnet; danach aus dem Cache gelesen.
    Cache wird automatisch invalidiert wenn sich result_link, Geburtsjahr
    oder Geschlecht ändern.
    """
    from ekgdata import EKGdata
    from person import Person
    try:
        ekg = EKGdata({"id": 0, "date": "", "result_link": result_link})
        if ekg.df is None:
            return 0
        p = Person(0, date_of_birth, "", "", "", gender or "Divers", "", "approved")
        return len(ekg.detect_anomalies(p))
    except Exception:
        return 0


def render_studienleiter(study, db):
    st.title("Studienleiter-Portal")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Übersicht",
        "Registrierungen",
        "Probandenverwaltung",
        "Testverwaltung",
        "Analyse",
        "Verwaltung",
    ])

    with tab1:
        _tab_uebersicht(study, db)
    with tab2:
        _tab_registrierungen(study, db)
    with tab3:
        _tab_probandenverwaltung(study, db)
    with tab4:
        _tab_testverwaltung(study, db)
    with tab5:
        _tab_analyse(study, db)
    with tab6:
        _tab_verwaltung(study, db)


# ----------------------------------------------------------------- Tab 1

def _tab_uebersicht(study, db):
    st.header("Übersicht")

    col1, col2, col3 = st.columns(3)
    col1.metric("Probanden gesamt", db.get_total_persons())
    col2.metric("Tests gesamt", db.get_total_tests())
    avg_hr = db.get_average_hr_all_tests()
    col3.metric("Ø Herzfrequenz (alle Tests)", f"{avg_hr:.1f} bpm" if avg_hr else "–")

    st.subheader("Alle Probanden")
    rows = []
    for p in study.get_all_persons():
        tests = study.get_tests_by_person(p.id)
        anomalie_count = sum(
            _anomalie_count(t.result_link, p.date_of_birth, p.gender)
            for t in tests if t.result_link
        )
        rows.append({
            "ID": p.id,
            "Name": p.get_full_name(),
            "Alter": p.calc_age(),
            "Geschlecht": p.gender or "–",
            "Status": p.status,
            "Tests": len(tests),
            "Anomalien": f"⚠️ {anomalie_count}" if anomalie_count else "✅ Keine",
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Noch keine Probanden vorhanden.")


# ----------------------------------------------------------------- Tab 2

def _tab_registrierungen(study, db):
    st.header("Neue Registrierungen verwalten")

    pending = db.get_pending_persons()
    if not pending:
        st.info("Aktuell keine offenen Registrierungsanfragen.")
        return

    for p in pending:
        with st.container(border=True):
            col_img, col_info, col_act = st.columns([1, 3, 2])

            with col_img:
                try:
                    st.image(p.get_image(), width=100)
                except Exception:
                    st.write("(Kein Foto)")

            with col_info:
                st.markdown(f"**{p.get_full_name()}**")
                st.write(f"Geburtsjahr: {p.date_of_birth}  |  Alter: {p.calc_age()}")
                st.write(f"Geschlecht: {p.gender or '–'}  |  E-Mail: {p.email or '–'}")
                if p.weight:
                    st.write(f"Gewicht: {p.weight} kg  |  Fitnesslevel: {p.fitness_level or '–'}")

            with col_act:
                if st.button("Annehmen", key=f"approve_{p.id}", type="primary"):
                    db.approve_person(p.id)
                    study.load_from_db(db)
                    st.success(
                        f"**{p.get_full_name()}** wurde angenommen und kann sich ab sofort "
                        f"mit den bei der Registrierung gewählten Zugangsdaten einloggen."
                    )
                    st.rerun()

                if st.button("Ablehnen", key=f"reject_{p.id}"):
                    db.reject_person(p.id)
                    st.warning(f"{p.get_full_name()} abgelehnt.")
                    study.load_from_db(db)
                    st.rerun()


# ----------------------------------------------------------------- Tab 3

def _tab_probandenverwaltung(study, db):
    """Tab zur Anzeige und Bearbeitung aller Probanden-Attribute inkl. Bild."""
    st.header("Probandenverwaltung")

    # ── Neuen Probanden manuell anlegen ───────────────────────────────────
    with st.expander("Neuen Probanden manuell anlegen", icon="➕"):
        st.caption(
            "Hier kannst du einen Probanden direkt anlegen (ohne Registrierungsanfrage). "
            "Der Account ist sofort aktiv."
        )
        with st.form("add_proband_form"):
            col_a, col_b = st.columns(2)
            add_first  = col_a.text_input("Vorname *")
            add_last   = col_b.text_input("Nachname *")

            add_email  = st.text_input("E-Mail-Adresse *")

            col_c, col_d = st.columns(2)
            add_dob    = col_c.number_input("Geburtsjahr *", min_value=1900, max_value=2015, value=1990, step=1)
            add_gender = col_d.selectbox("Geschlecht *", ["Male", "Female", "Divers"])

            col_e, col_f = st.columns(2)
            add_weight  = col_e.number_input("Körpergewicht (kg)", min_value=20.0, max_value=300.0, value=70.0, step=0.5)
            add_fitness = col_f.selectbox("Sportlicher Zustand", ["aktiv", "gelegentlich", "inaktiv"])

            st.markdown("**Login-Daten für den Probanden**")
            col_g, col_h = st.columns(2)
            add_username = col_g.text_input("Benutzername *")
            add_password = col_h.text_input("Passwort *", type="password")

            add_submitted = st.form_submit_button("Probanden anlegen", type="primary")

        if add_submitted:
            errors = []
            if not add_first.strip():   errors.append("Vorname fehlt.")
            if not add_last.strip():    errors.append("Nachname fehlt.")
            if not add_email.strip():   errors.append("E-Mail fehlt.")
            if not add_username.strip(): errors.append("Benutzername fehlt.")
            if not add_password.strip(): errors.append("Passwort fehlt.")
            if db.username_exists(add_username.strip()):
                errors.append(f"Benutzername '{add_username.strip()}' ist bereits vergeben.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                new_pid = db.add_person(
                    firstname=add_first.strip(),
                    lastname=add_last.strip(),
                    date_of_birth=int(add_dob),
                    email=add_email.strip(),
                    gender=add_gender,
                    weight=float(add_weight),
                    fitness_level=add_fitness,
                    status="approved",
                )
                db.add_user(add_username.strip(), add_password.strip(), "proband", new_pid)
                study.load_from_db(db)
                st.success(
                    f"Proband **{add_first.strip()} {add_last.strip()}** angelegt. "
                    f"Login: `{add_username.strip()}` / `{add_password.strip()}`"
                )
                st.rerun()

    st.divider()

    persons = study.get_all_persons()
    if not persons:
        st.info("Keine Probanden vorhanden.")
        return

    col_f1, col_f2 = st.columns(2)
    show_pending  = col_f1.toggle("Ausstehende anzeigen", value=False)
    show_rejected = col_f2.toggle("Abgelehnte anzeigen",  value=False)

    visible = [
        p for p in persons
        if p.status == "approved"
        or (show_pending  and p.status == "pending")
        or (show_rejected and p.status == "rejected")
    ]
    if not visible:
        st.info("Keine Probanden gefunden.")
        return

    namen = {p.id: f"{p.get_full_name()}  [{p.status}]" for p in visible}
    selected_id = st.selectbox(
        "Proband auswählen",
        options=list(namen.keys()),
        format_func=lambda x: namen[x],
    )

    person = db.get_person_by_id(selected_id)
    if person is None:
        return

    # --- Profilbild-Vorschau ---
    col_img, col_info = st.columns([1, 3])
    with col_img:
        try:
            st.image(person.get_image(), width=130)
        except Exception:
            st.caption("(Kein Foto)")
    with col_info:
        st.markdown(f"### {person.get_full_name()}")
        st.write(f"**Status:** {person.status}  |  **Max HR:** {person.calc_max_heart_rate():.0f} bpm")

    st.divider()
    st.subheader("Nachname bearbeiten")
    st.caption("Als Studienleiter kannst du nur den Nachnamen des Probanden ändern (z.B. nach Heirat).")

    with st.form("edit_person_form"):
        new_last = st.text_input("Nachname", value=person.lastname or "")
        submitted = st.form_submit_button("Nachname speichern", type="primary")

    if submitted:
        db.update_person(
            person_id=selected_id,
            firstname=person.firstname,
            lastname=new_last.strip(),
            date_of_birth=person.date_of_birth,
            email=person.email,
            gender=person.gender,
            weight=person.weight,
            fitness_level=person.fitness_level,
        )
        study.load_from_db(db)
        st.success("Nachname gespeichert.")
        st.rerun()

    # ── Proband löschen ────────────────────────────────────────────────────
    st.divider()
    with st.expander("Proband löschen", icon="🗑️"):
        st.warning(
            f"**{person.get_full_name()}** und alle zugehörigen Tests und Login-Daten "
            "werden unwiderruflich gelöscht."
        )
        confirm_key = f"confirm_delete_person_{selected_id}"
        if st.session_state.get(confirm_key):
            col_yes, col_no = st.columns(2)
            if col_yes.button("Ja, endgültig löschen", type="primary", key=f"del_yes_{selected_id}"):
                db.delete_person(selected_id)
                study.load_from_db(db)
                st.session_state.pop(confirm_key, None)
                st.success("Proband gelöscht.")
                st.rerun()
            if col_no.button("Abbrechen", key=f"del_no_{selected_id}"):
                st.session_state.pop(confirm_key, None)
                st.rerun()
        else:
            if st.button("Proband löschen", key=f"del_person_{selected_id}"):
                st.session_state[confirm_key] = True
                st.rerun()


# ----------------------------------------------------------------- Tab 4

def _tab_testverwaltung(study, db):
    st.header("Testverwaltung")

    approved = [p for p in study.get_all_persons() if p.status == "approved"]
    if not approved:
        st.info("Keine aktiven Probanden vorhanden.")
        return

    namen = {p.id: p.get_full_name() for p in approved}
    selected_id = st.selectbox(
        "Proband auswählen",
        options=list(namen.keys()),
        format_func=lambda x: namen[x],
        key="tv_person",
    )

    st.subheader("Neuen Test hinzufügen")
    date_input = st.text_input("Datum (TT.MM.JJJJ)", placeholder="z.B. 15.06.2025")
    uploaded = st.file_uploader(
        "EKG-Datei hochladen (.txt, .csv, .tsv)",
        type=["txt", "csv", "tsv"],
    )
    if st.button("Test speichern", type="primary"):
        if not date_input.strip():
            st.error("Bitte ein Datum eingeben.")
        elif uploaded is None:
            st.error("Bitte eine EKG-Datei hochladen.")
        else:
            study.add_test_with_file_upload(db, selected_id, date_input.strip(), uploaded)
            study.load_from_db(db)
            st.success("Test erfolgreich hinzugefügt.")
            st.rerun()

    st.divider()
    st.subheader("Vorhandene Tests")
    tests = study.get_tests_by_person(selected_id)
    if tests:
        for t in tests:
            with st.container(border=True):
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    st.markdown(f"**Test {t.test_id}** — {t.date}")
                    st.caption(f"Datei: {t.result_link}")
                with col_del:
                    confirm_key = f"confirm_del_test_{t.test_id}"
                    if st.session_state.get(confirm_key):
                        if st.button("Löschen bestätigen", key=f"del_test_yes_{t.test_id}", type="primary"):
                            db.delete_test(t.test_id)
                            study.load_from_db(db)
                            st.session_state.pop(confirm_key, None)
                            st.rerun()
                        if st.button("Abbrechen", key=f"del_test_no_{t.test_id}"):
                            st.session_state.pop(confirm_key, None)
                            st.rerun()
                    else:
                        if st.button("🗑️", key=f"del_test_{t.test_id}", help="Test löschen"):
                            st.session_state[confirm_key] = True
                            st.rerun()
    else:
        st.info("Noch keine Tests vorhanden.")


# ----------------------------------------------------------------- Tab 5

def _tab_analyse(study, db):
    """Interaktive EKG-Auswertung mit Zeitbereich-Slider und Testvergleich."""
    st.header("EKG-Analyse")

    persons = study.get_all_persons()
    if not persons:
        st.info("Keine Probanden vorhanden.")
        return

    # ── Auswahl ────────────────────────────────────────────────────────────
    with st.container(border=True):
        col_p, col_t = st.columns(2)
        namen = {p.id: p.get_full_name() for p in persons}
        selected_pid = col_p.selectbox(
            "Proband auswählen",
            options=list(namen.keys()),
            format_func=lambda x: namen[x],
            key="ana_person",
        )
        person = db.get_person_by_id(selected_pid)
        tests = study.get_tests_by_person(selected_pid)

        if not tests:
            st.info("Dieser Proband hat noch keine Tests.")
            return

        test_options = {t.test_id: f"Test {t.test_id}  –  {t.date}" for t in tests}
        selected_tid = col_t.selectbox(
            "Test auswählen",
            options=list(test_options.keys()),
            format_func=lambda x: test_options[x],
            key="ana_test",
        )

    test = study.get_test_by_id(selected_tid)

    with st.spinner("EKG-Daten werden geladen …"):
        ekg = _load_ekg_cached(test.result_link, test.test_id)
    if ekg is None:
        st.error("EKG-Daten konnten nicht geladen werden.")
        return

    max_hr_limit = person.calc_max_heart_rate() if person else None

    # ── Test-Steckbrief ────────────────────────────────────────────────────
    st.markdown(
        f"### Auswertung: {person.get_full_name() if person else '–'}  "
        f"&nbsp;|&nbsp; Test {selected_tid}  "
        f"&nbsp;|&nbsp; Aufnahmedatum: **{test.date}**"
    )

    avg_hr  = test.avg_hr()
    max_hr_val = test.max_hr()
    dur_min = test.duration_min()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Aufnahmedauer",    f"{dur_min:.2f} min"        if dur_min     else "–",
                help="Gesamtlänge der EKG-Aufnahme in Minuten")
    col2.metric("Ø Herzfrequenz",   f"{avg_hr:.1f} bpm"         if avg_hr      else "–",
                help="Durchschnittliche Herzfrequenz über die gesamte Aufnahme")
    col3.metric("Max. Herzfrequenz",f"{max_hr_val:.1f} bpm"     if max_hr_val  else "–",
                help="Höchste gemessene Herzfrequenz (aus dem kürzesten RR-Intervall)")
    col4.metric("Max-HR-Grenzwert", f"{max_hr_limit:.0f} bpm"   if max_hr_limit else "–",
                help="Alters-/geschlechtsspezifischer Grenzwert (Tanaka-Formel)")

    st.divider()

    # ── Zeitbereich-Slider ─────────────────────────────────────────────────
    st.subheader("Schritt 1 — Zeitbereich wählen")
    st.caption(
        "Ziehe die Regler, um einen Ausschnitt der Aufnahme zu vergrößern. "
        "EKG-Signal und Herzfrequenz-Kurve aktualisieren sich sofort."
    )

    t_min_s, t_max_s = ekg.get_time_range_s()
    if t_max_s > t_min_s:
        time_range = st.slider(
            "Zeitfenster (Sekunden)",
            min_value=t_min_s, max_value=t_max_s,
            value=(t_min_s, t_max_s), step=1,
            key="sl_ana_leiter",
        )
        start_ms, end_ms = time_range[0] * 1000, time_range[1] * 1000
    else:
        start_ms, end_ms = t_min_s * 1000, t_max_s * 1000

    # Kennzahlen für das gewählte Fenster
    ws = ekg.window_stats(start_ms, end_ms)
    if ws:
        with st.container(border=True):
            st.caption("Kennzahlen für den gewählten Zeitbereich")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Dauer",     f"{ws['dauer_s']/60:.2f} min")
            c2.metric("R-Peaks",   ws["peaks"],
                      help="Anzahl erkannter Herzschläge im gewählten Fenster")
            c3.metric("Ø HR",      f"{ws['avg_hr']:.1f} bpm"    if ws.get("avg_hr")    else "–")
            c4.metric("Max HR",    f"{ws['max_hr']:.1f} bpm"    if ws.get("max_hr")    else "–")
            c5.metric("HRV (SDNN)",f"{ws['hrv_sdnn']:.1f} ms"  if ws.get("hrv_sdnn") else "–",
                      help="Herzratenvariabilität: Standardabweichung der RR-Intervalle. "
                           "Höhere Werte = gesündere Variabilität.")

    st.divider()

    # ── Kombinierter Plot ──────────────────────────────────────────────────
    st.subheader("Schritt 2 — EKG-Signal & Herzfrequenz")

    with st.container(border=True):
        st.markdown(
            "**Oberes Panel — EKG-Signal (mV)**  \n"
            "Zeigt die elektrische Herzaktivität über die Zeit. "
            "**Rote Punkte** markieren erkannte R-Peaks (Herzschläge)."
        )
        st.markdown(
            "**Unteres Panel — Herzfrequenz (bpm)**  \n"
            "Grüne Linie: HR je Herzschlag aus RR-Abstand.  "
            "**Orangene Linie**: gleitender Durchschnitt (5 Schläge) — zeigt den Trend.  "
            "**Rote gestrichelte Linie**: individueller Max-HR-Grenzwert."
        )
        fig = ekg.plot_combined(start_ms, end_ms, max_hr_line=max_hr_limit)
        st.plotly_chart(fig, use_container_width=True, key=f"leiter_main_plot_{selected_tid}")
        st.caption(
            "Tipp: Im Diagramm kannst du mit der Maus in einen Bereich hineinzoomen "
            "oder die Legende anklicken, um einzelne Kurven ein-/auszublenden."
        )

    # ── Anomalien ──────────────────────────────────────────────────────────
    anomalies = ekg.detect_anomalies(person)
    st.divider()
    st.subheader("Schritt 3 — Auffälligkeiten")
    if anomalies:
        for a in anomalies:
            st.error(
                f"**{a['typ']}**  \n"
                f"Gemessener Wert: **{a['wert']}**  |  Grenzwert: {a['grenzwert']}  \n\n"
                f"{a['empfehlung']}"
            )
    else:
        st.success("Keine Auffälligkeiten im gesamten Test festgestellt.")

    # ── Rohdaten ───────────────────────────────────────────────────────────
    with st.expander("Rohdaten des gewählten Zeitfensters anzeigen"):
        st.caption("Zeilen mit besonders hohen Ausschlägen (>95 % des Maximums) sind rot markiert.")
        df_raw = ekg.df[
            (ekg.df["Zeit in ms"] >= start_ms) &
            (ekg.df["Zeit in ms"] <= end_ms)
        ].copy()
        if not df_raw.empty:
            threshold_val = 0.95 * df_raw["Messwerte in mV"].max()

            def _highlight(row):
                return (["background-color: #ffcccc"] * len(row)
                        if row["Messwerte in mV"] > threshold_val else [""] * len(row))

            st.dataframe(df_raw.style.apply(_highlight, axis=1),
                         use_container_width=True, height=300)

    # ── Testvergleich ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("Test-Vergleich")

    if len(tests) < 2:
        st.info("Mindestens zwei Tests für einen Vergleich nötig.")
        return

    st.caption(
        "Wähle einen zweiten Test, um beide Aufnahmen direkt nebeneinander zu vergleichen. "
        "Der Schieberegler steuert den angezeigten Zeitbereich für beide Tests gleichzeitig."
    )

    compare_options = {t.test_id: f"Test {t.test_id}  –  {t.date}"
                       for t in tests if t.test_id != selected_tid}
    compare_tid = st.selectbox(
        "Vergleichs-Test auswählen",
        options=list(compare_options.keys()),
        format_func=lambda x: compare_options[x],
        key="compare_test",
    )
    test2 = study.get_test_by_id(compare_tid)
    with st.spinner("Vergleichs-EKG wird geladen …"):
        ekg2 = _load_ekg_cached(test2.result_link, test2.test_id)

    if ekg2:
        t2_min_s, t2_max_s = ekg2.get_time_range_s()
        common_max = min(t_max_s - t_min_s, t2_max_s - t2_min_s)
        compare_range = st.slider(
            "Gemeinsames Zeitfenster (Sekunden, relativ zum Start jedes Tests)",
            min_value=0, max_value=common_max,
            value=(0, common_max), step=1,
            key="sl_compare_leiter",
        )
        s1_ms = (t_min_s + compare_range[0]) * 1000
        e1_ms = (t_min_s + compare_range[1]) * 1000
        s2_ms = (t2_min_s + compare_range[0]) * 1000
        e2_ms = (t2_min_s + compare_range[1]) * 1000

        col_a, col_b = st.columns(2)
        with col_a:
            with st.container(border=True):
                st.markdown(f"**Test {selected_tid}  –  Aufnahme vom {test.date}**")
                st.plotly_chart(
                    ekg.plot_combined(s1_ms, e1_ms, max_hr_line=max_hr_limit),
                    use_container_width=True,
                    key=f"leiter_compare_a_{selected_tid}_{compare_tid}",
                )
        with col_b:
            with st.container(border=True):
                st.markdown(f"**Test {compare_tid}  –  Aufnahme vom {test2.date}**")
                st.plotly_chart(
                    ekg2.plot_combined(s2_ms, e2_ms, max_hr_line=max_hr_limit),
                    use_container_width=True,
                    key=f"leiter_compare_b_{selected_tid}_{compare_tid}",
                )

        st.markdown("**Direktvergleich der Kennzahlen**")
        comp_rows = []
        for t_obj, lbl in [(test, f"Test {selected_tid}  ({test.date})"),
                           (test2, f"Test {compare_tid}  ({test2.date})")]:
            comp_rows.append({
                "Test": lbl,
                "Dauer (min)":  f"{t_obj.duration_min():.2f}" if t_obj.duration_min() else "–",
                "Ø HR (bpm)":   f"{t_obj.avg_hr():.1f}"       if t_obj.avg_hr()        else "–",
                "Max HR (bpm)": f"{t_obj.max_hr():.1f}"       if t_obj.max_hr()        else "–",
            })
        st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)

        # ── Automatische Zusammenfassung ──────────────────────────────────
        hr1, hr2 = test.avg_hr(), test2.avg_hr()
        mhr1, mhr2 = test.max_hr(), test2.max_hr()
        if hr1 and hr2:
            diff = hr2 - hr1
            diff_str = f"{'gestiegen (+' if diff > 0 else 'gesunken ('}{abs(diff):.1f} bpm)"
            if abs(diff) < 5:
                bewertung = "Die durchschnittliche Herzfrequenz ist nahezu unverändert — die kardiovaskuläre Belastung war in beiden Aufnahmen vergleichbar."
            elif diff < 0:
                bewertung = "Die Herzfrequenz ist gesunken — dies kann auf einen Trainingsfortschritt, bessere Erholung oder geringere Belastung hinweisen."
            else:
                bewertung = "Die Herzfrequenz ist gestiegen — mögliche Ursachen sind höhere Belastung, Stress, Erkrankung oder unzureichende Erholung."

            with st.container(border=True):
                st.markdown("**Auswertung des Vergleichs**")
                st.write(
                    f"Zwischen Test {selected_tid} ({test.date}) und Test {compare_tid} ({test2.date}) "
                    f"hat sich die durchschnittliche Herzfrequenz von **{hr1:.1f} bpm** auf "
                    f"**{hr2:.1f} bpm** {diff_str}). {bewertung}"
                )
                if mhr1 and mhr2:
                    mdiff = mhr2 - mhr1
                    mdir = "höher" if mdiff > 0 else "niedriger"
                    st.write(
                        f"Die maximale Herzfrequenz war im zweiten Test "
                        f"**{abs(mdiff):.1f} bpm {mdir}** ({mhr1:.1f} → {mhr2:.1f} bpm)."
                    )


# ----------------------------------------------------------------- Tab 6

def _tab_verwaltung(study, db):
    st.header("Verwaltung")

    all_persons = study.get_all_persons()
    active = [p for p in all_persons if p.status == "approved"]
    pending = [p for p in all_persons if p.status == "pending"]
    rejected = [p for p in all_persons if p.status == "rejected"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Aktive Probanden", len(active))
    col2.metric("Ausstehend", len(pending))
    col3.metric("Abgelehnt", len(rejected))

    st.subheader("Aktive Probanden – Übersicht")
    if active:
        rows = []
        for p in active:
            tests = study.get_tests_by_person(p.id)
            avg_list = [t.avg_hr() for t in tests if t.avg_hr() is not None]
            rows.append({
                "Name": p.get_full_name(),
                "Alter": p.calc_age(),
                "Tests": len(tests),
                "Ø HR": f"{sum(avg_list)/len(avg_list):.1f}" if avg_list else "–",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Keine aktiven Probanden.")

    st.divider()
    st.subheader("Datenexport")
    if st.button("Test-Daten als CSV exportieren"):
        csv_data = study.export_stats_to_csv()
        st.download_button(
            label="CSV herunterladen",
            data=csv_data,
            file_name="ekg_studie_export.csv",
            mime="text/csv",
        )
