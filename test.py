"""Modul für EKG-Tests — verknüpft Personen mit ihren Messdaten."""

from ekgdata import EKGdata


class Test:
    """Repräsentiert einen einzelnen EKG-Test einer Person.

    Attributes:
        test_id: Eindeutige Test-ID.
        person_id: ID der zugehörigen Person.
        date: Testdatum als String (TT.MM.JJJJ).
        ekg_data: Geladenes EKGdata-Objekt (lazy, beim ersten Zugriff befüllt).
        result_link: Dateipfad zur EKG-Rohdatendatei (.txt / .tsv).
    """

    def __init__(self, test_id=None, person_id=None, date=None,
                 ekg_data=None, result_link=None):
        self.test_id = test_id
        self.person_id = person_id
        self.date = date
        self.ekg_data = ekg_data
        self.result_link = result_link

    def load_ekg_data(self):
        """Lädt die EKG-Daten aus der Datei (nur beim ersten Aufruf).

        Returns:
            EKGdata-Objekt oder None, wenn kein result_link gesetzt ist.
        """
        if self.ekg_data is None and self.result_link is not None:
            self.ekg_data = EKGdata({
                "id": self.test_id,
                "date": self.date,
                "result_link": self.result_link,
            })
        return self.ekg_data

    def duration(self):
        """Gibt die Messdauer in Sekunden zurück.

        Returns:
            Dauer in Sekunden (float) oder None bei fehlenden Daten.
        """
        ekg = self.load_ekg_data()
        if ekg is not None and ekg.df is not None:
            return (ekg.df["Zeit in ms"].max() - ekg.df["Zeit in ms"].min()) / 1000
        return None

    def duration_min(self):
        """Gibt die Messdauer in Minuten zurück.

        Returns:
            Dauer in Minuten (float) oder None bei fehlenden Daten.
        """
        d = self.duration()
        return d / 60 if d is not None else None

    def basic_stats(self):
        """Berechnet deskriptive Statistiken des EKG-Signals.

        Returns:
            Dict mit Schlüsseln 'mean', 'std', 'min', 'max' (in mV)
            oder None bei fehlenden Daten.
        """
        ekg = self.load_ekg_data()
        if ekg is not None and ekg.df is not None:
            return {
                "mean": ekg.df["Messwerte in mV"].mean(),
                "std":  ekg.df["Messwerte in mV"].std(),
                "min":  ekg.df["Messwerte in mV"].min(),
                "max":  ekg.df["Messwerte in mV"].max(),
            }
        return None

    def avg_hr(self):
        """Gibt die durchschnittliche Herzfrequenz in bpm zurück.

        Returns:
            Durchschnittliche HR (float) oder None.
        """
        ekg = self.load_ekg_data()
        return ekg.estimate_hr() if ekg else None

    def max_hr(self):
        """Gibt die maximale instantane Herzfrequenz in bpm zurück.

        Returns:
            Maximale HR (float) oder None.
        """
        ekg = self.load_ekg_data()
        return ekg.max_hr() if ekg else None


if __name__ == "__main__":
    test = Test(
        test_id=1,
        person_id=1,
        date="10.2.2023",
        result_link="data/ekg_data/01_Ruhe.txt",
    )
    print("Test-ID:", test.test_id)
    print("Dauer (min):", test.duration_min())
    print("Avg HR:", test.avg_hr())
    print("Max HR:", test.max_hr())
