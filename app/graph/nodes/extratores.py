"""Nós de extração — desmembram o texto livre do usuário em campos estruturados.

São três funções-nó que rodam **em paralelo** a partir do START do grafo. Cada
uma lê ``texto_descritivo`` e escreve apenas a sua chave no estado, de modo que
não há conflito de escrita concorrente entre elas. O nó Orquestrador consolida
os três resultados depois (fan-in).

``extrair_lugar`` e ``extrair_distancia`` já usam LLM real (MiniMax-M3 via
LangChain); ``extrair_horario`` segue mock até ser implementado.
"""

from __future__ import annotations

import re

from app.graph.state import EstadoAgentico
from app.llm import get_llm

_SYSTEM_DISTANCIA = (
    "Você extrai a distância-alvo do percurso, em quilômetros, do texto do usuário. "
    "Converta metros ou milhas para km quando necessário. " #tool de metros para km 
    "Responda apenas com o número em km, usando ponto como separador decimal."
)

_SYSTEM_LUGAR = (
    "Você extrai o nome do lugar de partida do percurso a partir do texto do usuário "
    "(bairro, parque, endereço ou cidade). "
    "Responda apenas com o nome do lugar, sem explicações."
)

# MiniMax-M3 é um modelo de raciocínio: emite um bloco <think>...</think> antes
# da resposta. Removemos esse bloco e extraímos o número do restante.
_RE_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_RE_NUMERO = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def extrair_lugar(estado: EstadoAgentico) -> dict:
    """Extrai o nome do lugar de partida do texto via LangChain + MiniMax-M3."""
    resposta = get_llm().invoke(
        [("system", _SYSTEM_LUGAR), ("human", estado["texto_descritivo"])]
    )
    lugar = _RE_THINK.sub("", str(resposta.content)).strip().strip("\"'")
    if not lugar:
        raise ValueError("Não foi possível extrair o lugar do texto.")
    return {"lugar": lugar}


def extrair_distancia(estado: EstadoAgentico) -> dict:
    """Extrai a distância-alvo (km) do texto via LangChain + MiniMax-M3."""
    resposta = get_llm().invoke(
        [("system", _SYSTEM_DISTANCIA), ("human", estado["texto_descritivo"])]
    )
    texto = _RE_THINK.sub("", str(resposta.content)).strip()
    match = _RE_NUMERO.search(texto)
    if match is None:
        raise ValueError(f"Não foi possível extrair a distância de: {texto!r}")
    return {"distancia_alvo_km": float(match.group().replace(",", "."))}


def extrair_horario(estado: EstadoAgentico) -> dict:
    """Extrai o horário de início a partir do texto de entrada."""
    # TODO: extração real via LLM (LangChain) a partir de ``texto_descritivo``.
    return {"horario_inicio": "2026-07-19T07:00"}
