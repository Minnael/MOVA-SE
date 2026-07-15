import logging

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

from app.graph.state import EstadoAgentico
from app.utils.geocoding import BBOX

logger = logging.getLogger(__name__)

# Bounding box da região atendida (Natal/RN) — derivado da fonte única em
# ``app.utils.geocoding.BBOX``. geopy espera dois cantos opostos (lat, lon).
_LAT_MIN, _LAT_MAX, _LON_MIN, _LON_MAX = BBOX
_VIEWBOX = [(_LAT_MIN, _LON_MIN), (_LAT_MAX, _LON_MAX)]


def obter_coordenadas(nome_local):
    # O Nominatim exige um user_agent único para identificar quem está fazendo a requisição.
    geolocator = Nominatim(user_agent="app_pesquisa_espacial")

    try:
        # Faz a busca pelo nome do local, restrita à bounding box.
        logger.debug("Geocodificando (bounded=True) na caixa %s: %r", _VIEWBOX, nome_local)
        localizacao = geolocator.geocode(nome_local, viewbox=_VIEWBOX, bounded=True)

        if localizacao:
            return localizacao.latitude, localizacao.longitude
        else:
            return None

    except GeocoderTimedOut:
        logger.warning("Timeout na geocodificação de %r", nome_local)
        return "Erro: Tempo de limite da requisição excedido."


def geocodificar(estado: EstadoAgentico) -> dict:
    """Nó do grafo: geocodifica ``lugar`` em coordenadas (lat, lon).

    Busca restrita ao bounding box (``bounded=True``). Quando não encontra o
    lugar dentro da caixa, retorna ``{"coordenadas": None}`` em vez de abortar,
    para que o roteador do grafo desvie ao nó de fallback (busca ampla na
    internet + validação da caixa).
    """
    lugar = estado["lugar"]
    logger.info("[geocodificar] Buscando %r dentro do bounding box (bounded=True)", lugar)
    resultado = obter_coordenadas(lugar)
    if not isinstance(resultado, tuple):  # None (não encontrado) ou string de erro
        logger.warning(
            "[geocodificar] %r não encontrado na caixa — desviando ao fallback (busca no RN)",
            lugar,
        )
        return {"coordenadas": None}
    logger.info("[geocodificar] %r resolvido para %s", lugar, resultado)
    return {"coordenadas": resultado}