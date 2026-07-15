"""Utilitário de clima para consulta da API pública Open-Meteo."""

from __future__ import annotations

from datetime import datetime
import requests


def consultar_open_meteo(lat: float, lon: float, data_hora_iso: str) -> dict:
    """Busca a previsão meteorológica horária na API Open-Meteo.

    Retorna temperatura, probabilidade de chuva, índice UV e velocidade do vento
    para o horário mais próximo ao solicitado no formato ISO.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "precipitation_probability", "uv_index", "wind_speed_10m"],
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    # Encontra o índice da previsão mais próxima do horário solicitado
    target_dt = datetime.fromisoformat(data_hora_iso)
    times = [datetime.fromisoformat(t) for t in data["hourly"]["time"]]
    closest_idx = min(range(len(times)), key=lambda i: abs((times[i] - target_dt).total_seconds()))

    return {
        "temperatura": data["hourly"]["temperature_2m"][closest_idx],
        "chuva_probabilidade": data["hourly"]["precipitation_probability"][closest_idx],
        "indice_uv": data["hourly"]["uv_index"][closest_idx],
        "velocidade_vento": data["hourly"]["wind_speed_10m"][closest_idx],
    }
