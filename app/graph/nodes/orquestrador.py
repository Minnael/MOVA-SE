"""Nó do Agente 1 — Orquestrador / Engenheiro de Requisitos.

Responsável por fazer o *parsing* do texto livre do usuário e transformá-lo em
requisitos estruturados para os agentes subordinados.

MOCK: por ora o nó ignora o texto e devolve requisitos fixos. A extração real
(parsing via LLM) e a definição final dos campos virão em seguida.
"""

from __future__ import annotations

from app.graph.state import EstadoAgentico, RequisitosRota


def extrair_requisitos(estado: EstadoAgentico) -> dict:
    """Extrai os requisitos da rota a partir do texto de entrada.

    Args:
        estado: estado agêntico contendo ``texto_entrada``.

    Returns:
        Atualização parcial do estado com a chave ``requisitos``.
    """
    # TODO: substituir o mock por extração real (LLM) a partir de
    # ``estado["texto_entrada"]``.
    requisitos_mock: RequisitosRota = {
        "ponto_partida": "-23.5505, -46.6333",
        "distancia_alvo_km": 12.0,
        "perfil_altimetria": "Moderado",
        "janela_temporal": "2026-07-19T07:00",
        "modalidade": "Corrida de Rua Pedestre",
    }
    return {"requisitos": requisitos_mock}
