"""Nó de plotagem — gera uma imagem PNG da rota sobre o grafo viário.

Carrega o grafo anotado pelo Agente 3 (a partir de ``caminho_grafo``) e a rota
calculada pelo Agente 4 (``coordenadas_rota``), renderizando a rota destacada
sobre a malha e salvando em ``data/mapa_grafo.png``. O arquivo é servido pela
API no endpoint ``GET /rotas/imagem``.

Se não houver rota no estado, plota apenas a malha viária.
"""

from __future__ import annotations

import logging
import os

import matplotlib

# Backend headless: não há display no servidor; deve vir antes do pyplot.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import osmnx as ox  # noqa: E402

from app.graph.state import EstadoAgentico  # noqa: E402

logger = logging.getLogger(__name__)

# Caminho fixo do PNG gerado — mesmo esquema de ``data/`` do Agente 3.
_PASTA_DATA = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")
)
CAMINHO_IMAGEM = os.path.join(_PASTA_DATA, "mapa_grafo.png")


def _desenhar_rota(ax, coordenadas_rota) -> None:
    """Sobrepõe a rota (lista de ``(lat, lon)``) no eixo, em vermelho.

    No plot do osmnx o eixo x é a longitude e o y é a latitude.
    """
    if not coordenadas_rota:
        return
    ys = [float(lat) for lat, lon in coordenadas_rota]
    xs = [float(lon) for lat, lon in coordenadas_rota]
    ax.plot(xs, ys, color="red", linewidth=3, alpha=0.9, zorder=5)
    ax.scatter([xs[0]], [ys[0]], c="#2ca02c", s=70, zorder=6)  # partida/chegada


def _plotar_fallback(G, coordenadas_rota, caminho: str) -> None:
    """Plot manual (matplotlib puro) caso ``ox.plot_graph`` falhe.

    Usa os atributos ``x``/``y`` dos nós; útil para grafos mock sem CRS.
    """
    fig, ax = plt.subplots(figsize=(10, 10))
    for u, v, data in G.edges(data=True):
        xu, yu = G.nodes[u].get("x"), G.nodes[u].get("y")
        xv, yv = G.nodes[v].get("x"), G.nodes[v].get("y")
        if None in (xu, yu, xv, yv):
            continue
        ax.plot([float(xu), float(xv)], [float(yu), float(yv)], color="#cccccc", linewidth=0.6)
    _desenhar_rota(ax, coordenadas_rota)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.savefig(caminho, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plotar_grafo(estado: EstadoAgentico) -> dict:
    """Renderiza a rota sobre o grafo viário em PNG e retorna o caminho do arquivo."""
    logger.info("[plotar_grafo] Iniciando plotagem da rota/grafo")
    caminho_grafo = estado.get("caminho_grafo")
    if not caminho_grafo:
        logger.error("[plotar_grafo] 'caminho_grafo' ausente no estado")
        raise ValueError("Não há grafo para plotar: 'caminho_grafo' não definido no estado.")

    coordenadas_rota = estado.get("coordenadas_rota") or []
    logger.info("[plotar_grafo] Rota com %d pontos", len(coordenadas_rota))

    os.makedirs(_PASTA_DATA, exist_ok=True)
    G = ox.load_graphml(caminho_grafo)
    logger.info("[plotar_grafo] Grafo carregado (%d nós, %d arestas)", len(G.nodes), len(G.edges))

    try:
        # Malha discreta (cinza) para a rota vermelha se destacar.
        fig, ax = ox.plot_graph(
            G,
            show=False,
            close=False,
            save=False,
            node_size=2,
            node_color="#8aa0b6",
            edge_color="#cccccc",
            edge_linewidth=0.6,
            bgcolor="white",
        )
        _desenhar_rota(ax, coordenadas_rota)
        fig.savefig(CAMINHO_IMAGEM, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        logger.info("[plotar_grafo] Imagem salva via osmnx em: %s", CAMINHO_IMAGEM)
    except Exception as e:
        logger.warning("[plotar_grafo] Falha no ox.plot_graph (%s). Usando fallback matplotlib.", e)
        _plotar_fallback(G, coordenadas_rota, CAMINHO_IMAGEM)
        logger.info("[plotar_grafo] Imagem salva via fallback em: %s", CAMINHO_IMAGEM)

    return {"caminho_imagem": CAMINHO_IMAGEM}
