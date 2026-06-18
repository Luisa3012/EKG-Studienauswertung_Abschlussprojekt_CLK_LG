import json
from PIL import Image


class Person:

    def __init__(self, id : int, date_of_birth : int, firstname, lastname, picture_path, ekg_tests, gender = "Male"):
        self.id = id
        self.date_of_birth = date_of_birth
        self.firstname = firstname
        self.lastname = lastname
        self.picture_path = picture_path
        self.ekg_tests = ekg_tests
        self.age = self.calc_age()
        self.gender = gender
        self.max_hr = self.calc_max_heart_rate()


    def get_full_name(self):
        return self.lastname + ", " + self.firstname


    def get_image(self):
        image = Image.open(self.picture_path)
        return image
    
    def load_by_id (self, id):
        persons = get_person_data()
        for person in persons:
            if person.id == id:
                return person
        return None
    
    def calc_age(self): 
        current_year = 2026
        age = current_year-self.date_of_birth
        return age
    
    def calc_max_heart_rate(self):
        age = self.calc_age()
        gender = self.gender
        if gender == "Male":
            return (208-(0.7*age))
        elif gender == "Female":
            return (206-(0.88*age))
        else: 
            return (220-age)
    
    def __str__(self):
        return "{Person: self.get_full_name()}, Geb.{self.date_of_birth}, Alter:{sel.age}"