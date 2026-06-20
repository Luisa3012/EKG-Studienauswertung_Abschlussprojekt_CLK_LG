print("Hello world")


from ekgdata import EKGdata

class Test:

    def __init__(self, test_id=None, person_id=None, date=None, ekg_data=None):
        self.test_id = test_id
        self.person_id = person_id
        self.date = date
        self.ekg_data = ekg_data

    def duration(self):
        if self.ekg_data is not None and self.ekg_data.df is not None:
            return (
                self.ekg_data.df["Zeit in ms"].max()
                - self.ekg_data.df["Zeit in ms"].min()
            ) / 1000
        return None

    def basic_stats(self):
        if self.ekg_data is not None and self.ekg_data.df is not None:
            return {
                "mean": self.ekg_data.df["Messwerte in mV"].mean(),
                "std": self.ekg_data.df["Messwerte in mV"].std(),
                "min": self.ekg_data.df["Messwerte in mV"].min(),
                "max": self.ekg_data.df["Messwerte in mV"].max()
            }
        return None


if __name__ == "__main__":

    ekg_dict = {
        "id": 1,
        "date": "10.2.2023",
        "result_link": "data/ekg_data/01_Ruhe.txt"
    }

    ekg_data = EKGdata(ekg_dict)

    test = Test(
        test_id=1,
        person_id=1,
        date="10.2.2023",
        ekg_data=ekg_data
    )

    print("Test-ID:", test.test_id)
    print("Person-ID:", test.person_id)
    print("Datum:", test.date)

    print("\nErste 5 Zeilen der EKG-Daten:")
    print(test.ekg_data.df.head())

    print("\nDauer:")
    print(test.duration())

    print("\nStatistiken:")
    print(test.basic_stats())