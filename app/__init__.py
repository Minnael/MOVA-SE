"""Pacote da aplicação MOVA-SE.

Configura o logging assim que o pacote é importado, para que qualquer ponto de
entrada (API, ``main.py`` ou scripts avulsos) já registre as etapas do grafo.
"""

from app.logging_config import configurar_logging

configurar_logging()
