class User:
    def __init__(self, username, password, role, person_id=None):
        self.username = username
        self.password = password
        self.role = role
        self.person_id = person_id


class Login:

    def __init__(self, db):
        self.db = db

    def login(self, username, password):
        return self.db.get_user_by_credentials(username, password)

    def register(self, firstname, lastname, date_of_birth, email, gender,
                 weight, fitness_level, username, password):
        """
        Legt eine neue Person (Status 'pending') und einen User-Account an.
        Gibt die neue Person zurück oder None wenn der Benutzername bereits existiert.
        """
        if self.db.username_exists(username):
            return None

        person_id = self.db.add_person(
            firstname=firstname,
            lastname=lastname,
            date_of_birth=date_of_birth,
            email=email,
            gender=gender,
            weight=weight,
            fitness_level=fitness_level,
            status="pending",
        )
        self.db.add_user(username, password, "proband", person_id)
        return self.db.get_person_by_id(person_id)

