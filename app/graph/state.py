"""Estado agêntico — o "barramento de contexto" que trafega pelo grafo.

Cada nó (agente) lê e escreve neste estado compartilhado. Por enquanto ele
carrega apenas o texto de entrada e os requisitos extraídos pelo Orquestrador.
Conforme os demais agentes forem implementados, novos campos serão adicionados
(fatores meteorológicos, características viárias, rota calculada, etc.).
"""

from __future__ import annotations

from typing import TypedDict


class RequisitosRota(TypedDict, total=False):
    """Requisitos estruturados extraídos do texto livre do usuário.

    PROVISÓRIO: os campos abaixo são um placeholder baseado no contrato de
    entrada do documento de diretrizes. Ainda vamos definir quais informações
    realmente importam para o roteamento.
    """

    ponto_partida: str  # coordenadas "lat, lon" ou endereço para geocoding
    distancia_alvo_km: float
    perfil_altimetria: str  # "Plano" | "Moderado" | "Montanhoso"
    janela_temporal: str  # data/hora ISO 8601 do evento
    modalidade: str  # "Corrida de Rua Pedestre" | "Ciclismo Urbano"


class EstadoAgentico(TypedDict):
    """Estado compartilhado entre os nós do grafo."""

    texto_entrada: str
    requisitos: RequisitosRota | None
