import Person
import EKGdata

class Study:
    def __init__(self):
        self.persons = []
        self.tests = []

    # Personen werden verwaltet --> werden Liste hinzugefügt

    def add_person():
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
    
    def get_average_hr_all_tests(selfs):
        all_values = []
        for test in self.tests:
            all_values.extend(test.ekg_data)
        return sum(all_values) / len(all_values)
        
    
    
    