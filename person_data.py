import json

class PersonData:
    def __init__(self):
        self.persons = self.get_person_data()

    @staticmethod
    def get_person_data():
        with open("persons.json", "r", encoding="utf-8") as file:
            return json.load(file)

    def load_by_id(self, person_id):
        for person in self.persons:
            if person["id"] == person_id:
                return person
        return None

    def get_test(self, person_id, test_id):
        person = self.load_by_id(person_id)
        if person is None:
            return None

        for test in person["ekg_tests"]:
            if test["id"] == test_id:
                return test
        return None

    
if __name__ == "__main__":

    pd = PersonData()
    print(pd.load_by_id(1))
    print(pd.get_test(1, 1))