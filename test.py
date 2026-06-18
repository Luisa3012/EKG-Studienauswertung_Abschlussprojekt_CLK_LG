import pandas as pd
from ekgdata import EKGdata 


class Test:

    def __init__(self, test_id=None, person_id=None, date=None, ekg_data=None):
        self.test_id = test_id
        self.person_id = person_id
        self.date = date
        self.ekg_data = ekg_data

    def duration(self):
        if self.ekg_data is not None:
            return (
                self.ekg_data.df["Zeit in ms"].max()
                - self.ekg_data.df["Zeit in ms"].min()
            ) / 1000
        return None

    def basic_stats(self):
        if self.ekg_data is not None:
            return {
                "mean": self.ekg_data.df["Messwerte in mV"].mean(),
                "std": self.ekg_data.df["Messwerte in mV"].std(),
                "min": self.ekg_data.df["Messwerte in mV"].min(),
                "max": self.ekg_data.df["Messwerte in mV"].max()
            }
        return None
    




  


