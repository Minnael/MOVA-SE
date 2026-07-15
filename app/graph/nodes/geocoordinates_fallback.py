"""Nó de fallback de geocodificação.

Aciona quando o nó primário (``geocodificar``, restrito ao bounding box via
``bounded=True``) não encontra o lugar. Faz uma busca na internet **restrita ao
Rio Grande do Norte** (anexando o contexto regional à consulta) e valida
manualmente se a coordenada encontrada está dentro do bounding box da região
atendida. Se cair fora — ou se nada for encontrado — levanta ``ValueError``
(capturado em ``app/api.py`` → 422).
"""

from __future__ import annotations

import logging

from app.graph.state import EstadoAgentico
from app.utils.geocoding import _RE_COORDENADAS, dentro_do_bbox, obter_coordenadas

logger = logging.getLogger(__name__)

# Contexto regional anexado à consulta para restringir a busca ao RN.
_CONTEXTO_RN = "Rio Grande do Norte, Brasil"


def buscar_coordenadas_internet(estado: EstadoAgentico) -> dict:
    """Busca restrita ao RN na internet + validação contra o bounding box atendido."""
    lugar = estado["lugar"]
    # Anexa o estado à consulta para restringir ao RN — exceto quando o "lugar"
    # já é uma coordenada "lat, lon" (nesse caso a busca resolve direto).
    if _RE_COORDENADAS.match(lugar) or _CONTEXTO_RN.lower() in lugar.lower():
        consulta = lugar
    else:
        consulta = f"{lugar}, {_CONTEXTO_RN}"

    logger.info("[fallback] Buscando na internet (restrito ao RN): %r", consulta)
    resultado = obter_coordenadas(consulta)  # busca restrita ao RN

    if resultado is None:
        logger.error("[fallback] %r não encontrado na internet", lugar)
        raise ValueError(f"Lugar não encontrado na internet: {lugar!r}")

    lat, lon = resultado
    if not dentro_do_bbox(lat, lon):
        logger.error(
            "[fallback] %r resolvido para %s, mas FORA do bounding box atendido",
            lugar, resultado,
        )
        raise ValueError(
            f"Lugar fora da região atendida (bounding box): {lugar!r} -> {resultado}"
        )

    logger.info("[fallback] %r resolvido para %s (dentro da caixa)", lugar, resultado)
    return {"coordenadas": resultado}
