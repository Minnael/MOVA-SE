"""Construção do grafo de orquestração (LangGraph).

Por enquanto o grafo tem três nós de extração que rodam em paralelo a partir do
START (lugar, distância, horário) e convergem no Orquestrador, que consolida os
resultados. Os demais agentes (meteorológico, infraestrutura, redes, comunicador)
serão adicionados como novos nós e arestas conforme o desenvolvimento avançar.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.nodes.extratores import (
    extrair_distancia,
    extrair_horario,
    extrair_lugar,
)
from app.graph.nodes.meteorologia import analisar_clima
from app.graph.nodes.orquestrador import consolidar_requisitos
from app.graph.state import EstadoAgentico


def construir_grafo():
    """Monta e compila o grafo agêntico."""
    grafo = StateGraph(EstadoAgentico)

    grafo.add_node("extrair_lugar", extrair_lugar)
    grafo.add_node("extrair_distancia", extrair_distancia)
    grafo.add_node("extrair_horario", extrair_horario)
    grafo.add_node("orquestrador", consolidar_requisitos)
    grafo.add_node("analista_meteorologico", analisar_clima)

    # Fan-out: os três extratores rodam em paralelo a partir do START.
    grafo.add_edge(START, "extrair_lugar")
    grafo.add_edge(START, "extrair_distancia")
    grafo.add_edge(START, "extrair_horario")
    # Fan-in: o Orquestrador só executa após os três terminarem.
    grafo.add_edge("extrair_lugar", "orquestrador")
    grafo.add_edge("extrair_distancia", "orquestrador")
    grafo.add_edge("extrair_horario", "orquestrador")
    
    # Orquestrador conecta com o Analista Meteorológico (que rodará em paralelo com o de infraestrutura futuramente)
    grafo.add_edge("orquestrador", "analista_meteorologico")
    grafo.add_edge("analista_meteorologico", END)

    return grafo.compile()
