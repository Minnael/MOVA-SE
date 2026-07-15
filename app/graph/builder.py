"""Construção do grafo de orquestração (LangGraph).

Por enquanto o grafo tem três nós de extração que rodam em paralelo a partir do
START (lugar, distância, horário); o ramo do lugar ainda geocodifica o nome em
coordenadas antes de convergirem no Orquestrador, que consolida os resultados.
Os demais agentes (meteorológico, infraestrutura, redes, comunicador) serão
adicionados como novos nós e arestas conforme o desenvolvimento avançar.
"""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from app.graph.nodes.extratores import (
    extrair_distancia,
    extrair_horario,
    extrair_lugar,
)
from app.graph.nodes.infraestrutura import analisar_infraestrutura
from app.graph.nodes.meteorologia import analisar_clima
from app.graph.nodes.geocoordinates_getter import geocodificar
from app.graph.nodes.geocoordinates_fallback import buscar_coordenadas_internet
from app.graph.nodes.orquestrador import consolidar_requisitos
from app.graph.nodes.comunicador import redigir_relatorio
from app.graph.state import EstadoAgentico

logger = logging.getLogger(__name__)


def _roteador_geocodificacao(estado: EstadoAgentico) -> str:
    """Roteia após ``geocodificar``: se achou coordenadas segue direto ao
    orquestrador; caso contrário desvia ao nó de fallback (busca na internet)."""
    if isinstance(estado.get("coordenadas"), tuple):
        logger.info("[roteador] Coordenadas encontradas na caixa -> orquestrador")
        return "orquestrador"
    logger.info("[roteador] Sem coordenadas na caixa -> geocodificar_fallback")
    return "geocodificar_fallback"


def construir_grafo():
    """Monta e compila o grafo agêntico."""
    grafo = StateGraph(EstadoAgentico)

    grafo.add_node("extrair_lugar", extrair_lugar)
    grafo.add_node("geocodificar", geocodificar)
    grafo.add_node("geocodificar_fallback", buscar_coordenadas_internet)
    grafo.add_node("extrair_distancia", extrair_distancia)
    grafo.add_node("extrair_horario", extrair_horario)
    grafo.add_node("orquestrador", consolidar_requisitos, defer=True)
    grafo.add_node("analista_meteorologico", analisar_clima)
    grafo.add_node("analista_infraestrutura", analisar_infraestrutura)
    grafo.add_node("comunicador", redigir_relatorio)

    # Fan-out: os três extratores rodam em paralelo a partir do START.
    grafo.add_edge(START, "extrair_lugar")
    grafo.add_edge(START, "extrair_distancia")
    grafo.add_edge(START, "extrair_horario")
    # O lugar extraído é geocodificado antes de chegar ao Orquestrador.
    grafo.add_edge("extrair_lugar", "geocodificar")
    # Se a geocodificação restrita à caixa falhar, desvia ao fallback (busca
    # ampla na internet + validação da caixa); senão segue ao Orquestrador.
    grafo.add_conditional_edges(
        "geocodificar",
        _roteador_geocodificacao,
        ["orquestrador", "geocodificar_fallback"],
    )
    grafo.add_edge("geocodificar_fallback", "orquestrador")
    # Fan-in: o Orquestrador só executa após os três ramos terminarem.
    grafo.add_edge("extrair_distancia", "orquestrador")
    grafo.add_edge("extrair_horario", "orquestrador")
    
    # Fan-out paralelo: Orquestrador conecta com o Analista Meteorológico e o Analista de Infraestrutura
    grafo.add_edge("orquestrador", "analista_meteorologico")
    grafo.add_edge("orquestrador", "analista_infraestrutura")
    
    # Fan-in: Ambos convergem ao Comunicador
    grafo.add_edge("analista_meteorologico", "comunicador")
    grafo.add_edge("analista_infraestrutura", "comunicador")
    
    # Comunicador encerra o fluxo
    grafo.add_edge("comunicador", END)

    return grafo.compile()
