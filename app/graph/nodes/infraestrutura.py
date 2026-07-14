"""Nó do Agente 3 — Analista de Infraestrutura e Segurança Urbana.

Responsável por obter o grafo viário correspondente à região de partida,
classificar cada via quanto ao seu risco de segurança e nível de infraestrutura,
e salvar o grafo em formato GraphML para o motor matemático de rotas.
"""

from __future__ import annotations

import os
import osmnx as ox
import networkx as nx

from app.graph.state import EstadoAgentico
from app.utils.grafo import (
    calcular_atributos_grafo,
    configurar_e_baixar_grafo,
    determinar_periodo_dia,
)


def analisar_infraestrutura(estado: EstadoAgentico) -> dict:
    """Baixa o grafo de ruas local, anota as vias com Se e Ie, e salva o arquivo GraphML.

    Args:
        estado: estado agêntico contendo `coordenadas` e `requisitos`.

    Returns:
        Atualização parcial do estado com a chave `caminho_grafo`.
    """
    coordenadas = estado.get("coordenadas")
    requisitos = estado.get("requisitos")

    if not coordenadas or not requisitos:
        raise ValueError("Coordenadas ou requisitos não definidos no estado.")

    lat, lon = coordenadas
    distancia_alvo = requisitos["distancia_alvo_km"]
    modalidade = requisitos["modalidade"]
    janela_temporal = requisitos["janela_temporal"]

    # Heurística para estimar raio de busca viária (em metros) com base na distância-alvo
    # Exemplo: 10km -> ~3300 metros de raio (3.3km)
    raio_metros = int(max(1000.0, min(5000.0, (distancia_alvo * 1000.0) / 3.0)))

    # Determinar período do dia para cálculo de risco de iluminação
    periodo_dia = determinar_periodo_dia(janela_temporal)

    print(f"Agente 3: Baixando rede '{modalidade}' em um raio de {raio_metros}m...")

    try:
        # 1. Download do Grafo real da API Overpass
        G = configurar_e_baixar_grafo(lat, lon, raio_metros, modalidade)
        print(f"Agente 3: Grafo baixado com {len(G.nodes)} nós e {len(G.edges)} arestas.")
    except Exception as e:
        print(f"Alerta: Falha ao obter grafo do OSM ({e}). Utilizando grafo mock para testes.")
        # Fallback local para desenvolvimento ágil offline
        G = nx.MultiDiGraph()
        # Nó de origem
        G.add_node(1, y=lat, x=lon)
        # Nó de destino simulado a 1km de distância
        # ~0.009 graus de latitude equivalem a ~1km
        G.add_node(2, y=lat + 0.009, x=lon + 0.009)
        # Arestas de ida e volta
        G.add_edge(1, 2, key=0, length=1414.0, highway="residential", lit="no")
        G.add_edge(2, 1, key=0, length=1414.0, highway="residential", lit="no")

    # 2. Computar Se e Ie para cada via do grafo
    calcular_atributos_grafo(G, modalidade, periodo_dia)

    # 3. Salvar o grafo em arquivo GraphML no workspace
    pasta_data = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
    )
    os.makedirs(pasta_data, exist_ok=True)
    caminho_arquivo = os.path.join(pasta_data, "grafo_local.graphml")

    print(f"Agente 3: Gravando grafo anotado em: {caminho_arquivo}")
    ox.save_graphml(G, filepath=caminho_arquivo)

    return {"caminho_grafo": caminho_arquivo}
