"""Nó do Agente 1 — Orquestrador / Engenheiro de Requisitos.

Responsável por consolidar (fan-in) os campos extraídos pelos nós de extração
paralelos em um único dicionário de requisitos estruturados que alimenta os
agentes subordinados.

Por ora dois campos do contrato (``perfil_altimetria`` e ``modalidade``) seguem
mocados, até que sua entrada/extração seja definida.
"""

from __future__ import annotations

from app.graph.state import EstadoAgentico, RequisitosRota
from app.utils.geocoding import obter_coordenadas


def consolidar_requisitos(estado: EstadoAgentico) -> dict:
    """Consolida os campos extraídos em ``requisitos`` e realiza a geocodificação.

    Args:
        estado: estado agêntico contendo ``lugar``, ``distancia_alvo_km`` e
            ``horario_inicio`` (produzidos pelos nós de extração).

    Returns:
        Atualização parcial do estado com as chaves ``requisitos`` e ``coordenadas``.
    """
    lugar = estado["lugar"]
    coordenadas = obter_coordenadas(lugar)

    # Suporta data e hora separadas ou combinadas no formato ISO 8601
    data = estado.get("data_inicio")
    hora = estado.get("hora_inicio")
    if data and hora:
        janela_temporal = f"{data}T{hora}"
    else:
        # Se vier apenas a string combinada ou fallback padrão
        janela_temporal = estado.get("horario_inicio", "2026-07-19T07:00")

    requisitos: RequisitosRota = {
        "ponto_partida": lugar,
        "distancia_alvo_km": estado["distancia_alvo_km"],
        "janela_temporal": janela_temporal,
        # TODO: ainda mocados; virão de entrada/extração em seguida.
        "perfil_altimetria": "Moderado",
        "modalidade": "Corrida de Rua Pedestre",
    }
    return {"requisitos": requisitos, "coordenadas": coordenadas}
