from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

def obter_coordenadas(nome_local):
    # O Nominatim exige um user_agent único para identificar quem está fazendo a requisição.
    geolocator = Nominatim(user_agent="app_pesquisa_espacial")
    
    try:
        # Faz a busca pelo nome do local
        localizacao = geolocator.geocode(nome_local)
        
        if localizacao:
            return localizacao.latitude, localizacao.longitude
        else:
            return None
            
    except GeocoderTimedOut:
        return "Erro: Tempo de limite da requisição excedido."