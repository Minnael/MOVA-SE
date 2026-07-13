# CLAUDE.md — MOVA-SE

Orientações para trabalhar neste repositório. Leia junto ao `README.md` (visão de produto) e ao
`projeto_sistema_agentico_mobilidade.pdf` (documento de diretrizes original / fonte da verdade).

## O que é o projeto

Sistema **agêntico multiagente** que gera rotas otimizadas de corrida de rua e ciclismo urbano.
Une raciocínio de LLMs à teoria dos grafos (OSMnx/NetworkX). Contexto acadêmico: TCC/APS de
Engenharia de Computação — o rigor técnico da manipulação de pesos em grafos reais é o diferencial
avaliado, então **não trate o projeto como um simples wrapper de API de LLM**.

## Stack e ambiente

- Python `>= 3.14`, gerenciado com **uv** (há `pyproject.toml` + `.venv`; não use `pip` direto).
- Dependências já instaladas: `langchain`, `langgraph`.
- Comandos:
  - `uv add <pkg>` — adicionar dependência (atualiza `pyproject.toml` e lockfile).
  - `uv sync` — sincronizar o ambiente.
  - `uv run main.py` — executar.
- Ao introduzir grafos/visualização, prováveis próximas dependências: `osmnx`, `networkx`,
  `folium`, `matplotlib`, além de um cliente HTTP para as APIs.

## Arquitetura: 5 agentes cooperativos

Orquestração via **LangGraph** (grafo de estados) com **LangChain** para as ferramentas.

1. **Orquestrador / Engenheiro de Requisitos** — parsing das entradas, aciona os subordinados, consolida a saída.
2. **Analista Meteorológico** — API Open-Meteo; emite diretrizes ambientais (UV, chuva, vento, temperatura).
3. **Infraestrutura e Segurança Urbana** — API Overpass; calçadas, ciclovias, iluminação (`lit=yes`).
4. **Matemático de Redes (motor de roteamento)** — OSMnx/NetworkX; Dijkstra modificado / A\* sobre pesos dinâmicos.
5. **Comunicador / Redator Técnico** — converte métricas e JSONs em relatório narrativo.

Os agentes 2 e 3 rodam **em paralelo** na fase de enriquecimento. Comunicação por um barramento de contexto compartilhado.

## Regra de negócio central: peso das arestas

O coração técnico do sistema. Para cada aresta `e` do grafo viário:

```
Wₑ = Lₑ × (1 + α·Eₑ + β·Sₑ − γ·Iₑ)
```

- `Lₑ` comprimento bruto (m) · `Eₑ` penalidade de inclinação · `Sₑ` risco urbano · `Iₑ` bônus de infraestrutura saudável.
- `α, β, γ` são **hiperparâmetros configuráveis** — mantenha-os externalizados (config), não hardcoded espalhados.
- O algoritmo de caminho mínimo minimiza `Σ Wₑ` aproximando-se da distância-alvo, em circuito fechado ou ponto a ponto.

Ao mexer no motor de roteamento, preserve a separação entre: (a) download/estrutura do grafo,
(b) cálculo de pesos por aresta, (c) busca de caminho. São responsabilidades distintas.

## Contratos (não quebrar sem intenção)

- **Entrada:** ponto de partida (Lat/Lon ou endereço), distância-alvo (`float` km + tolerância),
  perfil de altimetria (`Plano`/`Moderado`/`Montanhoso`), janela temporal (data/hora), modalidade
  (`Corrida de Rua Pedestre`/`Ciclismo Urbano`).
- **Saída:** artefato geoespacial (mapa Folium/Matplotlib), matriz de métricas (distância, ganho de
  elevação, tempo estimado), relatório técnico narrativo.

## Convenções de desenvolvimento

- **Mock primeiro:** para Open-Meteo e Overpass, use respostas fixas durante o desenvolvimento —
  economiza requisições e isola a depuração na convergência matemática da rota. Não faça chamadas
  reais em testes.
- Idioma do projeto: **português** (código, docs e comentários seguem o domínio em pt-BR).
- Ao adicionar código de LLM, confirmar o provedor antes de assumir (o projeto usa LangChain como
  camada de orquestração; o provedor de modelo ainda não foi fixado).

## Estado atual

Projeto em bootstrap: `main.py` é um stub "Hello". Arquitetura e diretrizes definidas; a
implementação dos agentes e do motor de grafos ainda não começou.
