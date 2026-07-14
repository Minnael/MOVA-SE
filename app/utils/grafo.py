"""Utilitário de grafos para baixar, analisar e persistir malhas viárias do OpenStreetMap."""

from __future__ import annotations

from datetime import datetime
import os
import osmnx as ox
import networkx as nx


def configurar_osmnx() -> None:
    """Configura o OSMnx para baixar tags personalizadas adicionais."""
    tags_adicionais = ["lit", "sidewalk", "surface", "cycleway", "bicycle", "foot"]
    current_useful = list(ox.settings.useful_tags_way)
    new_tags = list(set(current_useful + tags_adicionais))
    ox.settings.useful_tags_way = new_tags


def determinar_periodo_dia(data_hora_iso: str) -> str:
    """Determina se a janela temporal representa o período do dia ou da noite.

    Retorna 'noite' se o horário estiver entre 18:00 e 05:59, caso contrário 'dia'.
    """
    try:
        dt = datetime.fromisoformat(data_hora_iso)
        if dt.hour >= 18 or dt.hour < 6:
            return "noite"
    except Exception as e:
        print(f"Erro ao analisar data_hora_iso '{data_hora_iso}': {e}. Assumindo 'dia'.")
    return "dia"


def configurar_e_baixar_grafo(lat: float, lon: float, raio_metros: int, modalidade: str) -> nx.MultiDiGraph:
    """Configura o OSMnx e baixa o grafo de ruas ao redor das coordenadas fornecidas.

    :param lat: Latitude do ponto de partida.
    :param lon: Longitude do ponto de partida.
    :param raio_metros: Raio de busca ao redor do ponto inicial em metros.
    :param modalidade: Modalidade da atividade física ('Corrida de Rua Pedestre' ou 'Ciclismo Urbano').
    """
    configurar_osmnx()

    # Define o tipo de rede com base na modalidade
    tipo_rede = "walk" if "Corrida" in modalidade else "bike"

    # Baixa o grafo viário usando OSMnx
    G = ox.graph_from_point((lat, lon), dist=raio_metros, network_type=tipo_rede)
    return G


def calcular_atributos_grafo(G: nx.MultiDiGraph, modalidade: str, periodo_dia: str) -> None:
    """Classifica cada aresta do grafo adicionando Se (risco) e Ie (infraestrutura).

    :param G: Grafo retornado pelo OSMnx (MultiDiGraph).
    :param modalidade: Modalidade da atividade física.
    :param periodo_dia: Período do dia ('dia' ou 'noite').
    """
    for u, v, k, data in G.edges(keys=True, data=True):
        # Pontuações iniciais
        Se = 0.0  # Risco Urbano
        Ie = 0.0  # Bônus de Infraestrutura

        # --- Auxiliares para lidar com tags que vêm como listas ---
        def contem_valor(tag_name: str, alvos: list[str]) -> bool:
            val = data.get(tag_name)
            if not val:
                return False
            if isinstance(val, list):
                return any(str(v).lower() in alvos for v in val)
            return str(val).lower() in alvos

        # 1. Análise de Risco Urbano (Se)
        # Se for noite e a via não for iluminada (ausência de lit=yes)
        is_lit = contem_valor("lit", ["yes", "true", "1"])
        if periodo_dia == "noite" and not is_lit:
            Se += 0.5

        # Vias arteriais expressas são mais arriscadas para atividades físicas
        vias_expressas = ["primary", "secondary", "trunk", "motorway"]
        if contem_valor("highway", vias_expressas):
            Se += 0.4

        # 2. Análise de Bônus de Infraestrutura (Ie)
        if "Corrida" in modalidade:
            # Calçadas ou vias exclusivas para pedestres
            is_pedestrian = contem_valor("highway", ["pedestrian", "footway", "path", "steps"])
            has_sidewalk = contem_valor("sidewalk", ["yes", "both", "left", "right"])
            if is_pedestrian:
                Ie += 0.8
            elif has_sidewalk:
                Ie += 0.4
        elif "Ciclismo" in modalidade:
            # Presença de ciclovias ou ciclofaixas
            has_cycleway = contem_valor("cycleway", ["yes", "lane", "track", "opposite_lane", "opposite_track", "share_busway"])
            is_designated_bike = contem_valor("bicycle", ["designated", "yes"])
            if has_cycleway or is_designated_bike:
                Ie += 0.8

        # Pavimentação de alta qualidade
        surface_lisa = ["asphalt", "concrete", "paved", "tarmac"]
        if contem_valor("surface", surface_lisa):
            Ie += 0.2

        # Limitar pontuações no intervalo [0.0, 1.0]
        data["Se"] = min(max(Se, 0.0), 1.0)
        data["Ie"] = min(max(Ie, 0.0), 1.0)
