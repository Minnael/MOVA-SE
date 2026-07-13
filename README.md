# MOVA-SE

**Sistema Agêntico Multimodal para Roteamento Inteligente e Seguro de Atividades Físicas Urbanas**

> Trabalho de Conclusão / Atividade Prática Supervisionada — Engenharia de Computação

MOVA-SE é uma arquitetura computacional multiagente que recebe requisições em linguagem
natural sobre eventos esportivos urbanos (corrida de rua e ciclismo), coleta dados exógenos
de topografia, infraestrutura viária e meteorologia, e calcula rotas otimizadas — saudáveis
e seguras — retornando uma interface multimodal com representação geoespacial e justificativa
narrativa.

## Motivação

Aplicativos de navegação comercial (Google Maps, Waze) otimizam para veículos e menor tempo,
ignorando variáveis críticas para atletas e pedestres: qualidade do asfalto, altimetria,
conforto térmico e segurança viária. Plataformas esportivas (Strava, Wikiloc) usam mapas de
calor históricos e carecem de reatividade contextual em tempo real (clima iminente, iluminação,
segurança pública).

MOVA-SE une a capacidade de raciocínio e decomposição de problemas dos **LLMs** ao determinismo
matemático de **algoritmos de teoria dos grafos** (via OSMnx / NetworkX), entregando rotas
personalizadas e justificadas analiticamente por agentes autônomos especialistas.

## Arquitetura Multiagente

O sistema adota o padrão de arquitetura multiagente cooperativa. Cada agente opera de forma
assíncrona, consome ferramentas de software específicas e compartilha resultados por um
barramento de contexto. A orquestração é implementada com **LangChain / LangGraph**.

| # | Agente | Responsabilidade | Ferramentas |
|---|--------|------------------|-------------|
| 1 | **Orquestrador / Engenheiro de Requisitos** | Padroniza as entradas brutas, faz o *parsing* inicial, aciona os agentes subordinados e consolida a resposta final | LangGraph (state graph) |
| 2 | **Analista Meteorológico** | Consome dados de temperatura, índice UV, precipitação e vento; emite diretrizes ao motor de redes (ex.: sol forte → priorizar vias arborizadas) | API Open-Meteo |
| 3 | **Infraestrutura e Segurança Urbana** | Analisa calçadas, ciclovias/ciclofaixas, iluminação pública (`lit=yes`) e evita vias arteriais expressas sem passagem protegida | API Overpass (OpenStreetMap) |
| 4 | **Matemático de Redes (Motor de Roteamento)** | Baixa o grafo de ruas local e aplica busca (Dijkstra modificado / A\*) sobre uma matriz de adjacência com pesos dinâmicos | OSMnx, NetworkX |
| 5 | **Comunicador / Redator Técnico** | Traduz métricas geográficas e JSONs complexos em narrativa humana acessível, apontando pontos críticos e motivos das escolhas | LLM |

## Fluxo de Execução

1. **Ingestão** — o usuário define os parâmetros (ex.: 12 km de corrida, partida em coord. X, domingo 07h00).
2. **Enriquecimento contextual** — o Orquestrador ativa em paralelo os agentes Meteorológico e de Infraestrutura, que retornam fatores ambientais e características viárias da região.
3. **Modelagem matemática de pesos** — o Agente de Redes intercepta o grafo do OSMnx e recalcula o peso de cada aresta:

   ```
   Wₑ = Lₑ × (1 + α·Eₑ + β·Sₑ − γ·Iₑ)
   ```

   | Símbolo | Significado |
   |---------|-------------|
   | `Wₑ` | Peso final da aresta (custo do caminho) |
   | `Lₑ` | Comprimento geométrico bruto da rua, em metros |
   | `Eₑ` | Penalidade por inclinação acentuada (se o usuário pediu rota plana) |
   | `Sₑ` | Fator de risco urbano (ruas sem iluminação à noite, vias expressas sem calçada) |
   | `Iₑ` | Bônus de infraestrutura saudável (arborização, ciclovias, calçadões) |
   | `α, β, γ` | Hiperparâmetros de ajuste configuráveis do sistema |

4. **Geração de rotas** — o algoritmo de caminho mínimo minimiza `Σ Wₑ` até aproximar-se da quilometragem desejada, em circuito fechado (retorno ao ponto inicial) ou ponto a ponto.
5. **Renderização e síntese** — o mapa é salvo como artefato e o relatório linguístico é gerado integrando as informações contextuais.

## Contratos de Entrada e Saída

### Entrada

| Parâmetro | Requisito técnico |
|-----------|-------------------|
| **Ponto de partida** | Coordenadas (Lat/Lon) ou endereço processável por *geocoding* |
| **Distância alvo** | Valor `float` em km, com tolerância de variação definida pelo usuário |
| **Perfil de altimetria** | `Plano` \| `Moderado` \| `Montanhoso/Treino de Força` |
| **Janela temporal** | Data e hora previstas do evento (base para clima e iluminação) |
| **Modalidade** | `Corrida de Rua Pedestre` \| `Ciclismo Urbano` (altera restrições de vias) |

### Saída

| Artefato | Descrição |
|----------|-----------|
| **Artefato geoespacial** | Mapa plotado (interativo via Folium ou Matplotlib) com o traçado exato |
| **Matriz de métricas** | Distância final, ganho de elevação acumulado e estimativa de tempo por ritmo |
| **Relatório técnico narrativo** | Texto explicativo com justificativa das ruas, alertas de segurança e cuidados operacionais |

## Stack Tecnológica

- **Linguagem:** Python `>= 3.14`
- **Orquestração de agentes:** LangChain, LangGraph
- **Grafos de ruas:** OSMnx, NetworkX
- **APIs públicas:** Open-Meteo (meteorologia), Overpass / OpenStreetMap (infraestrutura viária)
- **Visualização:** Folium, Matplotlib
- **Gerenciador de dependências:** [uv](https://github.com/astral-sh/uv)

## Instalação e Execução

```bash
# Instalar dependências (cria o .venv automaticamente)
uv sync

# Executar
uv run main.py
```

Para adicionar novas dependências:

```bash
uv add osmnx networkx folium matplotlib
```

## Desenvolvimento

**Estratégia de teste (mocking):** no início do desenvolvimento, configure respostas fixas
(*mock*) para as APIs Open-Meteo e Overpass, economizando requisições e focando a depuração na
lógica de convergência matemática do tamanho da rota gerada.

## Status

🚧 Em desenvolvimento — arquitetura definida, orquestração (LangChain/LangGraph) em configuração.
