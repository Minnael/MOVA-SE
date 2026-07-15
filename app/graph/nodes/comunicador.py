"""Nó do Agente 5 - Comunicador / Redator Técnico.

Usa um modelo local via Ollama para redigir um relatório amigável 
com base nos requisitos consolidados.
"""

from __future__ import annotations

import json

import os
from langchain_ollama import ChatOllama

from app.graph.state import EstadoAgentico


def redigir_relatorio(estado: EstadoAgentico) -> dict:
    """Consome o estado e gera um relatório com LLM local."""
    
    # Busca a URL do Ollama no .env (se não existir, usa o padrão localhost)
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    llm = ChatOllama(model="llama3", temperature=0.7, base_url=base_url)

    requisitos = estado.get("requisitos", {})
    clima = estado.get("relatorio_clima", "Sem dados de clima.")
    diretrizes = estado.get("diretrizes_clima", {})
    grafo_path = estado.get("caminho_mapa_html", "Grafo não gerado.")
    distancia_real = estado.get("distancia_real_calculada", requisitos.get("distancia_alvo_km"))

    dados_consolidados = {
        "requisitos_base": requisitos,
        "previsao_clima": clima,
        "alertas_seguranca_climatica": diretrizes,
        "distancia_efetiva_da_rota_km": distancia_real,
        "arquivo_rota_viaria": grafo_path
    }
    
    dados_json = json.dumps(dados_consolidados, indent=2, ensure_ascii=False)

    prompt = f"""Você é o Agente Comunicador do sistema MOVA-SE.
Sua função é gerar um relatório narrativo em português amigável e motivador para um atleta,
com base nos dados da rota planejada, do clima e da infraestrutura.

DADOS TÉCNICOS COLETADOS:
{dados_json}

Escreva um relatório com 3 a 4 parágrafos curtos:
1. Saudação e resumo da rota (distância, modalidade, horário, ponto de partida).
2. Dicas de saúde e segurança baseadas na previsão do tempo e nos alertas climáticos (ex: vento, UV, chuva).
3. Informe de maneira clara que o mapa detalhado com a infraestrutura foi gerado.

Não inclua pensamentos, tags XML, ou textos soltos antes ou depois do relatório. Apenas o relatório final legível.
"""

    try:
        resposta = llm.invoke(prompt)
        return {"relatorio_narrativo": str(resposta.content).strip()}
    except Exception as e:
        print(f"Alerta: Erro na chamada do Ollama local ({e}). Usando fallback heurístico.")
        dist = estado.get("distancia_real_calculada", requisitos.get("distancia_alvo_km", 10.0))
        ponto = requisitos.get("ponto_partida", "Parque Ibirapuera")
        horario = requisitos.get("janela_temporal", "08:00")
        
        clima_resumo = estado.get("relatorio_clima", "Verifique as condições climáticas locais.")
        
        fallback_texto = (
            f"[Fallback] Olá! Preparado para a sua atividade física?\n\n"
            f"Sua rota começará em {ponto} com uma distância alvo de {dist} km. "
            f"O horário programado é {horario}.\n\n"
            f"Previsão do Tempo: {clima_resumo}\n\n"
            f"O mapa com a análise da infraestrutura viária foi gerado com sucesso para a sua segurança. "
            f"Mantenha-se hidratado e aproveite o percurso!"
        )
        return {"relatorio_narrativo": fallback_texto}
