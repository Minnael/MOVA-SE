"""Nó do Agente 1 — Orquestrador / Engenheiro de Requisitos.

Responsável por consolidar os requisitos estruturados que alimentam os agentes
subordinados.

Por ora o nó apenas valida e repassa os campos já estruturados vindos do payload
da API (``ponto_partida`` e ``distancia_alvo_km``); os três campos restantes
seguem mocados até a definição da entrada/extração final.
"""

from __future__ import annotations

from app.graph.state import EstadoAgentico, RequisitosRota


def extrair_requisitos(estado: EstadoAgentico) -> dict:
    """Consolida os requisitos da rota a partir do estado de entrada.

    Args:
        estado: estado agêntico contendo ``ponto_partida`` e
            ``distancia_alvo_km`` (vindos do payload da API).

    Returns:
        Atualização parcial do estado com a chave ``requisitos``.
    """
    # TODO: os três campos abaixo ainda são mocados; virão de entrada/extração
    # (parsing via LLM) em seguida.
    requisitos: RequisitosRota = {
        "ponto_partida": estado["ponto_partida"],
        "distancia_alvo_km": estado["distancia_alvo_km"],
        "perfil_altimetria": "Moderado",
        "janela_temporal": "2026-07-19T07:00",
        "modalidade": "Corrida de Rua Pedestre",
    }
    return {"requisitos": requisitos}
