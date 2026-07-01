# EKG-Studienauswertung - Abschlussprojekt

Streamlit-Anwendung zur Verwaltung und Auswertung einer EKG-Studie. Probanden können sich registrieren und ihre eigenen EKG-Tests einsehen, Studienleiter verwalten Probanden, Tests und werten die aufgezeichneten EKG-Rohdaten aus (Herzfrequenz, Peak-Erkennung, Anomalieerkennung).

---

## Funktionen

Nach dem Login wird je nach Rolle eine eigene Oberfläche angezeigt:

**Studienleiter-Portal**

| Tab | Inhalt |
|-----|--------|
| **Übersicht** | Überblick über Studienstatus und Kennzahlen |
| **Registrierungen** | Annahme/Ablehnung neuer Proband-Registrierungen |
| **Probandenverwaltung** | Verwaltung der Probanden-Stammdaten |
| **Testverwaltung** | Anlegen und Verwalten von EKG-Tests |
| **Analyse** | Auswertung der EKG-Rohdaten (Herzfrequenz, Peaks, Anomalien) |
| **Verwaltung** | Allgemeine Studienverwaltung |

**Proband-Portal**

| Tab | Inhalt |
|-----|--------|
| **Mein Profil** | Eigene Stammdaten |
| **Meine Tests** | Übersicht der eigenen EKG-Tests |
| **Analyse** | Auswertung der eigenen EKG-Daten |
| **Über die Studie** | Informationen zur Studie |

Die Authentifizierung (Login/Registrierung) erfolgt über ein eigenes Benutzersystem mit den Rollen `leiter` und `proband`. Visualisierung der EKG-Signale mit Plotly.

---

## Login

Auf der Startseite der App stehen zwei Optionen zur Verfügung: **Anmelden** (links) und **Neu registrieren** (rechts).

**Studienleiter-Login**

| Benutzername | Passwort |
|--------------|----------|
| `leiter`     | `abcd`   |

Mit diesem Account gelangt man direkt in das Studienleiter-Portal.

**Proband-Login**

Probanden registrieren sich selbst über das Formular **Neu registrieren** (Vorname, Nachname, E-Mail, Geburtsjahr, Geschlecht, Körpergewicht, sportlicher Zustand, Benutzername, Passwort). Nach dem Absenden hat der Account zunächst den Status *pending* und muss von einem Studienleiter im Tab **Registrierungen** freigeschaltet werden. Erst danach ist ein Login mit dem gewählten Benutzernamen und Passwort möglich.
| Benutzername | Passwort |
|--------------|----------|
| `julian`     | `1234`   |


---

## Installation und Start

Voraussetzungen: **Python 3.13**, **uv**.

```bash
uv sync
uv run streamlit run main.py
```

Die Anwendung ist unter `http://localhost:8501/` erreichbar (Port kann abweichen, URL siehe Terminal).

`uv sync` installiert alle Abhängigkeiten exakt in den in `uv.lock` festgehaltenen Versionen in eine projekteigene virtuelle Umgebung. Der Start über `uv run` stellt sicher, dass diese Umgebung verwendet wird.

---

## Projektstruktur

```
- main.py            # Einstiegspunkt der Streamlit-App, Login/Registrierung, Routing
- log_in.py           # Authentifizierung (Login, Registrierung)
- studienleiter.py     # Oberfläche und Logik für die Rolle "Studienleiter"
- proband.py          # Oberfläche und Logik für die Rolle "Proband"
- person.py           # Datenmodell für Probanden/Personen
- study.py            # Datenmodell für die Studie
- ekgdata.py           # Laden, Analyse und Visualisierung der EKG-Rohdaten
- database.py          # Zugriff auf die SQLite-Datenbank
- data/                # Eingabe- und Anwendungsdaten (DB, EKG-Rohdaten, Bilder)
- pyproject.toml        # Projekt-Metadaten und Abhängigkeiten (uv)
- uv.lock             # Exakte, gepinnte Abhängigkeitsversionen (uv)
```

---

## Datenformat

Die EKG-Rohdaten liegen als Tab-getrennte Textdateien (`.txt`) in `data/ekg_data/` und werden mit 500 Hz aufgezeichnet. Jede Datei enthält zwei Spalten ohne Header:

- **Spalte 1** – Messwerte (mV)
- **Spalte 2** – Zeit (ms)

Proband- und Studiendaten werden in einer SQLite-Datenbank unter `data/ekg_study.db` gespeichert.

---

## Abhängigkeiten

- **Streamlit** – Web-Oberfläche
- **Pandas** – Datenverarbeitung
- **Plotly** – Visualisierung der EKG-Signale
- **Pillow** – Bildverarbeitung

Alle Abhängigkeiten und ihre Versionen sind in `pyproject.toml` definiert und in `uv.lock` für reproduzierbare Installationen gepinnt.

---

## Autoren

- Luisa Grimm 
- Clara Kerber

