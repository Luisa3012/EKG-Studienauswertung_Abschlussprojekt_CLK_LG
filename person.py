"""Modul für Personen/Probanden der EKG-Studie."""

import datetime
from PIL import Image


class Person:
    """Repräsentiert einen Probanden in der EKG-Studie.

    Attributes:
        id: Eindeutige Personen-ID.
        date_of_birth: Geburtsjahr (int, z.B. 1990).
        firstname: Vorname.
        lastname: Nachname.
        picture_path: Dateipfad zum Profilbild.
        gender: Geschlecht ('Male', 'Female' oder 'Divers').
        email: E-Mail-Adresse.
        status: Registrierungsstatus ('pending', 'approved', 'rejected').
        weight: Körpergewicht in kg (optional).
        fitness_level: Sportlicher Zustand ('aktiv', 'gelegentlich', 'inaktiv').
    """

    def __init__(self, id: int, date_of_birth: int, firstname: str, lastname: str,
                 picture_path: str, gender: str, email: str, status: str,
                 weight: float = None, fitness_level: str = None):
        self.id = id
        self.date_of_birth = date_of_birth
        self.firstname = firstname
        self.lastname = lastname
        self.picture_path = picture_path
        self.gender = gender
        self.email = email
        self.status = status
        self.weight = weight
        self.fitness_level = fitness_level

    def get_full_name(self) -> str:
        """Gibt den vollen Namen als 'Nachname, Vorname' zurück."""
        return f"{self.lastname}, {self.firstname}"

    def get_image(self) -> Image.Image:
        """Lädt und gibt das Profilbild als PIL-Image zurück."""
        return Image.open(self.picture_path)

    def calc_age(self) -> int:
        """Berechnet das aktuelle Alter anhand des Geburtsjahres.

        Returns:
            Alter in ganzen Jahren.
        """
        return datetime.date.today().year - self.date_of_birth

    def calc_max_heart_rate(self) -> float:
        """Berechnet die geschätzte maximale Herzfrequenz (geschlechtsspezifisch).

        Formeln:
            Männlich:  208 − 0,7 × Alter  (Tanaka-Formel)
            Weiblich:  206 − 0,88 × Alter
            Sonstige:  220 − Alter

        Returns:
            Maximale Herzfrequenz in bpm.
        """
        age = self.calc_age()
        if self.gender == "Male":
            return 208 - 0.7 * age
        elif self.gender == "Female":
            return 206 - 0.88 * age
        return 220 - age

    def __str__(self) -> str:
        return (f"Person(id={self.id}, name={self.get_full_name()}, "
                f"geb={self.date_of_birth}, status={self.status})")


if __name__ == "__main__":
    p = Person(1, 1990, "Julian", "Huber", "data/pictures/tb.jpg",
               "Male", "julian.huber@example.com", "pending")
    print(p.get_full_name())
    print("Alter:", p.calc_age())
    print("Max HR:", p.calc_max_heart_rate())
