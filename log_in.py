class User:
    def __init__(self, username, password, role, person_id=None):
        self.username = username
        self.password = password
        self.role = role
        self.person_id = person_id

class Login:
    def __init__(self):
        self.users = [
            User("proband1", "1234", "proband", person_id=1),
            User("leiter", "abcd", "leiter")
        ]

    def login(self, username, password):
        for user in self.users:
            if user.username == username and user.password == password:
                return user
        return None
    

if __name__ == "__main__":
    login = Login()
    user = login.login("proband1", "1234")

    if user is None:
        print("Login fehlgeschlagen")
    else:
        print("Login erfolgreich!")
        if user.role == "leiter":
            print("Zugriff: Alle Daten anzeigen")
        elif user.role == "proband":
            print("Zugriff: nur eigene Daten, person_id =", user.person_id)