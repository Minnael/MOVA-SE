"""Nó do Agente 1 — Orquestrador / Engenheiro de Requisitos.

Responsável por consolidar (fan-in) os campos extraídos pelos nós de extração
paralelos em um único dicionário de requisitos estruturados que alimenta os
agentes subordinados.

Por ora dois campos do contrato (``perfil_altimetria`` e ``modalidade``) seguem
mocados, até que sua entrada/extração seja definida.
"""

from __future__ import annotations

from app.graph.state import EstadoAgentico, RequisitosRota


def consolidar_requisitos(estado: EstadoAgentico) -> dict:
    """Consolida os campos extraídos em ``requisitos``.

    Args:
        estado: estado agêntico contendo ``lugar``, ``distancia_alvo_km`` e
            ``horario_inicio`` (produzidos pelos nós de extração).

    Returns:
        Atualização parcial do estado com a chave ``requisitos``.
    """
    requisitos: RequisitosRota = {
        "ponto_partida": estado["lugar"],
        "distancia_alvo_km": estado["distancia_alvo_km"],
        "janela_temporal": estado["horario_inicio"],
        # TODO: ainda mocados; virão de entrada/extração em seguida.
        "perfil_altimetria": "Moderado",
        "modalidade": "Corrida de Rua Pedestre",
    }
    return {"requisitos": requisitos}
