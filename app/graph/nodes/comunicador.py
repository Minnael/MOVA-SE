"""Nó do Agente 5 - Comunicador / Redator Técnico.

Usa o MiniMax-M3 (via cliente compartilhado ``app.llm.get_llm``) para redigir um
relatório narrativo amigável com base nos requisitos consolidados.
"""

from __future__ import annotations

import json
import logging
import re

from app.graph.state import EstadoAgentico
from app.llm import get_llm

logger = logging.getLogger(__name__)

# MiniMax-M3 é um modelo de raciocínio: pode emitir um bloco <think>...</think>
# antes da resposta. Removemos esse bloco do texto final.
_RE_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)

_SYSTEM_PROMPT = (
    "Você gera um relatório narrativo em português, amigável e motivador, para um atleta, "
    "com base nos dados da rota planejada. "
    "Escreva um relatório com 2 a 3 parágrafos curtos explicando a rota, o horário, a distância "
    "e dando dicas de preparação relacionadas ao treino (aquecimento, alongamento, ritmo, "
    "respiração, hidratação, vestuário). "
    "NÃO fale sobre alimentação, refeições ou nutrição. "
    "NÃO cite o nome de nenhum sistema, marca ou aplicativo (por exemplo, 'MOVA-SE'). "
    "Não inclua pensamentos, tags XML, títulos, nem textos soltos antes ou depois do relatório. "
    "Apenas o relatório final legível."
)


def redigir_relatorio(estado: EstadoAgentico) -> dict:
    """Consome o estado e gera um relatório com o MiniMax-M3."""

    logger.info("[comunicador] Iniciando redação do relatório (Agente 5, MiniMax)")

    requisitos = estado.get("requisitos", {})
    dados_json = json.dumps(requisitos, indent=2, ensure_ascii=False)
    prompt_usuario = f"DADOS DA ROTA:\n{dados_json}"

    try:
        logger.info("[comunicador] Chamando LLM MiniMax-M3")
        resposta = get_llm().invoke(
            [("system", _SYSTEM_PROMPT), ("human", prompt_usuario)]
        )
        texto = _RE_THINK.sub("", str(resposta.content)).strip()
        logger.info("[comunicador] Relatório gerado via MiniMax")
        return {"relatorio_narrativo": texto}
    except Exception as e:
        logger.warning("[comunicador] Erro na chamada do MiniMax (%s). Usando fallback heurístico.", e)
        dist = requisitos.get("distancia_alvo_km", 10.0)
        ponto = requisitos.get("ponto_partida", "Parque Ibirapuera")
        horario = requisitos.get("janela_temporal", "08:00")

        fallback_texto = (
            f"[Fallback] Olá! Preparado para a sua atividade física?\n\n"
            f"Sua rota começará em {ponto} com uma distância alvo de {dist} km. "
            f"O horário programado é {horario}. Lembre-se de conferir as condições "
            f"físicas e climáticas antes de começar, manter-se hidratado e aproveitar o percurso!"
        )
        return {"relatorio_narrativo": fallback_texto}
