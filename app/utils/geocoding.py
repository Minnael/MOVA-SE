"""Utilitário de geocodificação para conversão de endereços textuais em coordenadas (lat, lon)."""

from __future__ import annotations

import re
import requests

_RE_COORDENADAS = re.compile(r"^\s*([-+]?\d+\.\d+)\s*,\s*([-+]?\d+\.\d+)\s*$")


def obter_coordenadas(lugar: str) -> tuple[float, float]:
    """Resolve o nome do lugar para coordenadas (lat, lon).

    Se a string já estiver no formato "lat, lon", faz o parsing diretamente.
    Caso contrário, consulta a API pública Nominatim do OpenStreetMap.
    Se a API falhar ou ocorrer um timeout, retorna a coordenada padrão
    (centro de São Paulo: -23.5505, -46.6333) como fallback seguro.
    """
    match = _RE_COORDENADAS.match(lugar)
    if match:
        return float(match.group(1)), float(match.group(2))

    try:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "mova-se-routing-agent"}
        params = {"q": lugar, "format": "json", "limit": 1}

        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            return float(data["lat"]), float(data["lon"])
    except Exception as e:
        # Registra o erro internamente e segue para o fallback
        print(f"Erro ao geocodificar '{lugar}': {e}")

    # Fallback seguro (Centro de São Paulo)
    return -23.5505, -46.6333
