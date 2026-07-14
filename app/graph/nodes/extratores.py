"""Nós de extração — desmembram o texto livre do usuário em campos estruturados.

São três funções-nó que rodam **em paralelo** a partir do START do grafo. Cada
uma lê ``texto_descritivo`` e escreve apenas a sua chave no estado, de modo que
não há conflito de escrita concorrente entre elas. O nó Orquestrador consolida
os três resultados depois (fan-in).

MOCK: por ora as três ignoram o texto e devolvem valores fixos. A extração real
(via LLM/LangChain a partir de ``texto_descritivo``) virá em seguida.
"""

from __future__ import annotations

from app.graph.state import EstadoAgentico


def extrair_lugar(estado: EstadoAgentico) -> dict:
    """Extrai o nome do lugar de partida a partir do texto de entrada."""
    # TODO: extração real via LLM (LangChain) a partir de ``texto_descritivo``.
    return {"lugar": "Parque Ibirapuera, São Paulo"}


def extrair_distancia(estado: EstadoAgentico) -> dict:
    """Extrai a distância-alvo do percurso a partir do texto de entrada."""
    # TODO: extração real via LLM (LangChain) a partir de ``texto_descritivo``.
    return {"distancia_alvo_km": 12.0}


def extrair_horario(estado: EstadoAgentico) -> dict:
    """Extrai o horário de início a partir do texto de entrada."""
    # TODO: extração real via LLM (LangChain) a partir de ``texto_descritivo``.
    return {"horario_inicio": "2026-07-19T07:00"}
