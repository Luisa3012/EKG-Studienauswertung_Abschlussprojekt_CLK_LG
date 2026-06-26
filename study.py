import os
import json
from person import Person
from test import Test


class Study:
    def __init__(self):
        self.persons = []
        self.tests = []

    # ---------------------------------------------------------- Laden aus DB

    def load_from_db(self, db):
        self.persons = db.get_all_persons()
        self.tests = db.get_all_tests()

    # -------------------------------------------- Personen-Zugriff (in-mem)

    def get_all_persons(self):
        return self.persons

    def get_person_by_id(self, person_id):
        for p in self.persons:
            if p.id == person_id:
                return p
        return None

    def get_pending_persons(self):
        return [p for p in self.persons if p.status == "pending"]

    # ----------------------------------------------- Test-Zugriff (in-mem)

    def get_all_tests(self):
        return self.tests

    def get_tests_by_person(self, person_id):
        return [t for t in self.tests if t.person_id == person_id]

    def get_test_by_id(self, test_id):
        for t in self.tests:
            if t.test_id == test_id:
                return t
        return None

    # ------------------------------------------------------ Test hinzufügen

    def add_test_with_file_upload(self, db, person_id, date, uploaded_file):
        """
        Speichert eine hochgeladene EKG-Datei nach data/ekg_data/ und legt
        den Test in der Datenbank an. Gibt den neuen Test zurück.
        """
        os.makedirs("data/ekg_data", exist_ok=True)
        filename = f"upload_{person_id}_{date.replace('.', '-')}_{uploaded_file.name}"
        filepath = os.path.join("data", "ekg_data", filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())

        test_id = db.add_test(person_id, date, filepath)
        new_test = Test(test_id=test_id, person_id=person_id, date=date, result_link=filepath)
        self.tests.append(new_test)
        return new_test

    # ----------------------------------------------------------- Statistiken

    def get_total_persons(self):
        return len(self.persons)

    def get_total_tests(self):
        return len(self.tests)

    def get_average_hr_all_tests(self):
        values = [t.avg_hr() for t in self.tests if t.avg_hr() is not None]
        return sum(values) / len(values) if values else None

    # ----------------------------------------- JSON-Export (Datenexport CSV)

    def export_stats_to_csv(self):
        """Gibt einen CSV-String aller Test-Kennzahlen zurück."""
        lines = ["Person,Test-ID,Datum,Dauer(s),Ø HR,Max HR"]
        for t in self.tests:
            person = self.get_person_by_id(t.person_id)
            name = person.get_full_name() if person else str(t.person_id)
            avg = t.avg_hr()
            mx = t.max_hr()
            dur = t.duration()
            lines.append(
                f"{name},{t.test_id},{t.date},"
                f"{dur:.1f if dur else ''},"
                f"{avg:.1f if avg else ''},"
                f"{mx:.1f if mx else ''}"
            )
        return "\n".join(lines)
