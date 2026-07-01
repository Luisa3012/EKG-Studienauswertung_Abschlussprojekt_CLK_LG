"""Modul zur Verarbeitung und Visualisierung von EKG-Rohdaten."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Maximale Anzahl Messpunkte die für Plots gerendert werden (Performance).
_PLOT_MAX_POINTS = 10_000


class EKGdata:

    """Lädt und analysiert EKG-Messdaten aus einer Tab-separierten Textdatei.

    Die Rohdatei enthält zwei Spalten: Messwerte in mV und Zeit in ms,
    aufgezeichnet mit 500 Hz. Für rechenintensive Plot-Operationen wird
    das Signal automatisch heruntergesampelt.

    Attributes:
        id: Test-ID.
        date: Aufnahmedatum als String.
        data: Dateipfad zur Rohdatendatei.
        df: DataFrame mit allen geladenen Messpunkten (volle Auflösung).
    """

    def __init__(self, ekg_dict: dict, max_samples: int = 50_000):
        """Lädt EKG-Daten aus einer TSV-Datei.

        Args:
            ekg_dict: Dict mit Schlüsseln 'id', 'date', 'result_link'.
            max_samples: Maximale Anzahl zu ladender Zeilen (None = alle).
                         Begrenzt Ladezeit bei sehr langen Aufnahmen.
        """
        self.id = ekg_dict["id"]
        self.date = ekg_dict["date"]
        self.data = ekg_dict["result_link"]
        self.df = pd.read_csv(
            self.data, sep="\t", header=None,
            names=["Messwerte in mV", "Zeit in ms"],
        )
        if max_samples is not None:
            self.df = self.df.iloc[:max_samples]

    def find_peaks(self, threshold: float = 0.9) -> pd.Series:
        """Erkennt R-Peaks im EKG-Signal mittels Schwellenwert-Methode.

        Ein Peak muss größer als seine Nachbarn und größer als
        threshold × globales Maximum sein.

        Args:
            threshold: Anteil des globalen Maximums als Mindesthöhe (0–1).

        Returns:
            Series mit Zeitstempeln (ms) der erkannten Peaks.
        """
        mv = self.df["Messwerte in mV"]
        is_peak = (
            (mv > mv.shift(1)) &
            (mv >= mv.shift(-1)) &
            (mv > threshold * mv.max())
        )
        return self.df["Zeit in ms"][is_peak]

    def estimate_hr(self, threshold: float = 0.9) -> float | None:
        """Schätzt die mittlere Herzfrequenz über den gesamten Aufnahmezeitraum.

        Args:
            threshold: Peak-Erkennungsschwelle (weitergegeben an find_peaks).

        Returns:
            Durchschnittliche Herzfrequenz in bpm oder None bei zu wenigen Peaks.
        """
        peak_times = self.find_peaks(threshold)
        if len(peak_times) < 2:
            return None
        duration_min = (
            (self.df["Zeit in ms"].max() - self.df["Zeit in ms"].min()) / 60_000
        )
        return len(peak_times) / duration_min if duration_min > 0 else None

    def max_hr(self, threshold: float = 0.9) -> float | None:
        """Berechnet die maximale instantane Herzfrequenz aus RR-Intervallen.

        Args:
            threshold: Peak-Erkennungsschwelle.

        Returns:
            Maximale HR in bpm oder None bei zu wenigen Peaks.
        """
        peak_times = self.find_peaks(threshold)
        if len(peak_times) < 2:
            return None
        rr = peak_times.diff().dropna()
        rr = rr[rr > 0]
        return (60_000 / rr).max() if not rr.empty else None

    def get_time_range_s(self) -> tuple[int, int]:
        """Gibt den Zeitbereich des Signals in ganzen Sekunden zurück.

        Returns:
            Tupel (start_sek, end_sek).
        """
        return (
            int(self.df["Zeit in ms"].min() / 1000),
            int(self.df["Zeit in ms"].max() / 1000),
        )

    def window_stats(self, start_ms: float, end_ms: float,
                     threshold: float = 0.9) -> dict:
        """Berechnet Kennzahlen für ein Zeitfenster.

        Args:
            start_ms: Fensterstart in Millisekunden.
            end_ms: Fensterende in Millisekunden.
            threshold: Peak-Erkennungsschwelle.

        Returns:
            Dict mit Schlüsseln 'peaks', 'avg_hr', 'max_hr', 'dauer_s',
            'hrv_sdnn', 'hrv_rmssd'. Fehlende Werte sind None.
        """
        df_w = self.df[
            (self.df["Zeit in ms"] >= start_ms) &
            (self.df["Zeit in ms"] <= end_ms)
        ]
        if df_w.empty:
            return {}

        local_max = df_w["Messwerte in mV"].max()
        if local_max > 0:
            is_peak = (
                (df_w["Messwerte in mV"] > df_w["Messwerte in mV"].shift(1)) &
                (df_w["Messwerte in mV"] >= df_w["Messwerte in mV"].shift(-1)) &
                (df_w["Messwerte in mV"] > threshold * local_max)
            )
            peak_times = df_w["Zeit in ms"][is_peak]
        else:
            peak_times = pd.Series(dtype=float)

        duration_min = (end_ms - start_ms) / 60_000
        avg_hr = (
            len(peak_times) / duration_min
            if duration_min > 0 and len(peak_times) >= 2 else None
        )

        rr = peak_times.diff().dropna()
        rr = rr[rr > 0]
        max_hr = (60_000 / rr).max() if not rr.empty else None

        # Herzratenvariabilität
        hrv_sdnn = float(rr.std()) if len(rr) >= 2 else None
        hrv_rmssd = (
            float((rr.diff().dropna() ** 2).mean() ** 0.5)
            if len(rr) >= 3 else None
        )

        return {
            "peaks": len(peak_times),
            "avg_hr": avg_hr,
            "max_hr": max_hr,
            "dauer_s": (end_ms - start_ms) / 1000,
            "hrv_sdnn": hrv_sdnn,
            "hrv_rmssd": hrv_rmssd,
        }

    def detect_anomalies(self, person=None, threshold: float = 0.9) -> list[dict]:
        """Erkennt Anomalien im EKG-Signal.

        Geprüft werden:
        - Tachykardie (Max-HR überschreitet personenspezifischen Grenzwert)
        - Bradykardie (Durchschnitts-HR < 40 bpm)
        - Unregelmäßiger Herzrhythmus (SDNN der RR-Intervalle > 200 ms)

        Args:
            person: Person-Objekt zur Berechnung des Max-HR-Grenzwerts (optional).
            threshold: Peak-Erkennungsschwelle.

        Returns:
            Liste von Dicts mit Schlüsseln 'typ', 'wert', 'grenzwert', 'empfehlung'.
        """
        anomalies = []
        peak_times = self.find_peaks(threshold)
        avg = self.estimate_hr(threshold)
        mx = self.max_hr(threshold)

        if person is not None and mx is not None:
            limit = person.calc_max_heart_rate()
            if mx > limit:
                anomalies.append({
                    "typ": "Tachykardie / Max-HR überschritten",
                    "wert": round(mx, 1),
                    "grenzwert": round(limit, 1),
                    "empfehlung": (
                        "Die maximale Herzfrequenz wurde überschritten. "
                        "Bitte setzen Sie sich mit einem Arzt in Verbindung."
                    ),
                })

        if avg is not None and avg < 40:
            anomalies.append({
                "typ": "Bradykardie (zu langsame Herzfrequenz)",
                "wert": round(avg, 1),
                "grenzwert": 40.0,
                "empfehlung": (
                    "Die durchschnittliche Herzfrequenz liegt unter 40 bpm. "
                    "Bitte konsultieren Sie einen Arzt."
                ),
            })

        if len(peak_times) >= 3:
            rr = peak_times.diff().dropna()
            rr = rr[rr > 0]
            if rr.std() > 200:
                anomalies.append({
                    "typ": "Unregelmäßiger Herzrhythmus",
                    "wert": round(rr.std(), 1),
                    "grenzwert": 200.0,
                    "empfehlung": (
                        "Unregelmäßige RR-Intervalle erkannt (SDNN > 200 ms). "
                        "Dies könnte auf eine Herzrhythmusstörung hinweisen — "
                        "bitte einen Arzt informieren."
                    ),
                })

        return anomalies


    @staticmethod
    def _downsample(df: pd.DataFrame, max_points: int = _PLOT_MAX_POINTS) -> pd.DataFrame:
        """Reduziert die Auflösung eines DataFrames für flüssiges Plot-Rendering.

        Args:
            df: Eingabe-DataFrame.
            max_points: Maximale Anzahl Zeilen im Ergebnis.

        Returns:
            Heruntergesampleter DataFrame (jeden n-ten Punkt).
        """
        if len(df) <= max_points:
            return df
        step = len(df) // max_points
        return df.iloc[::step]

    def plot_combined(self, start_ms: float = None, end_ms: float = None,
                      threshold: float = 0.9,
                      max_hr_line: float = None) -> go.Figure:
        """Kombinierter interaktiver Plot: EKG-Signal oben, Herzfrequenz unten.

        Beide Panels teilen die x-Achse — Zoom und Pan wirken synchron.
        Das EKG-Signal wird für das Rendering heruntergesampelt; die
        Peak-Erkennung nutzt die volle Auflösung des gewählten Fensters.

        Args:
            start_ms: Fensterstart in ms (None = Aufnahmestart).
            end_ms: Fensterende in ms (None = Aufnahmeende).
            threshold: Peak-Erkennungsschwelle.
            max_hr_line: Grenzwert für Max-HR als horizontale Linie (optional).

        Returns:
            Plotly Figure mit zwei Subplots.
        """
        t_min = self.df["Zeit in ms"].min()
        t_max = self.df["Zeit in ms"].max()
        start_ms = start_ms if start_ms is not None else t_min
        end_ms = end_ms if end_ms is not None else t_max

        df_w = self.df[
            (self.df["Zeit in ms"] >= start_ms) &
            (self.df["Zeit in ms"] <= end_ms)
        ].copy()

        if df_w.empty:
            return go.Figure()

        # Peak-Erkennung auf voller Fenster-Auflösung
        local_max = df_w["Messwerte in mV"].max()
        if local_max > 0:
            is_peak = (
                (df_w["Messwerte in mV"] > df_w["Messwerte in mV"].shift(1)) &
                (df_w["Messwerte in mV"] >= df_w["Messwerte in mV"].shift(-1)) &
                (df_w["Messwerte in mV"] > threshold * local_max)
            )
            peak_times = df_w["Zeit in ms"][is_peak]
            peak_values = df_w["Messwerte in mV"][is_peak]
        else:
            peak_times = pd.Series(dtype=float)
            peak_values = pd.Series(dtype=float)

        # HR-Kurve + gleitender Durchschnitt
        hr_x, hr_y, hr_rolling = [], [], []
        if len(peak_times) >= 2:
            rr = peak_times.diff().dropna()
            rr = rr[rr > 0]
            if not rr.empty:
                hr_vals = 60_000 / rr
                hr_x = peak_times.loc[rr.index].values
                hr_y = hr_vals.values
                # gleitender Durchschnitt über 5 Schläge
                hr_rolling = hr_vals.rolling(window=5, center=True).mean().values

        # EKG downsampled für Rendering
        df_plot = self._downsample(df_w)

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.6, 0.4],
            vertical_spacing=0.06,
            subplot_titles=("EKG-Signal (mV)", "Herzfrequenz (bpm)"),
        )

        # EKG-Linie (heruntergesampelt)
        fig.add_trace(go.Scatter(
            x=df_plot["Zeit in ms"],
            y=df_plot["Messwerte in mV"],
            mode="lines",
            name="EKG",
            line=dict(color="#636EFA", width=1),
            hovertemplate="Zeit: %{x} ms<br>Signal: %{y:.1f} mV<extra></extra>",
        ), row=1, col=1)

        # R-Peaks (volle Auflösung)
        if not peak_times.empty:
            fig.add_trace(go.Scatter(
                x=peak_times,
                y=peak_values,
                mode="markers",
                name="R-Peaks",
                marker=dict(color="red", size=9, symbol="circle"),
                hovertemplate="Peak: %{x} ms<br>%{y:.1f} mV<extra></extra>",
            ), row=1, col=1)

        # HR-Kurve
        if len(hr_x) > 0:
            fig.add_trace(go.Scatter(
                x=hr_x, y=hr_y,
                mode="lines+markers",
                name="HR (bpm)",
                line=dict(color="#00CC96", width=1.5),
                marker=dict(color="#00CC96", size=5),
                hovertemplate="Zeit: %{x} ms<br>HR: %{y:.1f} bpm<extra></extra>",
            ), row=2, col=1)

            # Gleitender Durchschnitt
            fig.add_trace(go.Scatter(
                x=hr_x, y=hr_rolling,
                mode="lines",
                name="Ø HR gleitend (5 Schläge)",
                line=dict(color="#FF7F0E", width=2.5, dash="solid"),
                hovertemplate="Ø HR: %{y:.1f} bpm<extra></extra>",
            ), row=2, col=1)

        if max_hr_line is not None:
            fig.add_hline(
                y=max_hr_line,
                row=2, col=1,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Max HR ({max_hr_line:.0f} bpm)",
                annotation_position="top right",
                annotation_font_color="red",
            )

        fig.update_layout(
            height=620,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1),
            margin=dict(t=60, b=40),
        )
        fig.update_xaxes(title_text="Zeit (ms)", row=2, col=1)
        fig.update_yaxes(title_text="mV", row=1, col=1)
        fig.update_yaxes(title_text="bpm", row=2, col=1)

        return fig

    def plot_time_series_with_peaks(self, threshold: float = 0.9) -> go.Figure:
        """Einfacher EKG-Plot mit markierten R-Peaks und Rangeslider.

        Args:
            threshold: Peak-Erkennungsschwelle.

        Returns:
            Plotly Figure.
        """
        df_plot = self._downsample(self.df)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_plot["Zeit in ms"],
            y=df_plot["Messwerte in mV"],
            mode="lines",
            name="EKG",
            line=dict(color="#636EFA", width=1),
        ))

        peak_times = self.find_peaks(threshold)
        peak_values = self.df["Messwerte in mV"][self.df["Zeit in ms"].isin(peak_times)]
        fig.add_trace(go.Scatter(
            x=peak_times, y=peak_values,
            mode="markers",
            name="R-Peaks",
            marker=dict(color="red", size=8),
        ))

        fig.update_layout(
            xaxis=dict(rangeslider=dict(visible=True)),
            xaxis_title="Zeit (ms)",
            yaxis_title="EKG-Signal (mV)",
            height=400,
        )
        return fig

    def plot_hr_over_time(self, threshold: float = 0.9,
                          max_hr_line: float = None) -> go.Figure:
        """Herzfrequenz-Verlauf über die Zeit mit gleitendem Durchschnitt.

        Args:
            threshold: Peak-Erkennungsschwelle.
            max_hr_line: Optionaler Grenzwert als gestrichelte Linie.

        Returns:
            Plotly Figure mit HR-Kurve und gleitendem Durchschnitt.
        """
        peak_times = self.find_peaks(threshold)
        if len(peak_times) < 2:
            return go.Figure()

        rr = peak_times.diff().dropna()
        rr = rr[rr > 0]
        if rr.empty:
            return go.Figure()

        hr_vals = 60_000 / rr
        x_vals = peak_times.loc[rr.index].values
        rolling = hr_vals.rolling(window=5, center=True).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_vals, y=hr_vals.values,
            mode="lines+markers",
            name="HR (bpm)",
            line=dict(color="#00CC96", width=1.5),
            marker=dict(size=5),
        ))
        fig.add_trace(go.Scatter(
            x=x_vals, y=rolling.values,
            mode="lines",
            name="Ø HR gleitend (5 Schläge)",
            line=dict(color="#FF7F0E", width=2.5),
        ))

        if max_hr_line is not None:
            fig.add_hline(
                y=max_hr_line,
                line_dash="dash", line_color="red",
                annotation_text=f"Max HR ({max_hr_line:.0f} bpm)",
                annotation_position="top right",
            )

        fig.update_layout(
            xaxis=dict(rangeslider=dict(visible=True)),
            xaxis_title="Zeit (ms)",
            yaxis_title="Herzfrequenz (bpm)",
            height=400,
        )
        return fig


if __name__ == "__main__":
    ekg = EKGdata({"id": 1, "date": "10.2.2023",
                   "result_link": "data/ekg_data/01_Ruhe.txt"})
    print("Peaks:", len(ekg.find_peaks()))
    print("Avg HR:", ekg.estimate_hr())
    print("Max HR:", ekg.max_hr())
