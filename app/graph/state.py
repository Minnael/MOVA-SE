"""Estado agêntico — o "barramento de contexto" que trafega pelo grafo.

Cada nó (agente) lê e escreve neste estado compartilhado. Por enquanto ele
carrega o texto de entrada (payload da API), os campos extraídos por cada nó de
extração paralelo (lugar, distância, horário) e os requisitos consolidados pelo
Orquestrador. Conforme os demais agentes forem implementados, novos campos serão
adicionados (fatores meteorológicos, características viárias, rota calculada, etc.).
"""

from __future__ import annotations

from typing import TypedDict


class RequisitosRota(TypedDict, total=False):
    """Requisitos estruturados extraídos do texto livre do usuário.

    PROVISÓRIO: os campos abaixo são um placeholder baseado no contrato de
    entrada do documento de diretrizes. Ainda vamos definir quais informações
    realmente importam para o roteamento.
    """

    ponto_partida: str  # coordenadas "lat, lon" ou endereço para geocoding
    distancia_alvo_km: float
    perfil_altimetria: str  # "Plano" | "Moderado" | "Montanhoso"
    janela_temporal: str  # data/hora ISO 8601 do evento
    modalidade: str  # "Corrida de Rua Pedestre" | "Ciclismo Urbano"


class DiretrizesClima(TypedDict):
    """Diretrizes de roteamento extraídas a partir da análise climática."""

    requer_sombra: bool  # Ativado se calor/UV alto
    risco_chuva: bool  # Ativado se probabilidade de chuva alta
    vento_forte: bool  # Ativado se vento > limite (ex: 20 km/h)
    temperatura_extrema: bool  # Ativado se muito frio ou muito quente


class EstadoAgentico(TypedDict):
    """Estado compartilhado entre os nós do grafo."""

    # Entrada recebida no payload da API.
    texto_descritivo: str  # descrição em linguagem natural
    # Campos extraídos pelos nós de extração paralelos (cada nó escreve o seu).
    lugar: str  # nome do lugar de partida
    coordenadas: tuple[float, float] | None  # (lat, lon) do lugar de partida
    distancia_alvo_km: float
    data_inicio: str  # data resolvida em ISO (YYYY-MM-DD)
    horario_inicio: str | None  # hora "HH:MM" ou None quando ausente no texto
    # Requisitos consolidados pelo Orquestrador.
    requisitos: RequisitosRota | None
    # Preenchido pelo Agente 2 (Analista Meteorológico)
    relatorio_clima: str | None
    diretrizes_clima: DiretrizesClima | None

    # Preenchido pelo Agente 3 (Infraestrutura e Segurança)
    caminho_grafo: str | None

    # Preenchido pelo Agente 4 (Matemático de Redes)
    coordenadas_rota: list[tuple[float, float]] | None
    caminho_mapa_html: str | None
    caminho_mapa_img: str | None
    distancia_real_calculada: float | None

    # Relatório narrativo gerado pelo Agente Comunicador (Ollama).
    relatorio_narrativo: str | None
