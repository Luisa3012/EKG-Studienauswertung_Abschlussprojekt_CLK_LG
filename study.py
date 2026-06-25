import json
from person import Person
from test import Test


class Study:
    def _init_(self):
        self.persons = []
        self.tests = []

    # ---------- Laden / Speichern ----------

    def load_from_json(self, filepath="data/person_db.json"):
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)

        self.persons = []
        self.tests = []

        for p in raw:
            person_obj = Person(
                id=p["id"],
                date_of_birth=p["date_of_birth"],
                firstname=p["firstname"],
                lastname=p["lastname"],
                picture_path=p["picture_path"],
                gender=p["gender"],
                email=p.get("email"),
                status=p.get("status", "pending")
            )
            self.persons.append(person_obj)

            for t in p.get("ekg_tests", []):
                test_obj = Test(
                    test_id=t["id"],
                    person_id=p["id"],
                    date=t["date"],
                    result_link=t["result_link"]
                )
                self.tests.append(test_obj)

    def save_to_json(self, filepath="data/person_db.json"):
        data = {"persons": []}
        for p in self.persons:
            person_tests = [
                {"id": t.test_id, "date": t.date, "result_link": t.result_link}
                for t in self.tests if t.person_id == p.id
            ]
            data["persons"].append({
                "id": p.id,
                "firstname": p.firstname,
                "lastname": p.lastname,
                "date_of_birth": p.date_of_birth,
                "picture_path": p.picture_path,
                "gender": p.gender,
                "email": p.email,
                "status": p.status,
                "ekg_tests": person_tests
            })
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_person_from_json(self, filepath):
        """Für die Registrierung: eine einzelne Person aus JSON importieren, landet als 'pending'."""
        with open(filepath, "r", encoding="utf-8") as f:
            p = json.load(f)

        new_id = max([person.id for person in self.persons], default=0) + 1
        person_obj = Person(
            id=new_id,
            date_of_birth=p["date_of_birth"],
            firstname=p["firstname"],
            lastname=p["lastname"],
            picture_path=p["picture_path"],
            gender=p["gender"],
            email=p.get("email"),
            status="pending"
        )
        self.persons.append(person_obj)
        self.save_to_json()
        return person_obj

    # ---------- Personen verwalten ----------

    def add_person(self, person):
        self.persons.append(person)

    def get_person_by_id(self, id):
        for person in self.persons:
            if person.id == id:
                return person
        return None

    def get_all_persons(self):
        return self.persons

    def get_pending_persons(self):
        return [p for p in self.persons if p.status == "pending"]

    def approve_person(self, person_id):
        p = self.get_person_by_id(person_id)
        if p:
            p.status = "approved"
            self.save_to_json()

    def reject_person(self, person_id):
        p = self.get_person_by_id(person_id)
        if p:
            p.status = "rejected"
            self.save_to_json()

    # ---------- Tests verwalten ----------

    def add_test(self, test):
        self.tests.append(test)
        self.save_to_json()

    def get_tests_by_person(self, person_id):
        return [t for t in self.tests if t.person_id == person_id]

    def get_test_by_id(self, test_id):
        for t in self.tests:
            if t.test_id == test_id:
                return t
        return None

    def import_test_from_csv(self, person_id, date, csv_path):
        new_id = max([t.test_id for t in self.tests], default=0) + 1
        test = Test(test_id=new_id, person_id=person_id, date=date, result_link=csv_path)
        self.add_test(test)
        return test

    # ---------- Statistiken ----------

    def get_total_persons(self):
        return len(self.persons)

    def get_total_tests(self):
        return len(self.tests)

    def get_average_hr_all_tests(self):
        values = [t.avg_hr() for t in self.tests if t.avg_hr() is not None]
        return sum(values) / len(values) if values else None


if __name__ == "__main__":
    study = Study()
    study.load_from_json("data/person_db.json")
    print("Personen:", study.get_total_persons())
    print("Tests:", study.get_total_tests())
    print("Pending:", [p.get_full_name() for p in study.get_pending_persons()])

