"""Demand-Forecaster [CRUX-MK].

Time-Series-Forecast mit Saisonalitaet + Events.

Phase-1 Skeleton: Heuristik-basiert (Saisonalitaet-Lookup + Event-Boost).
Phase-2: ARIMA / Prophet / Bayesian-Structural-Time-Series.

Lambda-Honesty-Caveat: Saisonalitaets-Lookup ist statisches Pattern,
nicht durch Hotel-spezifische historische Daten kalibriert.

[CRUX-MK]
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


# Statische Saisonalitaets-Pattern fuer DE-Hotels (Phase-1)
# Phase-2: pro-Hotel-Kalibration + Wetter-Integration
SEASONALITY_MONTH = {
    1: 0.7, 2: 0.7, 3: 0.85, 4: 0.95, 5: 1.05, 6: 1.15,
    7: 1.25, 8: 1.25, 9: 1.10, 10: 1.05, 11: 0.85, 12: 1.0,  # Dezember: Weihnachten-Spike
}

SEASONALITY_WEEKDAY = {
    0: 0.95,  # Montag
    1: 0.90,  # Dienstag
    2: 0.95,  # Mittwoch
    3: 1.05,  # Donnerstag
    4: 1.20,  # Freitag
    5: 1.15,  # Samstag
    6: 0.85,  # Sonntag
}


@dataclass
class DemandForecast:
    """Demand-Forecast fuer ein Datum + Hotel."""
    hotel_id: str
    forecast_date: str  # ISO YYYY-MM-DD
    demand_signal: float  # >1.0 high, <1.0 low
    saisonal_component: float
    weekday_component: float
    event_boost: float
    notes: list[str]


class DemandForecaster:
    """Time-Series-Forecast mit Saisonalitaet + Events.

    Phase-1: Multiplikatives Modell (Saison * Weekday * Event-Boost).
    """

    def __init__(self):
        self._events: dict[str, list[dict]] = {}  # hotel_id -> [{date, boost_factor, name}]

    def register_event(
        self,
        hotel_id: str,
        date_iso: str,
        boost_factor: float,
        event_name: str,
    ) -> None:
        """Event registrieren (z.B. Messe, Konzert, lokales Festival).

        Args:
            boost_factor: 1.0 = kein Effekt, 1.5 = +50% Demand, 2.0 = Verdopplung
        """
        if boost_factor < 0.5 or boost_factor > 3.0:
            raise ValueError(f"boost_factor out of range: {boost_factor}")
        if hotel_id not in self._events:
            self._events[hotel_id] = []
        self._events[hotel_id].append({
            "date": date_iso,
            "boost": boost_factor,
            "name": event_name,
        })

    def forecast(
        self,
        hotel_id: str,
        forecast_date_iso: str,
    ) -> DemandForecast:
        """Forecast fuer Datum.

        Decomposition: demand = saisonal * weekday * event_boost.
        """
        dt = datetime.fromisoformat(forecast_date_iso)
        season = SEASONALITY_MONTH.get(dt.month, 1.0)
        weekday = SEASONALITY_WEEKDAY.get(dt.weekday(), 1.0)

        # Event-Lookup
        event_boost = 1.0
        notes = []
        for event in self._events.get(hotel_id, []):
            if event["date"] == forecast_date_iso:
                event_boost *= event["boost"]
                notes.append(f"event:{event['name']}+{(event['boost']-1)*100:.0f}%")

        demand = season * weekday * event_boost

        return DemandForecast(
            hotel_id=hotel_id,
            forecast_date=forecast_date_iso,
            demand_signal=round(demand, 3),
            saisonal_component=season,
            weekday_component=weekday,
            event_boost=event_boost,
            notes=notes,
        )
