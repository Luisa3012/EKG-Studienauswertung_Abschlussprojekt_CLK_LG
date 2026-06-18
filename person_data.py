import json
import person


class person_data: 

    def load_persons(self, filename):
        with open(filename, "r") as file:
            self.persons = json.load(file)

        return self.persons

    def load_by_id (self, id):
        persons = self.load_persons("persons.json")
        for person in persons:
            if person.id == id:
                return person
        return None
    
    def calc_max_heart_rate(self):
        age = self.calc_age()
        gender = self.gender
        if gender == "Male":
            return (208-(0.7*age))
        elif gender == "Female":
            return (206-(0.88*age))
        else: 
            return (220-age)
        

    def get_test(self, person_id, test_id):
        person = self.get_person_by_id(person_id)

        if person is None:
            return None

        for test in person["ekg_tests"]:
            if test["test_id"] == test_id:
                return test

        return None
