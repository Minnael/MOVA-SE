"""Utilitário de geocodificação para conversão de endereços textuais em coordenadas (lat, lon)."""

from __future__ import annotations

import logging
import re
import requests

logger = logging.getLogger(__name__)

_RE_COORDENADAS = re.compile(r"^\s*([-+]?\d+\.\d+)\s*,\s*([-+]?\d+\.\d+)\s*$")

# Bounding box delimitador da região atendida (Natal/RN) — fonte da verdade única.
# Formato: (lat_min, lat_max, lon_min, lon_max).
BBOX = (-6.023117, -5.646052, -35.459747, -35.088959)


def dentro_do_bbox(lat: float, lon: float) -> bool:
    """Indica se a coordenada (lat, lon) está dentro do bounding box atendido."""
    lat_min, lat_max, lon_min, lon_max = BBOX
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


def obter_coordenadas(lugar: str) -> tuple[float, float] | None:
    """Resolve o nome do lugar para coordenadas (lat, lon).

    Se a string já estiver no formato "lat, lon", faz o parsing diretamente.
    Caso contrário, consulta a API pública Nominatim do OpenStreetMap (busca
    ampla, **sem** restrição de bounding box). Retorna ``None`` quando o lugar
    não é encontrado ou quando ocorre erro/timeout na requisição — cabe ao
    chamador decidir o fallback (ex.: validar contra o bounding box).
    """
    match = _RE_COORDENADAS.match(lugar)
    if match:
        coords = float(match.group(1)), float(match.group(2))
        logger.debug("Coordenada literal detectada em %r -> %s", lugar, coords)
        return coords

    try:
        url = "https://nominatim.openstreetmap.org/search"
        headers = {"User-Agent": "mova-se-routing-agent"}
        params = {"q": lugar, "format": "json", "limit": 1}

        logger.info("Consultando Nominatim: %r", lugar)
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            coords = float(data["lat"]), float(data["lon"])
            logger.info("Nominatim retornou %s para %r", coords, lugar)
            return coords
        logger.warning("Nominatim sem resultados para %r (status %s)", lugar, response.status_code)
    except Exception as e:
        # Registra o erro internamente e sinaliza falha ao chamador.
        logger.error("Erro ao geocodificar %r: %s", lugar, e)

    return None
