"""Construção do grafo de orquestração (LangGraph).

Por enquanto o grafo tem um único nó — o Orquestrador. Os demais agentes
(meteorológico, infraestrutura, redes, comunicador) serão adicionados como
novos nós e arestas conforme o desenvolvimento avançar.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.graph.nodes.orquestrador import extrair_requisitos
from app.graph.state import EstadoAgentico


def construir_grafo():
    """Monta e compila o grafo agêntico."""
    grafo = StateGraph(EstadoAgentico)

    grafo.add_node("orquestrador", extrair_requisitos)

    grafo.add_edge(START, "orquestrador")
    grafo.add_edge("orquestrador", END)

    return grafo.compile()
