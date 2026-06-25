from person import Person
from test import Test

class Study:
    def __init__(self):
        self.persons = []
        self.tests = []

    # Personen werden verwaltet --> werden Liste hinzugefügt

    def add_person(self, person):
        self.persons.append(person)

    def get_person_by_id(self, id):
        for person in self.persons:
            if person.id == id:
                return person
        return None
    
    def get_all_persons(self):
        return self.persons
    
    # Tests werden verwaltet --> werden Liste hinzugefügt

    def add_test(self, test):
        self.tests.append(test) 

    def get_test_by_person(self, person_id):
        return [t for t in self.tests if t.person_id == person_id]
    
    # Statistiken
    
    def get_total_persons(self):
        return len(self.persons)
    
    def get_total_tests(self):
        return len(self.tests)
    
    def get_average_hr_all_tests(self):
        all_values = []
        for test in self.tests:
            all_values.extend(test.ekg_data)
        return sum(all_values) / len(all_values)
    

if __name__ == "__main__":
    print ("Test Study class")
    from person import Person
    from test import Test
    study = Study()
    p1 = Person(1, 1990, "Julian", "Huber", "data/pictures/tb.jpg", "Male")
    t1 = Test(1, 1, "2026-01-01", [70, 72, 75, 73, 71])
    study.add_person(p1)
    print (study.get_total_persons())
    study.add_test(t1)
    print (study.get_total_tests())

    found = study.get_person_by_id(1)
    print (found.get_full_name())

    person_tests = study.get_test_by_person(1)
    print (len(person_tests))
    
