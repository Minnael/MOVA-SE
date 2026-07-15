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
    dados_json = json.dumps(requisitos, indent=2, ensure_ascii=False)

    prompt = f"""Você é o Agente Comunicador do sistema MOVA-SE.
Sua função é gerar um relatório narrativo em português amigável e motivador para um atleta, 
com base nos dados da rota planejada.

DADOS DA ROTA:
{dados_json}

Escreva um relatório com 2 a 3 parágrafos curtos explicando a rota, o horário, a distância e dando dicas de preparação.
Não inclua pensamentos, tags XML, ou textos soltos antes ou depois do relatório. Apenas o relatório final legível.
"""

    try:
        resposta = llm.invoke(prompt)
        return {"relatorio_narrativo": str(resposta.content).strip()}
    except Exception as e:
        print(f"Alerta: Erro na chamada do Ollama local ({e}). Usando fallback heurístico.")
        dist = requisitos.get("distancia_alvo_km", 10.0)
        ponto = requisitos.get("ponto_partida", "Parque Ibirapuera")
        horario = requisitos.get("janela_temporal", "08:00")
        
        fallback_texto = (
            f"[Fallback] Olá! Preparado para a sua atividade física?\n\n"
            f"Sua rota começará em {ponto} com uma distância alvo de {dist} km. "
            f"O horário programado é {horario}. Lembre-se de conferir as condições "
            f"físicas e climáticas antes de começar, manter-se hidratado e aproveitar o percurso!"
        )
        return {"relatorio_narrativo": fallback_texto}
