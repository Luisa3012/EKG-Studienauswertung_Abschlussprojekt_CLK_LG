import os
import json
from person import Person
from test import Test


class Study:

    def __init__(self):
        self.persons = []
        self.tests = []


    def load_from_db(self, db):
        self.persons = db.get_all_persons()
        self.tests = db.get_all_tests()


    def get_all_persons(self):
        return self.persons

    def get_person_by_id(self, person_id):
        for p in self.persons:
            if p.id == person_id:
                return p
        return None

    def get_pending_persons(self):
        return [p for p in self.persons if p.status == "pending"]


    def get_all_tests(self):
        return self.tests

    def get_tests_by_person(self, person_id):
        return [t for t in self.tests if t.person_id == person_id]

    def get_test_by_id(self, test_id):
        for t in self.tests:
            if t.test_id == test_id:
                return t
        return None


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


    def get_total_persons(self):
        return len(self.persons)

    def get_total_tests(self):
        return len(self.tests)

    def get_average_hr_all_tests(self):
        values = [t.avg_hr() for t in self.tests if t.avg_hr() is not None]
        return sum(values) / len(values) if values else None



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
                f"{f'{dur:.1f}' if dur is not None else ''},"
                f"{f'{avg:.1f}' if avg is not None else ''},"
                f"{f'{mx:.1f}' if mx is not None else ''}"
            )
        return "\n".join(lines)


if __name__ == "__main__":
    from person import Person
    from test import Test

    p1 = Person(1, 1989, "Julian", "Huber", "data/pictures/tb.jpg",
                "Male", "julian.huber@example.com", "approved")
    p2 = Person(2, 1967, "Yannic", "Heyer", "data/pictures/js.jpg",
                "Male", "yannic.heyer@example.com", "pending")

    t1 = Test(test_id=1, person_id=1, date="10.2.2023",
              result_link="data/ekg_data/01_Ruhe.txt")
    t2 = Test(test_id=2, person_id=1, date="11.3.2023",
              result_link="data/ekg_data/04_Belastung.txt")
    t3 = Test(test_id=3, person_id=2, date="10.2.2023",
              result_link="data/ekg_data/02_Ruhe.txt")

    study = Study()
    study.persons = [p1, p2]
    study.tests = [t1, t2, t3]

    print("Alle Personen:")
    for p in study.get_all_persons():
        print(" ", p)

    print("\nPerson mit ID 1:", study.get_person_by_id(1))
    print("Person mit ID 99:", study.get_person_by_id(99))

    print("\nPending-Probanden:")
    for p in study.get_pending_persons():
        print(" ", p)

    print(f"\nAnzahl Tests gesamt: {study.get_total_tests()}")
    print(f"Anzahl Personen gesamt: {study.get_total_persons()}")

    print("\nTests von Person 1:")
    for t in study.get_tests_by_person(1):
        print(f"  Test {t.test_id} vom {t.date}")

    print("\nTest mit ID 2:", study.get_test_by_id(2).date)
    print("Test mit ID 99:", study.get_test_by_id(99))

    print("\nCSV-Export:")
    print(study.export_stats_to_csv())
