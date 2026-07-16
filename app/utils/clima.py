"""Utilitário de clima para consulta da API pública Open-Meteo."""

from __future__ import annotations

import logging
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


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

    logger.info("Consultando Open-Meteo em (%s, %s) para %s", lat, lon, data_hora_iso)
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Encontra o índice da previsão mais próxima do horário solicitado
        target_dt = datetime.fromisoformat(data_hora_iso)
        times = [datetime.fromisoformat(t) for t in data["hourly"]["time"]]
        closest_idx = min(range(len(times)), key=lambda i: abs((times[i] - target_dt).total_seconds()))

        previsao = {
            "temperatura": data["hourly"]["temperature_2m"][closest_idx],
            "chuva_probabilidade": data["hourly"]["precipitation_probability"][closest_idx],
            "indice_uv": data["hourly"]["uv_index"][closest_idx],
            "velocidade_vento": data["hourly"]["wind_speed_10m"][closest_idx],
        }
        logger.info("Open-Meteo (%s): %s", data["hourly"]["time"][closest_idx], previsao)
        return previsao
        
    except requests.exceptions.RequestException as e:
        logger.warning("Falha ao consultar Open-Meteo (%s). Usando dados climáticos de fallback.", e)
        return {
            "temperatura": 26.0,
            "chuva_probabilidade": 10,
            "indice_uv": 4.0,
            "velocidade_vento": 12.0,
        }
