import streamlit as st
import pandas as pd


@st.cache_data(show_spinner=False)
def _load_ekg_cached(result_link: str, test_id: int):
    """Cached: EKG-Datei einmalig laden — verhindert wiederholtes Einlesen."""
    from ekgdata import EKGdata
    try:
        return EKGdata({"id": test_id, "date": "", "result_link": result_link})
    except Exception:
        return None


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

    # ── Profil bearbeiten ──────────────────────────────────────────────────
    st.divider()
    st.subheader("Profil bearbeiten")

    with st.form("proband_edit_form"):
        new_last   = st.text_input("Nachname", value=person.lastname or "")
        new_weight = st.number_input(
            "Körpergewicht (kg)", min_value=20.0, max_value=300.0,
            value=float(person.weight) if person.weight else 70.0,
            step=0.5,
        )
        new_pic = st.file_uploader("Profilbild ändern (optional)", type=["jpg", "jpeg", "png"])
        edit_submitted = st.form_submit_button("Änderungen speichern", type="primary")

    if edit_submitted:
        import os
        pic_path = None
        if new_pic is not None:
            os.makedirs("data/pictures", exist_ok=True)
            pic_path = f"data/pictures/person_{person.id}_{new_pic.name}"
            with open(pic_path, "wb") as f:
                f.write(new_pic.getbuffer())
        db.update_person(
            person_id=person.id,
            firstname=person.firstname,
            lastname=new_last.strip(),
            date_of_birth=person.date_of_birth,
            email=person.email,
            gender=person.gender,
            weight=float(new_weight),
            fitness_level=person.fitness_level,
            picture_path=pic_path,
        )
        st.success("Profil aktualisiert.")
        st.rerun()

    # ── Profil löschen ─────────────────────────────────────────────────────
    st.divider()
    with st.expander("Profil löschen", icon="🗑️"):
        st.warning(
            "Dein Profil, alle deine Tests und dein Login-Account werden "
            "**unwiderruflich gelöscht**. Diese Aktion kann nicht rückgängig gemacht werden."
        )
        if st.session_state.get("confirm_delete_self"):
            col_yes, col_no = st.columns(2)
            if col_yes.button("Ja, Profil endgültig löschen", type="primary", key="del_self_yes"):
                db.delete_person(person.id)
                st.session_state.user = None
                st.session_state.pop("confirm_delete_self", None)
                st.rerun()
            if col_no.button("Abbrechen", key="del_self_no"):
                st.session_state.pop("confirm_delete_self", None)
                st.rerun()
        else:
            if st.button("Profil löschen", key="del_self_btn"):
                st.session_state["confirm_delete_self"] = True
                st.rerun()


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
            ekg = _load_ekg_cached(test.result_link, test.test_id)
        if ekg:
            st.subheader(f"EKG-Signal – {test.date}")
            st.plotly_chart(ekg.plot_time_series_with_peaks(), use_container_width=True,
                            key=f"proband_detail_{selected_tid}")


# ----------------------------------------------------------------- Tab 3

def _tab_analyse(study, db, person):
    """Interaktive Analyse der eigenen EKG-Daten."""
    st.header("Meine EKG-Analyse")

    tests = study.get_tests_by_person(person.id)
    if not tests:
        st.info("Noch keine Tests vorhanden. Bitte wende dich an die Studienleitung.")
        return

    # ── Test auswählen ─────────────────────────────────────────────────────
    test_options = {t.test_id: f"Aufnahme vom {t.date}  (Test-ID {t.test_id})" for t in tests}
    selected_tid = st.selectbox(
        "Welchen Test möchtest du auswerten?",
        options=list(test_options.keys()),
        format_func=lambda x: test_options[x],
        key="proband_ana_test",
    )
    test = study.get_test_by_id(selected_tid)

    with st.spinner("EKG-Daten werden geladen …"):
        ekg = _load_ekg_cached(test.result_link, test.test_id)

    if ekg is None:
        st.error("Die EKG-Daten konnten nicht geladen werden.")
        return

    max_hr_limit = person.calc_max_heart_rate()

    # ── Test-Steckbrief ────────────────────────────────────────────────────
    avg_hr     = test.avg_hr()
    max_hr_val = test.max_hr()
    dur_min    = test.duration_min()

    st.markdown(f"### Auswertung — Aufnahme vom **{test.date}**")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Aufnahmedauer",      f"{dur_min:.2f} min"    if dur_min     else "–",
                help="Wie lange die Aufnahme insgesamt dauerte")
    col2.metric("Ø Herzfrequenz",     f"{avg_hr:.1f} bpm"     if avg_hr      else "–",
                help="Dein durchschnittlicher Herzschlag über die gesamte Aufnahme")
    col3.metric("Max. Herzfrequenz",  f"{max_hr_val:.1f} bpm" if max_hr_val  else "–",
                help="Dein höchstes gemessenes Herzschlagtempo")
    col4.metric("Dein HR-Grenzwert",  f"{max_hr_limit:.0f} bpm",
                help="Dein individueller Maximalwert (berechnet aus Alter & Geschlecht)")

    st.divider()

    # ── Zeitbereich-Slider ─────────────────────────────────────────────────
    st.subheader("Schritt 1 — Zeitbereich wählen")
    st.caption(
        "Schiebe die Regler, um einen bestimmten Abschnitt deiner Aufnahme zu vergrößern. "
        "Beide Diagramme passen sich sofort an."
    )

    t_min_s, t_max_s = ekg.get_time_range_s()
    if t_max_s > t_min_s:
        time_range = st.slider(
            "Zeitfenster (Sekunden)",
            min_value=t_min_s, max_value=t_max_s,
            value=(t_min_s, t_max_s), step=1,
            key="sl_ana_proband",
        )
        start_ms, end_ms = time_range[0] * 1000, time_range[1] * 1000
    else:
        start_ms, end_ms = t_min_s * 1000, t_max_s * 1000

    # Kennzahlen für das Fenster
    ws = ekg.window_stats(start_ms, end_ms)
    if ws:
        with st.container(border=True):
            st.caption("Kennzahlen für den gewählten Abschnitt")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Dauer",      f"{ws['dauer_s']/60:.2f} min")
            c2.metric("Ø HR",       f"{ws['avg_hr']:.1f} bpm"   if ws.get("avg_hr")    else "–")
            c3.metric("Max HR",     f"{ws['max_hr']:.1f} bpm"   if ws.get("max_hr")    else "–")
            c4.metric("HRV (SDNN)", f"{ws['hrv_sdnn']:.1f} ms" if ws.get("hrv_sdnn") else "–",
                      help="Herzratenvariabilität — ein Maß für die Anpassungsfähigkeit deines Herzens. "
                           "Höhere Werte sind in der Regel ein gutes Zeichen.")

    st.divider()

    # ── Kombinierter Plot ──────────────────────────────────────────────────
    st.subheader("Schritt 2 — Dein EKG & Herzfrequenz")

    with st.container(border=True):
        st.markdown(
            "**Oberes Diagramm — EKG-Signal (mV)**  \n"
            "Zeigt deine elektrische Herzaktivität. "
            "Jeder **rote Punkt** ist ein erkannter Herzschlag (R-Peak)."
        )
        st.markdown(
            "**Unteres Diagramm — Herzfrequenz (bpm)**  \n"
            "Die **grüne Linie** zeigt, wie schnell dein Herz schlägt.  "
            "Die **orangene Linie** ist ein gleitender Durchschnitt — sie zeigt den Gesamttrend.  "
            "Die **rote gestrichelte Linie** ist dein persönlicher Maximalwert."
        )
        fig = ekg.plot_combined(start_ms, end_ms, max_hr_line=max_hr_limit)
        st.plotly_chart(fig, use_container_width=True, key=f"proband_main_plot_{selected_tid}")
        st.caption(
            "Tipp: Du kannst im Diagramm mit der Maus in einen Bereich hineinzoomen "
            "oder auf Legendeneinträge klicken, um einzelne Kurven zu zeigen/verstecken."
        )

    # ── Gesundheitshinweise ────────────────────────────────────────────────
    anomalies = ekg.detect_anomalies(person)
    st.divider()
    st.subheader("Schritt 3 — Gesundheitshinweise")

    if anomalies:
        for a in anomalies:
            st.warning(
                f"**{a['typ']}**  \n"
                f"Gemessener Wert: **{a['wert']}**  |  Dein Grenzwert: {a['grenzwert']} bpm  \n\n"
                f"{a['empfehlung']}"
            )

        st.error(
            "**Achtung: Auffälligkeiten festgestellt!**  \n"
            "Bitte nimm diese Hinweise ernst und wende dich an medizinisches Fachpersonal."
        )

        # ── Hilfe-Button ──────────────────────────────────────────────────
        st.markdown("###")
        with st.expander("Hilfe & Notfallkontakte — Was soll ich tun?", icon="🆘", expanded=True):
            st.markdown("#### Was bedeuten diese Warnungen?")

            erklaerungen = {
                "Tachykardie": (
                    "**Tachykardie** bedeutet, dass dein Herz zu schnell schlägt "
                    "(über deinem persönlichen Maximalwert). "
                    "Das kann nach starker körperlicher Belastung normal sein, "
                    "aber auch auf ein Herzproblem hinweisen."
                ),
                "Bradykardie": (
                    "**Bradykardie** bedeutet, dass dein Herz sehr langsam schlägt "
                    "(unter 40 Schläge pro Minute). "
                    "Bei Leistungssportlern kann das normal sein — "
                    "ansonsten sollte dies ärztlich abgeklärt werden."
                ),
                "Unregelmäßiger Rhythmus": (
                    "**Unregelmäßiger Herzrhythmus** bedeutet, dass die Abstände "
                    "zwischen deinen Herzschlägen stark schwanken. "
                    "Dies kann auf eine Herzrhythmusstörung hinweisen."
                ),
            }
            for a in anomalies:
                for key, text in erklaerungen.items():
                    if key.lower() in a["typ"].lower():
                        st.info(text)
                        break

            st.markdown("---")
            st.markdown("#### Wann muss ich sofort handeln?")
            st.error(
                "**Ruf sofort den Notruf (112) an, wenn du:**  \n"
                "- Schmerzen oder Druck in der Brust hast  \n"
                "- Atemnot, Schwindel oder Ohnmachtsgefühl verspürst  \n"
                "- Starkes Herzrasen oder -stolpern bemerkst, das nicht aufhört  \n"
                "- Dich sehr unwohl fühlst"
            )

            st.markdown("---")
            st.markdown("#### Wichtige Kontakte")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(
                    """
                    <div style='background:#7f1d1d;padding:16px;border-radius:10px;text-align:center;'>
                    <div style='font-size:28px;'>🚨</div>
                    <div style='font-weight:bold;font-size:18px;color:white;'>Notruf</div>
                    <div style='font-size:28px;font-weight:900;color:#fca5a5;'>112</div>
                    <div style='font-size:12px;color:#fca5a5;'>Lebensbedrohliche Notfälle</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    """
                    <div style='background:#1e3a5f;padding:16px;border-radius:10px;text-align:center;'>
                    <div style='font-size:28px;'>🏥</div>
                    <div style='font-weight:bold;font-size:18px;color:white;'>Bereitschaft</div>
                    <div style='font-size:28px;font-weight:900;color:#93c5fd;'>116 117</div>
                    <div style='font-size:12px;color:#93c5fd;'>Kassenärztlicher Dienst (24h)</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col3:
                st.markdown(
                    """
                    <div style='background:#1a3a1a;padding:16px;border-radius:10px;text-align:center;'>
                    <div style='font-size:28px;'>🩺</div>
                    <div style='font-weight:bold;font-size:18px;color:white;'>Hausarzt</div>
                    <div style='font-size:18px;font-weight:700;color:#86efac;'>Termin vereinbaren</div>
                    <div style='font-size:12px;color:#86efac;'>Für nicht-dringende Abklärung</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("---")
            st.markdown("#### Arzt in deiner Nähe finden")
            st.markdown(
                "- **Arztsuche** der Kassenärztlichen Vereinigung: "
                "[www.arztsuche.116117.de](https://www.arztsuche.116117.de)  \n"
                "- **Kardiologen finden** (Herzspezialisten): "
                "[www.kardiologie.org/patienteninfo](https://www.kardiologie.org/patienteninfo)  \n"
                "- **Telefonische Beratung** (kostenlos, 24h): **116 117**"
            )

            st.markdown("---")
            st.caption(
                "Diese Hinweise ersetzen keine ärztliche Diagnose. "
                "Bei Unsicherheit wende dich immer an deine Studienleitung oder einen Arzt."
            )
    else:
        st.success(
            "Alles im grünen Bereich! Keine Auffälligkeiten in dieser Aufnahme festgestellt."
        )

    # ── Trendvergleich ─────────────────────────────────────────────────────
    if len(tests) >= 2:
        st.divider()
        st.subheader("Test-Vergleich — Wie hat sich dein Herz verändert?")
        st.caption(
            "Wähle eine zweite Aufnahme, um beide direkt nebeneinander zu vergleichen. "
            "Der Schieberegler steuert beide Diagramme gleichzeitig."
        )

        compare_options = {t.test_id: f"Aufnahme vom {t.date}  (Test-ID {t.test_id})"
                           for t in tests if t.test_id != selected_tid}
        compare_tid = st.selectbox(
            "Vergleichs-Aufnahme auswählen",
            options=list(compare_options.keys()),
            format_func=lambda x: compare_options[x],
            key="proband_compare_test",
        )
        test2 = study.get_test_by_id(compare_tid)
        with st.spinner("Vergleichs-EKG wird geladen …"):
            ekg2 = _load_ekg_cached(test2.result_link, test2.test_id)

        if ekg2:
            t2_min_s, t2_max_s = ekg2.get_time_range_s()
            common_max = min(t_max_s - t_min_s, t2_max_s - t2_min_s)
            compare_range = st.slider(
                "Gemeinsames Zeitfenster für beide Aufnahmen (Sekunden)",
                min_value=0, max_value=common_max,
                value=(0, common_max), step=1,
                key="sl_compare_proband",
            )
            s1_ms = (t_min_s + compare_range[0]) * 1000
            e1_ms = (t_min_s + compare_range[1]) * 1000
            s2_ms = (t2_min_s + compare_range[0]) * 1000
            e2_ms = (t2_min_s + compare_range[1]) * 1000

            col_a, col_b = st.columns(2)
            with col_a:
                with st.container(border=True):
                    st.markdown(f"**Aufnahme vom {test.date}**")
                    st.plotly_chart(
                        ekg.plot_combined(s1_ms, e1_ms, max_hr_line=max_hr_limit),
                        use_container_width=True,
                        key=f"proband_compare_a_{selected_tid}_{compare_tid}",
                    )
            with col_b:
                with st.container(border=True):
                    st.markdown(f"**Aufnahme vom {test2.date}**")
                    st.plotly_chart(
                        ekg2.plot_combined(s2_ms, e2_ms, max_hr_line=max_hr_limit),
                        use_container_width=True,
                        key=f"proband_compare_b_{selected_tid}_{compare_tid}",
                    )

            st.markdown("**Vergleich der Kennzahlen**")
            trend_rows = []
            for t_obj, lbl in [(test,  f"Aufnahme {test.date}"),
                                (test2, f"Aufnahme {test2.date}")]:
                trend_rows.append({
                    "Aufnahme":     lbl,
                    "Dauer (min)":  f"{t_obj.duration_min():.2f}" if t_obj.duration_min() else "–",
                    "Ø HR (bpm)":   f"{t_obj.avg_hr():.1f}"       if t_obj.avg_hr()        else "–",
                    "Max HR (bpm)": f"{t_obj.max_hr():.1f}"       if t_obj.max_hr()        else "–",
                })
            st.dataframe(pd.DataFrame(trend_rows), use_container_width=True, hide_index=True)

            # ── Automatische Zusammenfassung ──────────────────────────────
            hr1, hr2 = test.avg_hr(), test2.avg_hr()
            mhr1, mhr2 = test.max_hr(), test2.max_hr()
            if hr1 and hr2:
                diff = hr2 - hr1
                diff_str = f"{'gestiegen (+' if diff > 0 else 'gesunken ('}{abs(diff):.1f} bpm)"
                if abs(diff) < 5:
                    bewertung = "Deine durchschnittliche Herzfrequenz ist nahezu gleich geblieben — das deutet auf eine stabile körperliche Verfassung hin."
                elif diff < 0:
                    bewertung = "Deine Herzfrequenz ist gesunken — das kann auf einen positiven Trainingseffekt oder eine bessere Erholung hinweisen."
                else:
                    bewertung = "Deine Herzfrequenz ist gestiegen — das könnte auf höhere Belastung, Stress oder weniger Erholung hindeuten."

                with st.container(border=True):
                    st.markdown("**Auswertung des Vergleichs**")
                    st.write(
                        f"Zwischen der Aufnahme vom **{test.date}** und der vom **{test2.date}** "
                        f"ist deine durchschnittliche Herzfrequenz von **{hr1:.1f} bpm** auf "
                        f"**{hr2:.1f} bpm** {diff_str}). {bewertung}"
                    )
                    if mhr1 and mhr2:
                        mdiff = mhr2 - mhr1
                        mdir = "höher" if mdiff > 0 else "niedriger"
                        st.write(
                            f"Auch deine maximale Herzfrequenz war in der zweiten Aufnahme "
                            f"**{abs(mdiff):.1f} bpm {mdir}** ({mhr1:.1f} → {mhr2:.1f} bpm)."
                        )


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
