"""Gera um diagrama (PNG) da sequência de passos do grafo LangGraph do MOVA-SE.

Fluxograma desenhado com matplotlib (offline), rotulado em pt-BR e com cores por
agente. Mantido em sincronia manual com ``app/graph/builder.py``.

Uso:
    uv run python scripts/gerar_diagrama_grafo.py
Saída:
    docs/fluxo_grafo.png
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

# --- Paleta ---------------------------------------------------------------
COR_APOIO = "#e8edf2"      # nós de apoio (geocodificação, orquestrador, plot)
COR_BORDA = "#5b6b7b"
COR_START = "#2ca02c"
COR_END = "#d62728"
# 7 cores distintas p/ os agentes, evitando verde/vermelho (START/END).
CORES_AGENTE = {
    1: "#4e79a7",  # extrair_lugar   (azul)
    2: "#f28e2b",  # extrair_distancia (laranja)
    3: "#b07aa1",  # extrair_horario (roxo)
    4: "#edc948",  # meteorológico   (amarelo)
    5: "#76b7b2",  # infraestrutura  (teal)
    6: "#9c755f",  # motor_roteamento (marrom)
    7: "#ff9da7",  # comunicador     (rosa)
}

# --- Nós: id -> (x, y, largura, altura, rótulo, cor) ----------------------
LARG, ALT = 2.35, 0.9
nos = {
    "START": (5.0, 12.2, 1.4, 0.7, "START", COR_START),
    "extrair_lugar": (1.7, 10.7, LARG, 1.2, "Agente Extrator\nde Lugar\n(Agente 1)", CORES_AGENTE[1]),
    "extrair_distancia": (5.0, 10.7, LARG, 1.2, "Agente Extrator\nde Distância\n(Agente 2)", CORES_AGENTE[2]),
    "extrair_horario": (8.3, 10.7, LARG, 1.2, "Agente Extrator\nde Horário\n(Agente 3)", CORES_AGENTE[3]),
    "geocodificar": (1.7, 9.0, LARG, ALT, "geocodificar", COR_APOIO),
    "geocodificar_fallback": (-1.4, 7.8, 2.9, 1.15, "geocodificar_fallback\n(busca na internet\npor termo)", COR_APOIO),
    "orquestrador": (5.0, 7.6, LARG, ALT, "orquestrador\n(nó · defer)", COR_APOIO),
    "analista_meteorologico": (2.6, 5.9, 3.05, ALT, "analista_meteorologico\n(Agente 4)", CORES_AGENTE[4]),
    "analista_infraestrutura": (7.4, 5.9, 3.05, ALT, "analista_infraestrutura\n(Agente 5)", CORES_AGENTE[5]),
    "motor_roteamento": (5.0, 4.3, LARG, ALT, "motor_roteamento\n(Agente 6)", CORES_AGENTE[6]),
    "comunicador": (5.0, 2.9, LARG, ALT, "comunicador\n(Agente 7)", CORES_AGENTE[7]),
    "plotar_grafo": (5.0, 1.5, LARG, ALT, "plotar_grafo", COR_APOIO),
    "END": (5.0, 0.3, 1.4, 0.7, "END", COR_END),
}

# --- Arestas: (origem, destino, estilo, rótulo[, ancoras]) -----------------
# estilo: "solida" | "condicional" (tracejada)
# ancoras (opcional): (saida, entrada) forçando os pontos, ex.: ("bot", "top").
arestas = [
    ("START", "extrair_lugar", "solida", ""),
    ("START", "extrair_distancia", "solida", ""),
    ("START", "extrair_horario", "solida", ""),
    ("extrair_lugar", "geocodificar", "solida", ""),
    ("geocodificar", "orquestrador", "condicional", "achou"),
    ("geocodificar", "geocodificar_fallback", "condicional", "não achou"),
    ("geocodificar_fallback", "orquestrador", "solida", "", ("right", "left")),
    ("extrair_distancia", "orquestrador", "solida", ""),
    ("extrair_horario", "orquestrador", "solida", ""),
    # Fan-out / fan-in em V (cima/embaixo) para leitura clara dos ramos paralelos.
    ("orquestrador", "analista_meteorologico", "solida", "", ("bot", "top")),
    ("orquestrador", "analista_infraestrutura", "solida", "", ("bot", "top")),
    ("analista_meteorologico", "motor_roteamento", "solida", "", ("bot", "top")),
    ("analista_infraestrutura", "motor_roteamento", "solida", "", ("bot", "top")),
    ("motor_roteamento", "comunicador", "solida", ""),
    ("comunicador", "plotar_grafo", "solida", ""),
    ("plotar_grafo", "END", "solida", ""),
]


def _texto_cor(cor_fundo: str) -> str:
    """Preto sobre fundos claros, branco sobre escuros."""
    r, g, b = (int(cor_fundo[i : i + 2], 16) for i in (1, 3, 5))
    luminancia = 0.299 * r + 0.587 * g + 0.114 * b
    return "#000000" if luminancia > 150 else "#ffffff"


def _borda(no: str):
    """Retorna as bordas (superior/inferior/esq/dir) do nó para ancorar setas."""
    x, y, w, h, *_ = nos[no]
    return {
        "top": (x, y + h / 2),
        "bot": (x, y - h / 2),
        "left": (x - w / 2, y),
        "right": (x + w / 2, y),
        "center": (x, y),
    }


def _ancoras(orig: str, dest: str):
    """Escolhe pontos de saída/entrada conforme a posição relativa dos nós."""
    xo, yo = nos[orig][0], nos[orig][1]
    xd, yd = nos[dest][0], nos[dest][1]
    bo, bd = _borda(orig), _borda(dest)
    if abs(yo - yd) >= abs(xo - xd):  # predominantemente vertical
        return (bo["bot"], bd["top"]) if yo > yd else (bo["top"], bd["bot"])
    return (bo["right"], bd["left"]) if xo < xd else (bo["left"], bd["right"])


def gerar(caminho_saida: str) -> str:
    fig, ax = plt.subplots(figsize=(11, 13))

    # Arestas primeiro (ficam atrás das caixas).
    for aresta in arestas:
        orig, dest, estilo, rotulo = aresta[:4]
        override = aresta[4] if len(aresta) > 4 else None
        if override:
            (x0, y0) = _borda(orig)[override[0]]
            (x1, y1) = _borda(dest)[override[1]]
        else:
            (x0, y0), (x1, y1) = _ancoras(orig, dest)
        tracejado = estilo == "condicional"
        seta = FancyArrowPatch(
            (x0, y0), (x1, y1),
            arrowstyle="-|>", mutation_scale=16,
            linewidth=1.6, color="#7a8896",
            linestyle="--" if tracejado else "-",
            connectionstyle="arc3,rad=0.0",
            shrinkA=1, shrinkB=1, zorder=1,
        )
        ax.add_patch(seta)
        if rotulo:
            ax.text(
                (x0 + x1) / 2 + 0.15, (y0 + y1) / 2, rotulo,
                fontsize=7.5, style="italic", color="#5b6b7b",
                ha="left", va="center", zorder=3,
            )

    # Caixas dos nós.
    for _id, (x, y, w, h, rotulo, cor) in nos.items():
        caixa = FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            linewidth=1.4, edgecolor=COR_BORDA, facecolor=cor, zorder=2,
        )
        ax.add_patch(caixa)
        ax.text(
            x, y, rotulo, ha="center", va="center",
            fontsize=9, fontweight="bold", color=_texto_cor(cor), zorder=3,
        )

    # Callout com a fórmula do peso das arestas (Agente 6 — Motor de Roteamento).
    fx, fy = 8.15, 4.3  # à direita do motor_roteamento
    ax.annotate(
        "", xy=(nos["motor_roteamento"][0] + LARG / 2, nos["motor_roteamento"][1]),
        xytext=(fx - 1.55, fy),
        arrowprops=dict(arrowstyle="-", color="#9c755f", lw=1.2), zorder=1,
    )
    ax.add_patch(FancyBboxPatch(
        (fx - 1.55, fy - 0.45), 3.1, 0.9,
        boxstyle="round,pad=0.04,rounding_size=0.1",
        linewidth=1.2, edgecolor="#9c755f", facecolor="#f6efe9", zorder=2,
    ))
    ax.text(
        fx, fy + 0.16, r"Peso da aresta ($W_e$)",
        fontsize=8, fontweight="bold", ha="center", va="center", color="#5b4636", zorder=3,
    )
    ax.text(
        fx, fy - 0.15, r"$W_e = L_e\,(1 + \alpha E_e + \beta S_e - \gamma I_e)$",
        fontsize=9.5, ha="center", va="center", color="#2b3742", zorder=3,
    )

    # Legenda dos agentes.
    legenda = [
        ("Agente 1 — Extrator de Lugar", CORES_AGENTE[1]),
        ("Agente 2 — Extrator de Distância", CORES_AGENTE[2]),
        ("Agente 3 — Extrator de Horário", CORES_AGENTE[3]),
        ("Agente 4 — Meteorológico", CORES_AGENTE[4]),
        ("Agente 5 — Infraestrutura", CORES_AGENTE[5]),
        ("Agente 6 — Motor de Roteamento", CORES_AGENTE[6]),
        ("Agente 7 — Comunicador", CORES_AGENTE[7]),
        ("Nós de apoio (orquestrador, etc.)", COR_APOIO),
    ]
    for i, (texto, cor) in enumerate(legenda):
        ly = 6.0 - i * 0.55
        ax.add_patch(FancyBboxPatch(
            (-3.1, ly - 0.16), 0.32, 0.32,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            linewidth=1.0, edgecolor=COR_BORDA, facecolor=cor, zorder=3,
        ))
        ax.text(-2.65, ly, texto, fontsize=8, va="center", ha="left", color="#2b3742", zorder=3)

    ax.text(
        5.0, 13.4, "MOVA-SE — Fluxo dos Agentes (LangGraph)",
        fontsize=15, fontweight="bold", ha="center", color="#2b3742",
    )
    ax.text(
        5.0, 12.9, "Sequência de passos do grafo de orquestração  ·  — fluxo normal   - - - aresta condicional",
        fontsize=8.5, ha="center", color="#5b6b7b",
    )

    ax.set_xlim(-3.4, 10.2)
    ax.set_ylim(-0.4, 13.8)
    ax.set_aspect("equal")
    ax.axis("off")

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    fig.savefig(caminho_saida, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return caminho_saida


if __name__ == "__main__":
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    saida = os.path.join(raiz, "docs", "fluxo_grafo.png")
    print("Diagrama salvo em:", gerar(saida))
