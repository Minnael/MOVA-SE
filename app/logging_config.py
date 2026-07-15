"""Configuração central de logging do MOVA-SE.

Todos os módulos usam ``logging.getLogger(__name__)`` para emitir mensagens; a
formatação e o nível são definidos aqui, uma única vez. O nível pode ser
ajustado pela variável de ambiente ``LOG_LEVEL`` (padrão ``INFO``), ex.:

    LOG_LEVEL=DEBUG uv run main.py
"""

from __future__ import annotations

import logging
import os

_FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATA_FMT = "%H:%M:%S"

_configurado = False


def configurar_logging() -> None:
    """Configura o logging da aplicação (idempotente).

    Usa ``logging.basicConfig``, que só instala um handler na raiz caso ainda
    não exista — assim convive com o logging do uvicorn/pytest sem duplicar
    saídas. Chamado automaticamente ao importar o pacote ``app``.
    """
    global _configurado
    if _configurado:
        return

    nivel = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=nivel, format=_FORMATO, datefmt=_DATA_FMT)
    # Garante o nível mesmo quando outro handler (uvicorn) já configurou a raiz.
    logging.getLogger("app").setLevel(nivel)
    _configurado = True
