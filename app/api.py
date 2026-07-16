"""Camada de entrada (interface) do sistema agêntico MOVA-SE.

Expõe a API HTTP que recebe a requisição em linguagem natural e a encaminha
para o grafo de orquestração.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.graph.builder import construir_grafo
from app.graph.nodes.plotter import CAMINHO_IMAGEM

logger = logging.getLogger(__name__)

# Diretórios de artefatos (data/) e do front-end (web/), relativos à raiz do repo.
_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIR_DATA = os.path.join(_RAIZ, "data")
DIR_WEB = os.path.join(_RAIZ, "web")
os.makedirs(DIR_DATA, exist_ok=True)

app = FastAPI(title="MOVA-SE")

# Compila o grafo uma única vez no carregamento do módulo; a rota apenas o
# aciona a cada requisição.
grafo = construir_grafo()


class RequisicaoRota(BaseModel):
    """Corpo da requisição: descrição em linguagem natural da rota desejada."""

    texto_descritivo: str  # descrição em linguagem natural


@app.post("/rotas")
def solicitar_rota(requisicao: RequisicaoRota) -> dict:
    """Recebe o texto do usuário e aciona o grafo agêntico completo.

    Retorna o estado final: coordenadas, requisitos, análise de clima, rota
    calculada (``coordenadas_rota``/``distancia_real_calculada``), mapa Folium
    (``caminho_mapa_html``), imagem PNG e o relatório narrativo do Comunicador.

    Erros de extração/validação (ex.: data/horário no passado, lugar fora do RN)
    viram HTTP 422.
    """
    logger.info("[API] Nova requisição de rota: %r", requisicao.texto_descritivo)
    try:
        resultado = grafo.invoke({"texto_descritivo": requisicao.texto_descritivo})
        logger.info("[API] Rota processada com sucesso")
        return resultado
    except ValueError as erro:
        logger.warning("[API] Requisição rejeitada (422): %s", erro)
        raise HTTPException(status_code=422, detail=str(erro)) from erro


@app.get("/rotas/imagem")
def obter_imagem_grafo() -> FileResponse:
    """Retorna o PNG do grafo viário gerado pela última chamada a ``POST /rotas``."""
    if not os.path.exists(CAMINHO_IMAGEM):
        logger.warning("[API] Imagem do grafo ainda não gerada")
        raise HTTPException(
            status_code=404,
            detail="Nenhuma imagem gerada ainda. Chame POST /rotas primeiro.",
        )
    logger.info("[API] Servindo imagem do grafo: %s", CAMINHO_IMAGEM)
    return FileResponse(CAMINHO_IMAGEM, media_type="image/png", filename="mapa_grafo.png")


from app.graph.nodes.comunicador import redigir_relatorio
from app.graph.state import EstadoAgentico

@app.post("/teste-agente5")
def testar_agente5_isolado() -> dict:
    """Rota criada para testar APENAS o Agente 5 (Comunicador / MiniMax) e a conexão do servidor.

    Ignora os demais agentes, usando dados fictícios fixos, e aciona diretamente
    o Comunicador. Atenção: o Agente 5 agora usa o MiniMax (cloud), então esta
    rota **consome tokens** — requer ``MINIMAX_API_KEY`` configurada (sem ela,
    cai no fallback heurístico).
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
    
    # Aciona diretamente o Comunicador (MiniMax) passando por cima de todo o resto
    resultado = redigir_relatorio(estado_ficticio)
    estado_ficticio["relatorio_narrativo"] = resultado["relatorio_narrativo"]

    return estado_ficticio


# --- Front-end (servido pela própria API, mesma origem => sem CORS) ---------
@app.get("/")
def pagina_inicial() -> FileResponse:
    """Serve a tela inicial (web/index.html)."""
    return FileResponse(os.path.join(DIR_WEB, "index.html"))


# Assets estáticos do front (style.css, app.js).
app.mount("/static", StaticFiles(directory=DIR_WEB), name="static")
# Artefatos gerados: mapa Folium (mapa_rota_*.html) e imagens (mapa_grafo.png).
app.mount("/data", StaticFiles(directory=DIR_DATA), name="data")
