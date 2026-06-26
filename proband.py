import streamlit as st
import pandas as pd


def render_proband(study, db, user):
    person = db.get_person_by_id(user.person_id)
    if person is None:
        st.error("Proband-Daten konnten nicht geladen werden.")
        return

    st.title(f"Willkommen, {person.firstname}!")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Mein Profil",
        "Meine Tests",
        "Analyse",
        "Über die Studie",
    ])

    with tab1:
        _tab_profil(study, db, person)
    with tab2:
        _tab_tests(study, db, person)
    with tab3:
        _tab_analyse(study, db, person)
    with tab4:
        _tab_ueber_studie()


# ----------------------------------------------------------------- Tab 1

def _tab_profil(study, db, person):
    st.header("Mein Profil")

    col_img, col_info = st.columns([1, 3])
    with col_img:
        try:
            st.image(person.get_image(), width=130)
        except Exception:
            st.write("(Kein Foto hinterlegt)")

    with col_info:
        st.markdown(f"### {person.get_full_name()}")
        st.write(f"**Geburtsjahr:** {person.date_of_birth}  |  **Alter:** {person.calc_age()} Jahre")
        st.write(f"**Geschlecht:** {person.gender or '–'}  |  **E-Mail:** {person.email or '–'}")
        if person.weight:
            st.write(f"**Körpergewicht:** {person.weight} kg  |  **Fitnesslevel:** {person.fitness_level or '–'}")
        st.write(f"**Max. Herzfrequenz (errechnet):** {person.calc_max_heart_rate():.0f} bpm")

    st.divider()
    tests = study.get_tests_by_person(person.id)
    avg_list = [t.avg_hr() for t in tests if t.avg_hr() is not None]
    last_date = tests[-1].date if tests else "–"

    col1, col2, col3 = st.columns(3)
    col1.metric("Anzahl Tests", len(tests))
    col2.metric("Letzter Test", last_date)
    col3.metric("Ø Herzfrequenz (eigene Tests)", f"{sum(avg_list)/len(avg_list):.1f} bpm" if avg_list else "–")


# ----------------------------------------------------------------- Tab 2

def _tab_tests(study, db, person):
    st.header("Meine Tests")

    tests = study.get_tests_by_person(person.id)
    if not tests:
        st.info("Noch keine Tests vorhanden.")
        return

    rows = []
    for t in tests:
        rows.append({
            "Nr.": t.test_id,
            "Datum": t.date,
            "Dauer (s)": f"{t.duration():.1f}" if t.duration() else "–",
            "Ø HR (bpm)": f"{t.avg_hr():.1f}" if t.avg_hr() else "–",
            "Max HR (bpm)": f"{t.max_hr():.1f}" if t.max_hr() else "–",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    test_options = {t.test_id: f"Test {t.test_id} – {t.date}" for t in tests}
    selected_tid = st.selectbox(
        "Test für Detailansicht auswählen",
        options=list(test_options.keys()),
        format_func=lambda x: test_options[x],
        key="proband_test_detail",
    )
    test = study.get_test_by_id(selected_tid)
    if test:
        with st.spinner("Lade EKG-Daten..."):
            ekg = test.load_ekg_data()
        if ekg:
            st.subheader(f"EKG-Signal – {test.date}")
            st.plotly_chart(ekg.plot_time_series_with_peaks(), use_container_width=True)


# ----------------------------------------------------------------- Tab 3

def _tab_analyse(study, db, person):
    st.header("Meine EKG-Analyse")

    tests = study.get_tests_by_person(person.id)
    if not tests:
        st.info("Noch keine Tests für die Analyse vorhanden.")
        return

    test_options = {t.test_id: f"Test {t.test_id} – {t.date}" for t in tests}
    selected_tid = st.selectbox(
        "Test auswählen",
        options=list(test_options.keys()),
        format_func=lambda x: test_options[x],
        key="proband_ana_test",
    )
    test = study.get_test_by_id(selected_tid)

    with st.spinner("EKG-Daten werden geladen..."):
        ekg = test.load_ekg_data()

    if ekg is None:
        st.error("EKG-Daten konnten nicht geladen werden.")
        return

    avg_hr = test.avg_hr()
    max_hr_val = test.max_hr()
    max_hr_limit = person.calc_max_heart_rate()

    dur_min = test.duration_min()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ø Herzfrequenz", f"{avg_hr:.1f} bpm" if avg_hr else "–")
    col2.metric("Max. Herzfrequenz", f"{max_hr_val:.1f} bpm" if max_hr_val else "–")
    col3.metric("Ihr HR-Grenzwert", f"{max_hr_limit:.0f} bpm")
    col4.metric("Aufnahmedauer", f"{dur_min:.2f} min" if dur_min else "–")

    st.divider()

    # --- Zeitbereich-Slider ---
    t_min_s, t_max_s = ekg.get_time_range_s()
    st.subheader("Interaktiver Plot — Zeitbereich wählen")

    if t_max_s > t_min_s:
        time_range = st.slider(
            "Zeitfenster (Sekunden)",
            min_value=t_min_s,
            max_value=t_max_s,
            value=(t_min_s, t_max_s),
            step=1,
            key="sl_ana_proband",
            help="Verschieben Sie die Regler, um einen bestimmten Bereich zu vergrößern.",
        )
        start_ms = time_range[0] * 1000
        end_ms = time_range[1] * 1000
    else:
        start_ms = t_min_s * 1000
        end_ms = t_max_s * 1000

    # Fenster-Statistik
    ws = ekg.window_stats(start_ms, end_ms)
    if ws:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Dauer (Auswahl)", f"{ws['dauer_s']/60:.2f} min")
        c2.metric("Ø HR", f"{ws['avg_hr']:.1f} bpm" if ws.get("avg_hr") else "–")
        c3.metric("Max HR", f"{ws['max_hr']:.1f} bpm" if ws.get("max_hr") else "–")
        c4.metric("HRV (SDNN)", f"{ws['hrv_sdnn']:.1f} ms" if ws.get("hrv_sdnn") else "–")

    # Kombinierter Plot
    fig = ekg.plot_combined(start_ms, end_ms, max_hr_line=max_hr_limit)
    st.plotly_chart(fig, use_container_width=True)

    # Anomalie-Hinweise
    anomalies = ekg.detect_anomalies(person)
    if anomalies:
        st.subheader("Wichtige Hinweise")
        for a in anomalies:
            st.warning(
                f"**{a['typ']}** (Messwert: {a['wert']}, Grenzwert: {a['grenzwert']} bpm)\n\n"
                f"{a['empfehlung']}"
            )
        st.info(
            "Bei gesundheitlichen Beschwerden oder Fragen zu diesen Hinweisen:\n\n"
            "Notruf: **112**  |  Kassenärztlicher Bereitschaftsdienst: **116 117**\n\n"
            "Bitte wenden Sie sich auch an Ihre Studienleitung."
        )
    else:
        st.success("Keine Auffälligkeiten in diesem Test festgestellt.")

    # Trendvergleich
    if len(tests) >= 2:
        st.divider()
        st.subheader("Trendvergleich")

        compare_options = {t.test_id: f"Test {t.test_id} – {t.date}" for t in tests if t.test_id != selected_tid}
        compare_tid = st.selectbox(
            "Vergleichs-Test auswählen",
            options=list(compare_options.keys()),
            format_func=lambda x: compare_options[x],
            key="proband_compare_test",
        )
        test2 = study.get_test_by_id(compare_tid)
        with st.spinner("Vergleichs-EKG wird geladen..."):
            ekg2 = test2.load_ekg_data()

        if ekg2:
            t2_min_s, t2_max_s = ekg2.get_time_range_s()
            common_max = min(t_max_s - t_min_s, t2_max_s - t2_min_s)
            compare_range = st.slider(
                "Vergleichs-Zeitfenster (Sekunden)",
                min_value=0,
                max_value=common_max,
                value=(0, common_max),
                step=1,
                key="sl_compare_proband",
            )
            s1_ms = (t_min_s + compare_range[0]) * 1000
            e1_ms = (t_min_s + compare_range[1]) * 1000
            s2_ms = (t2_min_s + compare_range[0]) * 1000
            e2_ms = (t2_min_s + compare_range[1]) * 1000

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Test {selected_tid} – {test.date}**")
                st.plotly_chart(ekg.plot_combined(s1_ms, e1_ms, max_hr_line=max_hr_limit), use_container_width=True)
            with col_b:
                st.markdown(f"**Test {compare_tid} – {test2.date}**")
                st.plotly_chart(ekg2.plot_combined(s2_ms, e2_ms, max_hr_line=max_hr_limit), use_container_width=True)

            trend_rows = []
            for t_obj, lbl in [(test, f"Test {selected_tid}"), (test2, f"Test {compare_tid}")]:
                trend_rows.append({
                    "Test": lbl,
                    "Datum": t_obj.date,
                    "Ø HR (bpm)": f"{t_obj.avg_hr():.1f}" if t_obj.avg_hr() else "–",
                    "Max HR (bpm)": f"{t_obj.max_hr():.1f}" if t_obj.max_hr() else "–",
                })
            st.dataframe(pd.DataFrame(trend_rows), use_container_width=True, hide_index=True)


# ----------------------------------------------------------------- Tab 4

def _tab_ueber_studie():
    st.header("Über diese Studie")

    st.markdown("""
    ## Ziel der Studie
    Diese EKG-Studie erfasst und analysiert die Herzaktivität von Probanden unter verschiedenen
    Belastungszuständen. Ziel ist es, Muster in der Herzfrequenz zu erkennen und die
    kardiovaskuläre Gesundheit der Teilnehmenden zu unterstützen.

    ## Ablauf
    1. **Registrierung** – Sie melden sich an und werden von der Studienleitung freigeschaltet.
    2. **Tests** – Die Studienleitung fügt EKG-Messungen für Sie hinzu.
    3. **Einsicht** – In Ihrem Portal sehen Sie Ihre Testergebnisse und können Trends verfolgen.
    4. **Hinweise** – Bei Auffälligkeiten erhalten Sie automatische Hinweise und Empfehlungen.

    ## Datenschutz
    Ihre Daten werden ausschließlich für Studienzwecke verwendet und nicht an Dritte weitergegeben.
    Sie können jederzeit die Löschung Ihrer Daten beantragen.

    ## Kontakt
    Bei Fragen zur Studie wenden Sie sich bitte an die Studienleitung:

    - **E-Mail:** studienleitung@ekg-studie.de
    - **Telefon:** 0800 123 456 (Mo–Fr 9–17 Uhr)

    ---
    *Notfall: 112  |  Ärztlicher Bereitschaftsdienst: 116 117*
    """)
