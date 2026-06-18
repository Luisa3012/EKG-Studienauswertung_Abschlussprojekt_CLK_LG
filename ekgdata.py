import json
import pandas as pd
import plotly.express as px
import person

class EKGdata:

## Konstruktor der Klasse soll die Daten einlesen

    def __init__(self, ekg_dict):
        #pass
        self.id = ekg_dict["id"]
        self.date = ekg_dict["date"]
        self.data = ekg_dict["result_link"]
        self.df = pd.read_csv(self.data, sep='\t', header=None, names=['Messwerte in mV','Zeit in ms',])
        self.df = self.df.iloc[:5000]  # Entferne die erste Zeile, da sie nur die Spaltennamen enthält



    def load_by_id(self, id):
        persons = person.get_person_data()
        for person in persons:
            for ekg in person.ekg_tests:
                if ekg["id"] == id:
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