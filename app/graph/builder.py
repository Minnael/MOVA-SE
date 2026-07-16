"""Construção do grafo de orquestração (LangGraph).

Por enquanto o grafo tem três nós de extração que rodam em paralelo a partir do
START (lugar, distância, horário); o ramo do lugar já geocodifica o nome em
coordenadas internamente, antes de convergirem no Orquestrador, que consolida
os resultados.
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
from app.graph.nodes.orquestrador import consolidar_requisitos
from app.graph.nodes.roteamento import aplicar_motor_roteamento
from app.graph.nodes.comunicador import redigir_relatorio
from app.graph.state import EstadoAgentico

logger = logging.getLogger(__name__)



def construir_grafo():
    """Monta e compila o grafo agêntico."""
    grafo = StateGraph(EstadoAgentico)

    grafo.add_node("extrair_lugar", extrair_lugar)

    grafo.add_node("extrair_distancia", extrair_distancia)
    grafo.add_node("extrair_horario", extrair_horario)
    grafo.add_node("orquestrador", consolidar_requisitos)
    grafo.add_node("analista_meteorologico", analisar_clima)
    grafo.add_node("analista_infraestrutura", analisar_infraestrutura)
    grafo.add_node("comunicador", redigir_relatorio)

    # Fan-out: os três extratores rodam em paralelo a partir do START.
    grafo.add_edge(START, "extrair_lugar")
    grafo.add_edge(START, "extrair_distancia")
    grafo.add_edge(START, "extrair_horario")
    
    # Fan-in: o Orquestrador só executa após os TRÊS ramos terminarem.
    grafo.add_edge("extrair_lugar", "orquestrador")
    grafo.add_edge("extrair_distancia", "orquestrador")
    grafo.add_edge("extrair_horario", "orquestrador")
    
    # Fan-out paralelo: Orquestrador conecta com o Analista Meteorológico e o Analista de Infraestrutura
    grafo.add_edge("orquestrador", "analista_meteorologico")
    grafo.add_edge("orquestrador", "analista_infraestrutura")
    
    # Fan-in 1: Ambos convergem ao Motor de Roteamento (Agente 4)
    grafo.add_node("motor_roteamento", aplicar_motor_roteamento)
    grafo.add_edge("analista_meteorologico", "motor_roteamento")
    grafo.add_edge("analista_infraestrutura", "motor_roteamento")
    
    # Linear: Motor de Roteamento conecta ao Comunicador (Agente 5)
    grafo.add_edge("motor_roteamento", "comunicador")
    
    # Comunicador encerra o fluxo
    grafo.add_edge("comunicador", END)

    return grafo.compile()
