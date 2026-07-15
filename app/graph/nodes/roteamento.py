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
    """Carrega o grafo, calcula a rota out-and-back e gera o mapa HTML."""
    caminho_grafo = estado.get("caminho_grafo")
    coordenadas = estado.get("coordenadas")
    
    if not coordenadas or not caminho_grafo:
        raise ValueError("Coordenadas ou grafo ausentes no estado.")
        
    lat, lon = coordenadas
    distancia_alvo = estado["requisitos"]["distancia_alvo_km"] * 1000.0  # em metros
    
    if not os.path.exists(caminho_grafo):
        raise ValueError(f"Grafo não encontrado: {caminho_grafo}")
        
    # 1. Carrega a rede viária
    print(f"Agente 4: Carregando grafo de {caminho_grafo}...")
    G = ox.load_graphml(caminho_grafo)
    
    # 2. Modelação Matemática de Pesos
    # W = L * (1 + 2.0*Se - 1.5*Ie)
    for u, v, k, data in G.edges(keys=True, data=True):
        length = float(data.get("length", 10.0))
        Se = float(data.get("Se", 0.0))
        Ie = float(data.get("Ie", 0.0))
        
        w = length * (1.0 + 2.0 * Se - 1.5 * Ie)
        data["peso_roteamento"] = max(0.1, w)
        
    # 3. Busca do Destino
    orig_node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
    target_dist = distancia_alvo / 2.0
    
    lengths = nx.single_source_dijkstra_path_length(G, orig_node, weight="length")
    
    best_node = None
    best_diff = float("inf")
    
    # Procura um nó que fique exatamente a metade da distância desejada para bater a km exata ida e volta
    for node, dist in lengths.items():
        if node != orig_node:
            diff = abs(dist - target_dist)
            if diff < best_diff:
                best_diff = diff
                best_node = node
                
    if best_node is None:
        best_node = orig_node
        
    # 4. Cálculo da Rota Otimizada (Ida e Volta)
    try:
        rota_ida = nx.shortest_path(G, orig_node, best_node, weight="peso_roteamento")
    except nx.NetworkXNoPath:
        rota_ida = [orig_node]
        
    try:
        rota_volta = nx.shortest_path(G, best_node, orig_node, weight="peso_roteamento")
    except nx.NetworkXNoPath:
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
            # Em multigrafos pode haver mais de uma aresta entre u e v, pega a mais curta
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
    caminho_mapa = os.path.join(pasta_data, "mapa_rota.html")
    m.save(caminho_mapa)
    
    print(f"Agente 4: Mapa salvo em {caminho_mapa}. Distância total: {distancia_real_km}km.")
    
    return {
        "coordenadas_rota": coordenadas_rota,
        "caminho_mapa_html": caminho_mapa,
        "distancia_real_calculada": distancia_real_km
    }
