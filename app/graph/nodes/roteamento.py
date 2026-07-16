"""Nó do Agente 4 — Matemático de Redes / Motor de Roteamento.

Responsável por carregar o grafo de ruas (com pesos Se e Ie), aplicar a fórmula
de custo matemático e gerar o melhor trajeto de ida e volta, minimizando riscos
urbanos. Desenha e salva o mapa interativo usando Folium.
"""

from __future__ import annotations

import math
import os
import networkx as nx
import osmnx as ox
import folium

from app.graph.state import EstadoAgentico

def aplicar_motor_roteamento(estado: EstadoAgentico) -> dict:
    """Carrega o grafo, calcula a rota em circuito (ida e volta) e gera o mapa HTML."""
    import uuid
    caminho_grafo = estado.get("caminho_grafo")
    coordenadas = estado.get("coordenadas")
    requisitos = estado.get("requisitos", {})
    
    if not coordenadas or not caminho_grafo:
        raise ValueError("Coordenadas ou grafo ausentes no estado.")
        
    lat, lon = coordenadas
    distancia_alvo = requisitos.get("distancia_alvo_km", 5.0) * 1000.0  # em metros
    perfil_altimetria = requisitos.get("perfil_altimetria", "Moderado")
    
    if not os.path.exists(caminho_grafo):
        raise ValueError(f"Grafo não encontrado: {caminho_grafo}")
        
    # 1. Carrega a rede viária
    print(f"Agente 4: Carregando grafo de {caminho_grafo}...")
    G = ox.load_graphml(caminho_grafo)
    
    # Define o peso da altimetria (alpha) com base no perfil
    if perfil_altimetria == "Plano":
        alpha = 15.0  # Penaliza fortemente subidas/descidas
    elif perfil_altimetria == "Montanhoso" or "Treino" in perfil_altimetria:
        alpha = -2.0  # Favorece inclinações
    else:
        alpha = 3.0   # Moderado
    
    # 2. Modelação Matemática de Pesos
    # W = L * (1 + alpha*E_e + 2.0*Se - 1.5*Ie)
    for u, v, k, data in G.edges(keys=True, data=True):
        length = float(data.get("length", 10.0))
        Se = float(data.get("Se", 0.0))
        Ie = float(data.get("Ie", 0.0))
        grade_abs = float(data.get("grade_abs", 0.0))
        
        # w = custo da aresta. Inclinação aumenta (se plano) ou diminui (se montanhoso)
        w = length * (1.0 + (alpha * grade_abs) + (2.0 * Se) - (1.5 * Ie))
        data["peso_roteamento"] = max(0.1, w)
        
    # 3. Preparação: origem, distâncias (por comprimento) e ângulos dos nós.
    orig_node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
    ox0, oy0 = G.nodes[orig_node]["x"], G.nodes[orig_node]["y"]
    lengths = nx.single_source_dijkstra_path_length(G, orig_node, weight="length")

    def _bearing(node):
        """Ângulo (graus) do nó em relação à origem."""
        dx = G.nodes[node]["x"] - ox0
        dy = G.nodes[node]["y"] - oy0
        return math.degrees(math.atan2(dy, dx)) % 360.0

    def _menor_caminho(grafo, origem, destino):
        try:
            return nx.shortest_path(grafo, origem, destino, weight="peso_roteamento")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def _remover_arestas(grafo, rota):
        for i in range(len(rota) - 1):
            u, v = rota[i], rota[i + 1]
            for a, b in ((u, v), (v, u)):
                if grafo.has_edge(a, b):
                    for k in list(grafo[a][b].keys()):
                        grafo.remove_edge(a, b, k)

    def _dist_m(rota):
        """Comprimento total (m) de uma rota (soma dos ``length`` das arestas)."""
        total = 0.0
        for i in range(len(rota) - 1):
            ed = G.get_edge_data(rota[i], rota[i + 1])
            if ed:
                total += min(float(d.get("length", 0.0)) for d in ed.values())
        return total

    def _construir_circuito(perna):
        """CIRCUITO triangular origem -> A -> B -> origem, pernas ~'perna' (m).

        A e B ficam a ~1 perna da origem, em direções ~135° separadas (bearing),
        para "abrir" o triângulo; cada trecho remove as ruas já usadas para não
        sobrepor a ida.
        """
        cands = [(n, d) for n, d in lengths.items() if n != orig_node and abs(d - perna) <= perna]
        if not cands:
            cands = [(n, d) for n, d in lengths.items() if n != orig_node]
        if not cands:
            return [orig_node]
        node_a = min(cands, key=lambda nd: abs(nd[1] - perna))[0]
        alvo_b = (_bearing(node_a) + 135.0) % 360.0
        perto = [nd for nd in cands if abs(nd[1] - perna) <= perna * 0.6] or cands
        node_b = min(perto, key=lambda nd: abs((_bearing(nd[0]) - alvo_b + 180.0) % 360.0 - 180.0))[0]

        G_rest = G.copy()
        rota = [orig_node]
        for destino in (node_a, node_b, orig_node):
            origem = rota[-1]
            if destino == origem:
                continue
            trecho = _menor_caminho(G_rest, origem, destino) or _menor_caminho(G, origem, destino)
            if not trecho or len(trecho) < 2:
                continue
            _remover_arestas(G_rest, trecho)
            rota.extend(trecho[1:])
        return rota

    # 4. Itera a 'perna' até o comprimento total ficar perto da distância-alvo
    # (tolerância de 15%), mantendo o formato de laço. Guarda o melhor resultado.
    tolerancia = 0.15
    perna = distancia_alvo / 3.0
    rota_completa, distancia_real, melhor_erro = [orig_node], 0.0, float("inf")
    for _ in range(6):
        rota = _construir_circuito(perna)
        dist = _dist_m(rota)
        erro = abs(dist - distancia_alvo) / distancia_alvo if distancia_alvo else 0.0
        if erro < melhor_erro:
            rota_completa, distancia_real, melhor_erro = rota, dist, erro
        if erro <= tolerancia or dist <= 0:
            break
        # Ajuste amortecido: escala a perna pela razão alvo/obtido.
        perna *= max(0.5, min(2.0, distancia_alvo / dist))
    print(f"Agente 4: circuito com {len(rota_completa)} nós, erro {melhor_erro * 100:.0f}% do alvo.")

    # 5. Extração Geométrica e Métricas
    coordenadas_rota = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in rota_completa]
    distancia_real_km = round(distancia_real / 1000.0, 2)
    
    # 6. Renderização de Artefato Geoespacial (Mapa)
    m = folium.Map(location=[lat, lon], zoom_start=14)
    if coordenadas_rota:
        folium.PolyLine(coordenadas_rota, color="blue", weight=5, opacity=0.8).add_to(m)
        folium.Marker(coordenadas_rota[0], popup="Partida/Chegada", icon=folium.Icon(color='green')).add_to(m)
        
    pasta_data = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))
    sessao_id = uuid.uuid4().hex[:8]
    nome_arquivo = f"mapa_rota_{sessao_id}.html"
    caminho_mapa = os.path.join(pasta_data, nome_arquivo)
    m.save(caminho_mapa)
    
    print(f"Agente 4: Mapa salvo em {caminho_mapa}. Distância total: {distancia_real_km}km.")
    
    return {
        "coordenadas_rota": coordenadas_rota,
        "caminho_mapa_html": caminho_mapa,
        "distancia_real_calculada": distancia_real_km
    }
