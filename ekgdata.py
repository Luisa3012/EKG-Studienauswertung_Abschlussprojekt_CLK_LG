import json
import pandas as pd
import plotly.express as px
import person
import study 

class EKGdata:

## Konstruktor der Klasse soll die Daten einlesen

    def __init__(self, ekg_dict):
        self.id = ekg_dict["id"]
        self.date = ekg_dict["date"]
        self.data = ekg_dict["result_link"]
        self.df = pd.read_csv(self.data, sep='\t', header=None, names=['Messwerte in mV','Zeit in ms',])
        self.df = self.df.iloc[:5000]  # Begrenzt auf ersten 5000 Messwerte

    @staticmethod
    def load_ekg_by_id(study, ekg_id):
        persons = person.get_person_data()
        for p in persons:
            for ekg in p["ekg_tests"]:
                if ekg["id"] == ekg_id:
                    return EKGdata(ekg)
        return None
    

    def find_peaks(self, threshold=0.9):
        is_peak = (
            (self.df["Messwerte in mV"] > self.df["Messwerte in mV"].shift(1)) &
            (self.df["Messwerte in mV"] >= self.df["Messwerte in mV"].shift(-1)) &
            (self.df["Messwerte in mV"] > threshold * self.df["Messwerte in mV"].max())
        )   
        return self.df["Zeit in ms"][is_peak]
    
    
    def estimate_hr(self, threshold=0.9):
            peak_times = self.find_peaks(threshold)
            number_peaks = len(peak_times)
            duration_min = (self.df["Zeit in ms"].max() - self.df["Zeit in ms"].min()) / 60000 # Dauer in Minuten
            return number_peaks/duration_min
    

    def plot_time_series_with_peaks(self, window_size=200, threshold_factor=1.2):
        self.plot_time_series()

        rolling_mean = self.df["Messwerte in mV"].rolling(window=window_size).mean()

        is_peak = (
        (self.df["Messwerte in mV"] > self.df["Messwerte in mV"].shift(1)) &
        (self.df["Messwerte in mV"] >= self.df["Messwerte in mV"].shift(-1)) &
        (self.df["Messwerte in mV"] > rolling_mean * threshold_factor)
        )

        peak_times = self.df["Zeit in ms"][is_peak]
        peak_values = self.df["Messwerte in mV"][is_peak]

        self.fig.add_scatter(
            x=peak_times,
            y=peak_values,
            mode='markers',
            marker=dict(color='blue', size=8),
            name='Peaks'
        )

        return self.fig
    
    
    def max_hr(self,):
        peak_times = self.find_peaks()
        rr_intervals_ms = peak_times.diff()
        hr_per_beat = 60000 / rr_intervals_ms
        return hr_per_beat.max()
    
    def plot_time_series(self):
        self.fig = px.line(self.df, x="Zeit in ms", y="Messwerte in mV")
        return self.fig
    
if __name__ == "__main__":
    ekg = EKGdata.load_ekg_by_id(study,1)
    if ekg is None:
        print("kein EKG gefunden")
    else:
        print("EKG laden")
    peaks=ekg.find_peaks()
    print("Peaks gefunden:", len(peaks))
    hr=ekg.estimate_hr()
    print("Herzfrequenz geschätzt:", hr)
    max_hr=ekg.max_hr()
    print("Max HR", max_hr)
    fig=ekg.plot_time_series_with_peaks()
    fig.show()