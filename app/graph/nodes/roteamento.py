"""Nó do Agente 4 — Matemático de Redes / Motor de Roteamento.

Responsável por carregar o grafo de ruas (com pesos Se e Ie), aplicar a fórmula
de custo matemático e gerar o melhor trajeto de ida e volta, minimizando riscos
urbanos. Desenha e salva o mapa interativo usando Folium.
"""

from __future__ import annotations

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
        
    # 3. Busca do Destino (ponto de retorno)
    orig_node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
    target_dist = distancia_alvo / 2.0
    
    lengths = nx.single_source_dijkstra_path_length(G, orig_node, weight="length")
    
    best_node = None
    best_diff = float("inf")
    
    # Encontrar o nó mais próximo da metade da distância alvo
    for node, dist in lengths.items():
        if node != orig_node:
            diff = abs(dist - target_dist)
            if diff < best_diff:
                best_diff = diff
                best_node = node
                
    if best_node is None:
        best_node = orig_node
        
    # 4. Cálculo da Rota Otimizada em Circuito (Loop Heuristic)
    try:
        rota_ida = nx.shortest_path(G, orig_node, best_node, weight="peso_roteamento")
    except nx.NetworkXNoPath:
        rota_ida = [orig_node]
        
    # Penalizar as arestas da ida para forçar um caminho de volta diferente (Circuito Fechado)
    G_volta = G.copy()
    if len(rota_ida) > 1:
        for i in range(len(rota_ida) - 1):
            u = rota_ida[i]
            v = rota_ida[i+1]
            if G_volta.has_edge(u, v):
                for k in G_volta[u][v]:
                    G_volta[u][v][k]["peso_roteamento"] *= 100.0  # Punição severa
            # Caso seja grafo direcionado e a via tenha sentido duplo, punimos a volta também
            if G_volta.has_edge(v, u):
                for k in G_volta[v][u]:
                    G_volta[v][u][k]["peso_roteamento"] *= 100.0
            
    try:
        rota_volta = nx.shortest_path(G_volta, best_node, orig_node, weight="peso_roteamento")
    except nx.NetworkXNoPath:
        try:
            # Fallback 1: Retorna pela mesma rota original se for forçado
            rota_volta = nx.shortest_path(G, best_node, orig_node, weight="peso_roteamento")
        except nx.NetworkXNoPath:
            # Fallback 2: Grafo sem volta possível (rua sem saída direcional)
            print("Agente 4: Alerta - Rota de volta impossível no grafo atual.")
            rota_volta = [best_node]
            
    rota_completa = rota_ida + rota_volta[1:] if len(rota_volta) > 1 else rota_ida
    
    # 5. Extração Geométrica e Métricas
    coordenadas_rota = []
    distancia_real = 0.0
    
    for i in range(len(rota_completa) - 1):
        u = rota_completa[i]
        v = rota_completa[i+1]
        coordenadas_rota.append((G.nodes[u]['y'], G.nodes[u]['x']))
        
        edge_data = G.get_edge_data(u, v)
        if edge_data:
            menor_length = min([float(d.get("length", 0.0)) for d in edge_data.values()])
            distancia_real += menor_length
            
    if rota_completa:
        ultimo_no = rota_completa[-1]
        coordenadas_rota.append((G.nodes[ultimo_no]['y'], G.nodes[ultimo_no]['x']))
        
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
