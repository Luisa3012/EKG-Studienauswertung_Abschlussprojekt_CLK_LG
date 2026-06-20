class User:
    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.role = role

class Login:
    def __init__(self):
        self.users = [
            User("proband1", "1234", "proband"),
            User("leiter", "abcd", "leiter")
        ]

    def login(self, username, password):
        for user in self.users:
            if user.username == username and user.password == password:
                return user
        return None
    


if __name__ == "__main__":   
    login = Login()
    user = login.login("leiter", "abcd")

    if user is None:
        print("Login fehlgeschlagen")

    else:
        print("Login erfolgreich!")

        if user.role == "leiter":
            print("Zugriff: Alle Daten anzeigen")

        elif user.role == "proband":
            print("Zugriff: nur eigene Daten anzeigen")