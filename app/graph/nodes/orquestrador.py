"""Nó do Agente 1 — Orquestrador / Engenheiro de Requisitos.

Responsável por consolidar (fan-in) os campos extraídos pelos nós de extração
paralelos em um único dicionário de requisitos estruturados que alimenta os
agentes subordinados.

Por ora dois campos do contrato (``perfil_altimetria`` e ``modalidade``) seguem
mocados, até que sua entrada/extração seja definida.
"""

from __future__ import annotations

import logging

from app.graph.state import EstadoAgentico, RequisitosRota

logger = logging.getLogger(__name__)


def consolidar_requisitos(estado: EstadoAgentico) -> dict:
    """Consolida os campos extraídos em ``requisitos``.

    Args:
        estado: estado agêntico contendo ``coordenadas``, ``distancia_alvo_km``,
            ``data_inicio`` e ``horario_inicio`` (produzidos pelos nós de extração).

    Returns:
        Atualização parcial do estado com as chaves ``requisitos``.
    """
    # Combina data e hora (estados separados) em uma janela temporal ISO 8601:
    # datetime quando há hora, apenas a data quando ela está ausente.
    logger.info("[orquestrador] Consolidando requisitos (fan-in)")
    data = estado.get("data_inicio")
    hora = estado.get("horario_inicio")
    janela = f"{data}T{hora}" if hora else data

    lat, lon = estado["coordenadas"]
    texto = estado.get("texto_descritivo", "").lower()
    
    # Heurística para Modalidade
    if "bicicleta" in texto or "bike" in texto or "ciclismo" in texto or "pedalar" in texto:
        modalidade = "Ciclismo Urbano"
    else:
        modalidade = "Corrida de Rua Pedestre"
        
    # Heurística para Perfil de Altimetria
    if "plano" in texto or "reta" in texto:
        altimetria = "Plano"
    elif "montanhoso" in texto or "morro" in texto or "subida" in texto or "ladeira" in texto or "força" in texto:
        altimetria = "Montanhoso"
    else:
        altimetria = "Moderado"

    requisitos: RequisitosRota = {
        "ponto_partida": f"{lat}, {lon}",
        "distancia_alvo_km": estado["distancia_alvo_km"],
        "janela_temporal": janela,
        "perfil_altimetria": altimetria,
        "modalidade": modalidade,
    }
    logger.info("[orquestrador] Requisitos consolidados: %s", requisitos)
    return {"requisitos": requisitos}

