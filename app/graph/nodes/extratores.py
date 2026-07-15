"""Nós de extração — desmembram o texto livre do usuário em campos estruturados.

São três funções-nó que rodam **em paralelo** a partir do START do grafo. Cada
uma lê ``texto_descritivo`` e escreve apenas a sua chave no estado, de modo que
não há conflito de escrita concorrente entre elas. O nó Orquestrador consolida
os três resultados depois (fan-in).

Os três já usam LLM real (MiniMax-M3 via LangChain). ``extrair_horario`` ainda
combina o modelo com a biblioteca ``dateparser`` para resolver datas relativas.
"""

from __future__ import annotations

import json
import re
from datetime import datetime

import dateparser

from app.graph.state import EstadoAgentico
from app.llm import get_llm
from app.graph.nodes.geocoordinates_getter import obter_coordenadas

_SYSTEM_DISTANCIA = (
    "Você extrai a distância-alvo do percurso, em quilômetros, do texto do usuário. "
    "Converta metros ou milhas para km quando necessário. " #tool de metros para km 
    "Responda apenas com o número em km, usando ponto como separador decimal."
)

_SYSTEM_LUGAR = (
    "Você extrai o nome do lugar de partida do percurso a partir do texto do usuário "
    "(bairro, parque, endereço ou cidade). "
    "Responda apenas com o nome do lugar, sem explicações."
)

_SYSTEM_HORARIO = (
    "Extraia a informação temporal do texto do usuário, separando data e hora. "
    'Responda APENAS em JSON: {"data": <expressão ou null>, "hora": <"HH:MM" ou null>}. '
    "Em 'data' devolva a expressão como aparece no texto (ex.: 'amanhã', 'próxima segunda', "
    "'20/08'); use null se não houver data. Em 'hora' use null se não houver hora explícita."
)
_RE_JSON = re.compile(r"\{.*\}", re.DOTALL)
_DP_SETTINGS = {
    "PREFER_DATES_FROM": "future",
    "DATE_ORDER": "DMY",
    "RETURN_AS_TIMEZONE_AWARE": False,
}

# MiniMax-M3 é um modelo de raciocínio: emite um bloco <think>...</think> antes
# da resposta. Removemos esse bloco e extraímos o número do restante.
_RE_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_RE_NUMERO = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


def extrair_lugar(estado: EstadoAgentico) -> dict:
    """Extrai o nome do lugar de partida do texto via LangChain + MiniMax-M3."""
    import os
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key or api_key == "dummy_key":
        # Fallback local sem LLM
        match = re.search(
            r"(?:no|na|em|para o|para a)\s+([A-Z\u00C0-\u00DC][a-zA-Z\u00C0-\u00FC\s',]+?)(?:\s+no|\s+às|\s+as|\s+domingo|\s+sábado|\s+para|$)",
            estado["texto_descritivo"]
        )
        if match:
            lugar = match.group(1).strip()
        else:
            lugar = "Parque Ibirapuera, São Paulo"
            
        coords = obter_coordenadas(lugar)
        if not isinstance(coords, tuple):
            coords = (-23.5874, -46.6576) # Fallback Ibirapuera
        return {"lugar": lugar, "coordenadas": coords}

    resposta = get_llm().invoke(
        [("system", _SYSTEM_LUGAR), ("human", estado["texto_descritivo"])]
    )
    lugar = _RE_THINK.sub("", str(resposta.content)).strip().strip("\"'")
    if not lugar:
        raise ValueError("Não foi possível extrair o lugar do texto.")
        
    coords = obter_coordenadas(lugar)
    if not isinstance(coords, tuple):
        raise ValueError(f"Não foi possível geocodificar o lugar: {lugar!r}")
        
    return {"lugar": lugar, "coordenadas": coords}


def extrair_distancia(estado: EstadoAgentico) -> dict:
    """Extrai a distância-alvo (km) do texto via LangChain + MiniMax-M3."""
    import os
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key or api_key == "dummy_key":
        # Fallback local sem LLM para desenvolvimento fácil sem chave
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:km|quilometros|quilômetros)", estado["texto_descritivo"], re.IGNORECASE)
        if match:
            return {"distancia_alvo_km": float(match.group(1).replace(",", "."))}
        return {"distancia_alvo_km": 10.0}

    resposta = get_llm().invoke(
        [("system", _SYSTEM_DISTANCIA), ("human", estado["texto_descritivo"])]
    )
    texto = _RE_THINK.sub("", str(resposta.content)).strip()
    match = _RE_NUMERO.search(texto)
    if match is None:
        raise ValueError(f"Não foi possível extrair a distância de: {texto!r}")
    return {"distancia_alvo_km": float(match.group().replace(",", "."))}


def extrair_horario(estado: EstadoAgentico) -> dict:
    """Extrai data (via dateparser) e hora do texto; rejeita momentos no passado."""
    import os
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key or api_key == "dummy_key":
        from datetime import timedelta
        # Fallback local sem LLM
        texto = estado["texto_descritivo"].lower()
        hora = "08:00"
        if " 7 " in texto or "às 7" in texto or "as 7" in texto or "7h" in texto:
            hora = "07:00"
        elif " 8 " in texto or "às 8" in texto or "as 8" in texto or "8h" in texto:
            hora = "08:00"
        elif " 9 " in texto or "às 9" in texto or "as 9" in texto or "9h" in texto:
            hora = "09:00"

        agora = datetime.now()
        data = agora.date()
        if "domingo" in texto:
            dias = (6 - agora.weekday()) % 7
            if dias == 0:
                dias = 7
            data = (agora + timedelta(days=dias)).date()
        elif "sábado" in texto or "sabado" in texto:
            dias = (5 - agora.weekday()) % 7
            if dias == 0:
                dias = 7
            data = (agora + timedelta(days=dias)).date()
        elif "amanhã" in texto or "amanha" in texto:
            data = (agora + timedelta(days=1)).date()

        return {"data_inicio": data.isoformat(), "horario_inicio": hora}

    resposta = get_llm().invoke(
        [("system", _SYSTEM_HORARIO), ("human", estado["texto_descritivo"])]
    )
    bruto = _RE_THINK.sub("", str(resposta.content)).strip()
    achado = _RE_JSON.search(bruto)
    dados = json.loads(achado.group()) if achado else {}

    agora = datetime.now()
    expr_data, hora = dados.get("data"), dados.get("hora")

    # Data: resolve a expressão via dateparser; se ausente, assume hoje.
    if expr_data:
        resolvido = dateparser.parse(
            expr_data,
            languages=["pt"],
            settings={**_DP_SETTINGS, "RELATIVE_BASE": agora},
        )
        if resolvido is None:
            raise ValueError(f"Não foi possível interpretar a data: {expr_data!r}")
        data = resolvido.date()
    else:
        data = agora.date()

    # Hora: valida formato "HH:MM"; caso inválido, trata como ausente.
    if hora:
        try:
            datetime.strptime(hora, "%H:%M")
        except ValueError:
            hora = None

    # Rejeita momentos no passado.
    if hora:
        if datetime.combine(data, datetime.strptime(hora, "%H:%M").time()) < agora:
            raise ValueError(f"O horário informado está no passado: {data} {hora}")
    elif data < agora.date():
        raise ValueError(f"A data informada está no passado: {data}")

    return {"data_inicio": data.isoformat(), "horario_inicio": hora}
