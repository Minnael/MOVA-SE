"""Camada de entrada (interface) do sistema agêntico MOVA-SE.

Expõe a API HTTP que recebe a requisição em linguagem natural e a encaminha
para o grafo de orquestração.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
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

    Erros de extração (ex.: data/horário no passado) viram HTTP 422.
    """
    try:
        return grafo.invoke({"texto_descritivo": requisicao.texto_descritivo})
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro


from app.graph.nodes.comunicador import redigir_relatorio
from app.graph.state import EstadoAgentico

@app.post("/teste-agente5")
def testar_agente5_isolado() -> dict:
    """Rota criada para testar APENAS o Agente 5 (Ollama) e a conexão do servidor.
    
    Ignora os agentes da nuvem (MiniMax), usando dados fictícios fixos. 
    Ideal para você e sua equipe testarem o Ngrok e a sua placa de vídeo sem gastar tokens.
    """
    estado_ficticio: EstadoAgentico = {
        "texto_descritivo": "teste isolado",
        "lugar": "Avenida Paulista",
        "coordenadas": (-23.561, -46.656),
        "distancia_alvo_km": 5.0,
        "data_inicio": "2026-07-15",
        "horario_inicio": "18:00",
        "requisitos": {
            "ponto_partida": "-23.561, -46.656",
            "distancia_alvo_km": 5.0,
            "janela_temporal": "2026-07-15T18:00",
            "perfil_altimetria": "Moderado",
            "modalidade": "Corrida de Rua Pedestre"
        }
    }
    
    # Aciona diretamente a sua GPU (Ollama) passando por cima de todo o resto
    resultado = redigir_relatorio(estado_ficticio)
    estado_ficticio["relatorio_narrativo"] = resultado["relatorio_narrativo"]
    
    return estado_ficticio
