import pandas as pd
import plotly.express as px


class EKGdata:

## Konstruktor der Klasse soll die Daten einlesen

    def __init__(self, ekg_dict):
        self.id = ekg_dict["id"]
        self.date = ekg_dict["date"]
        self.data = ekg_dict["result_link"]
        self.df = pd.read_csv(self.data, sep='\t', header=None, names=['Messwerte in mV','Zeit in ms',])
        self.df = self.df.iloc[:5000]  # Begrenzt auf ersten 5000 Messwerte
        self.fig = None  # Initialisiert die Figur als None, wird später für Plotly verwendet

    

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
    
    
    
    
    def max_hr(self,threshold=0.9):
        peak_times = self.find_peaks(threshold)
        rr_intervals_ms = peak_times.diff()
        hr_per_beat = 60000 / rr_intervals_ms
        return hr_per_beat.max()
    
    def plot_time_series(self):
        self.fig = px.line(self.df, x="Zeit in ms", y="Messwerte in mV")
        return self.fig

    def plot_time_series_with_peaks(self, threshold=0.9):
        self.plot_time_series()
        peak_times = self.find_peaks(threshold)
        peak_values = self.df["Messwerte in mV"][self.df["Zeit in ms"].isin(peak_times)]

        self.fig.add_scatter(
            x=peak_times,
            y=peak_values,
            mode='markers',
            marker=dict(color='blue', size=8),
            name='Peaks'
        )
      
        return self.fig
    

    
if __name__ == "__main__":
    ekg = EKGdata({"id": 1, "date": "10.2.2023", "result_link": "data/ekg_data/01_Ruhe.txt"})
    peaks = ekg.find_peaks()
    print("Peaks gefunden:", len(peaks))
    print("Herzfrequenz geschätzt:", ekg.estimate_hr())
    print("Max HR:", ekg.max_hr())
    fig = ekg.plot_time_series_with_peaks()
    fig.show()