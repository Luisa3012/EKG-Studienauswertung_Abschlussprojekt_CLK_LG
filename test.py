from ekgdata import EKGdata

class Test:

    def __init__(self, test_id=None, person_id=None, date=None, ekg_data=None, result_link=None):
        self.test_id = test_id
        self.person_id = person_id
        self.date = date
        self.ekg_data = ekg_data
        self.result_link = result_link
        
    def load_ekg_data(self):
        if self.ekg_data is None and self.result_link is not None:
            self.ekg_data = EKGdata({
                "id": self.test_id, 
                "date": self.date, 
                "result_link": self.result_link
            })
        return self.ekg_data


    def duration(self):
        ekg = self.load_ekg_data()
        if ekg is not None and ekg.df is not None:
            return (ekg.df["Zeit in ms"].max() - ekg.df["Zeit in ms"].min()) / 1000
        return None

    def basic_stats(self):
        ekg = self.load_ekg_data()
        if self.ekg_data is not None and self.ekg_data.df is not None:
            return {
                "mean": self.ekg_data.df["Messwerte in mV"].mean(),
                "std": self.ekg_data.df["Messwerte in mV"].std(),
                "min": self.ekg_data.df["Messwerte in mV"].min(),
                "max": self.ekg_data.df["Messwerte in mV"].max()
            }
        return None
    
    def avg_hr(self): 
        ekg = self.load_ekg_data()
        return ekg.estimate_hr() if ekg else None
    
    def max_hr(self):
        ekg = self.load_ekg_data()
        return ekg.max_hr() if ekg else None


if __name__ == "__main__":
    test = Test(
        test_id=1,
        person_id=1,
        date="10.2.2023",
        result_link="data/ekg_data/01_Ruhe.txt"
    )
    print("Test-ID:", test.test_id)
    print("Person-ID:", test.person_id)
    print("Datum:", test.date)
    print("Dauer:", test.duration())
    print("Avg HR:", test.avg_hr())
    print("Max HR:", test.max_hr())