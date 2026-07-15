"""Configuração e factory do cliente de LLM.

Centraliza o acesso ao modelo MiniMax-M3 (via API OpenAI-compatível) para reuso
pelos nós de extração. A chave vem do ``.env`` (``MINIMAX_API_KEY``); base_url e
modelo ficam externalizados aqui, fora do código de negócio.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

logger = logging.getLogger(__name__)

MINIMAX_BASE_URL = "https://api.minimax.io/v1"
MINIMAX_MODEL = "MiniMax-M3"


@lru_cache
def get_llm() -> ChatOpenAI:
    """Cliente LangChain apontado para a API MiniMax (OpenAI-compatível).

    Instanciado sob demanda (não no import) para não exigir a chave só por
    importar o módulo. Cacheado para reutilizar a mesma conexão.
    """
    tem_chave = bool(os.environ.get("MINIMAX_API_KEY")) and os.environ.get("MINIMAX_API_KEY") != "dummy_key"
    logger.info("Instanciando cliente LLM %s (chave configurada: %s)", MINIMAX_MODEL, tem_chave)
    return ChatOpenAI(
        model=MINIMAX_MODEL,
        api_key=os.environ.get("MINIMAX_API_KEY", "dummy_key"),
        base_url=MINIMAX_BASE_URL,
        temperature=0,  # extração determinística
    )
