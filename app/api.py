"""Camada de entrada (interface) do sistema agêntico MOVA-SE.

Expõe a API HTTP que recebe a requisição em linguagem natural e a encaminha
para o grafo de orquestração.
"""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from app.graph.builder import construir_grafo

app = FastAPI(title="MOVA-SE")

# Compila o grafo uma única vez no carregamento do módulo; a rota apenas o
# aciona a cada requisição.
grafo = construir_grafo()


class RequisicaoRota(BaseModel):
    """Corpo da requisição: descrição em linguagem natural da rota desejada."""

    texto_descritivo: str  # descrição em linguagem natural


@app.post("/rotas")
def solicitar_rota(requisicao: RequisicaoRota) -> dict:
    """Recebe o texto do usuário e aciona o grafo agêntico.

    Ainda não executa roteamento real: retorna o estado resultante com os
    requisitos consolidados pelo Orquestrador (parte dos campos ainda mocada).
    """
    return grafo.invoke({"texto_descritivo": requisicao.texto_descritivo})
