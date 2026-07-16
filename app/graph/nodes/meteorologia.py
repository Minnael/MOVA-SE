"""Nó do Agente 2 — Analista Meteorológico de Rotas.

Responsável por obter os dados de clima da API Open-Meteo com base na
localização e janela temporal, e acionar a LLM para formular a análise
qualitativa (alertas de saúde) e diretrizes quantitativas (sombra, vento, chuva).
"""

from __future__ import annotations

import json
import logging
import re

from app.graph.state import EstadoAgentico
from app.llm import get_llm
from app.utils.clima import consultar_open_meteo

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Você é o Analista Meteorológico do sistema MOVA-SE. "
    "Sua função é receber os dados brutos de clima previstos para a atividade física do usuário "
    "e sua modalidade de treino, analisar os riscos à saúde/prática esportiva "
    "(radiação UV extrema, chuva forte, vento excessivo, calor/frio severo) "
    "e retornar um objeto JSON estrito com a seguinte estrutura:\n"
    "{\n"
    '  "resumo": "Explicação curta (1-2 parágrafos) do clima e alertas relevantes.",\n'
    '  "diretrizes": {\n'
    '    "requer_sombra": true/false (marcar true se UV > 4 ou Temperatura > 26°C),\n'
    '    "risco_chuva": true/false (marcar true se probabilidade de chuva > 40%),\n'
    '    "vento_forte": true/false (marcar true se vento > 20 km/h),\n'
    '    "temperatura_extrema": true/false (marcar true se Temperatura > 32°C ou < 10°C)\n'
    "  }\n"
    "}\n\n"
    "Responda APENAS com o objeto JSON válido. Não inclua blocos de código markdown (como ```json) ou "
    "qualquer texto explicativo fora do JSON."
)

_RE_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def analisar_clima(estado: EstadoAgentico) -> dict:
    """Consome a API de meteorologia e usa a LLM para gerar a análise do clima.

    Args:
        estado: estado agêntico contendo `coordenadas` e `requisitos`.

    Returns:
        Atualização parcial do estado com as chaves `relatorio_clima` e `diretrizes_clima`.
    """
    logger.info("[meteorologia] Iniciando análise climática (Agente 2)")
    coordenadas = estado.get("coordenadas")
    requisitos = estado.get("requisitos")

    if not coordenadas or not requisitos:
        logger.error("[meteorologia] Coordenadas ou requisitos ausentes no estado")
        raise ValueError("Coordenadas ou requisitos não definidos no estado.")

    lat, lon = coordenadas
    data_hora = requisitos["janela_temporal"]
    modalidade = requisitos["modalidade"]

    # 1. Buscar dados de clima reais da API Open-Meteo. Se a API falhar
    # (timeout, 429/limite de requisições etc.), usa valores neutros para não
    # derrubar todo o fluxo — o roteamento não depende do clima.
    try:
        dados_clima = consultar_open_meteo(lat, lon, data_hora)
    except Exception as e:
        logger.warning("[meteorologia] Falha ao consultar Open-Meteo (%s). Usando clima neutro.", e)
        dados_clima = {
            "temperatura": 25.0,
            "chuva_probabilidade": 0,
            "indice_uv": 5.0,
            "velocidade_vento": 10.0,
        }

    # 2. Montar prompt do usuário
    prompt_usuario = (
        f"Dados de Clima:\n"
        f"- Temperatura: {dados_clima['temperatura']} °C\n"
        f"- Probabilidade de Chuva: {dados_clima['chuva_probabilidade']} %\n"
        f"- Índice UV: {dados_clima['indice_uv']}\n"
        f"- Vento: {dados_clima['velocidade_vento']} km/h\n\n"
        f"Modalidade: {modalidade}\n"
        f"Data/Hora do Treino: {data_hora}"
    )

    try:
        # 3. Chamar a LLM
        logger.info("[meteorologia] Chamando LLM para análise do clima")
        resposta = get_llm().invoke(
            [("system", _SYSTEM_PROMPT), ("human", prompt_usuario)]
        )

        # 4. Limpar e fazer o parsing do JSON
        texto_llm = _RE_THINK.sub("", str(resposta.content)).strip()
        
        # Remover possíveis marcações ```json e ```
        texto_llm = re.sub(r"^```json\s*", "", texto_llm, flags=re.IGNORECASE)
        texto_llm = re.sub(r"^```\s*", "", texto_llm)
        texto_llm = re.sub(r"\s*```$", "", texto_llm).strip()

        dados_analise = json.loads(texto_llm)
        logger.info("[meteorologia] Análise via LLM concluída")
    except Exception as e:
        # Fallback robusto via heurística caso a LLM falhe ou não tenha API Key
        logger.warning("[meteorologia] Erro na LLM (%s). Usando fallback heurístico (Python puro).", e)
        dados_analise = {
            "resumo": (
                f"Previsão de tempo para o treino: temperatura de {dados_clima['temperatura']}°C, "
                f"com {dados_clima['chuva_probabilidade']}% de probabilidade de chuva, índice UV em {dados_clima['indice_uv']} "
                f"e ventos de {dados_clima['velocidade_vento']} km/h."
            ),
            "diretrizes": {
                "requer_sombra": dados_clima["indice_uv"] > 4 or dados_clima["temperatura"] > 26,
                "risco_chuva": dados_clima["chuva_probabilidade"] > 40,
                "vento_forte": dados_clima["velocidade_vento"] > 20,
                "temperatura_extrema": dados_clima["temperatura"] > 32 or dados_clima["temperatura"] < 10,
            },
        }

    logger.info("[meteorologia] Diretrizes climáticas: %s", dados_analise["diretrizes"])
    return {
        "relatorio_clima": dados_analise["resumo"],
        "diretrizes_clima": dados_analise["diretrizes"],
    }
