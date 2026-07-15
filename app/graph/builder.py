"""Construção do grafo de orquestração (LangGraph).

Por enquanto o grafo tem três nós de extração que rodam em paralelo a partir do
START (lugar, distância, horário); o ramo do lugar ainda geocodifica o nome em
coordenadas antes de convergirem no Orquestrador, que consolida os resultados.
Os demais agentes (meteorológico, infraestrutura, redes, comunicador) serão
adicionados como novos nós e arestas conforme o desenvolvimento avançar.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.nodes.extratores import (
    extrair_distancia,
    extrair_horario,
    extrair_lugar,
)
from app.graph.nodes.infraestrutura import analisar_infraestrutura
from app.graph.nodes.meteorologia import analisar_clima
from app.graph.nodes.geocoordinates_getter import geocodificar
from app.graph.nodes.orquestrador import consolidar_requisitos
from app.graph.nodes.comunicador import redigir_relatorio
from app.graph.state import EstadoAgentico


def construir_grafo():
    """Monta e compila o grafo agêntico."""
    grafo = StateGraph(EstadoAgentico)

    grafo.add_node("extrair_lugar", extrair_lugar)
    grafo.add_node("geocodificar", geocodificar)
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
    # Fan-in: o Orquestrador só executa após os três ramos terminarem.
    grafo.add_edge("geocodificar", "orquestrador")
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
