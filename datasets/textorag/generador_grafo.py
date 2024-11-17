import networkx as nx
import pandas as pd
import json

# Cargar los datos desde el archivo CSV
data = pd.read_csv("productos.csv", delimiter=";")

# Crear el grafo dirigido para representar la jerarquía
G = nx.DiGraph()

# Agregar nodos y relaciones jerárquicas basadas en las columnas
for _, row in data.iterrows():
    # Crear nodo de cultivo si no existe
    G.add_node(row['nme_crop'], tipo="cultivo")
    
    # Crear nodo de producto si no existe
    if row['nme_product'] not in G:
        G.add_node(row['nme_product'], tipo="producto")
    G.add_edge(row['nme_crop'], row['nme_product'], relacion="tiene_producto")
    
    # Crear nodos de plaga y aplicación
    if row['nme_target_scientific'] not in G:
        G.add_node(row['nme_target_scientific'], tipo="plaga")
    G.add_edge(row['nme_product'], row['nme_target_scientific'], relacion="controla")

    # Crear nodo para momento de aplicación si no es NaN
    if pd.notna(row['dsc_applic_period']):
        G.add_node(row['dsc_applic_period'], tipo="aplicacion")
        G.add_edge(row['nme_target_scientific'], row['dsc_applic_period'], relacion="momento_aplicacion")

# Convertir el grafo a formato JSON jerárquico
grafo_json = {}

# Iterar sobre los nodos y construir la estructura JSON
for node in G.nodes:
    tipo = G.nodes[node]['tipo']
    
    if tipo == "cultivo":
        # Crear la estructura para cada cultivo
        if node not in grafo_json:
            grafo_json[node] = {"Productos": {}}
    
    elif tipo == "producto":
        # Agregar cada producto al cultivo correspondiente
        for parent in G.predecessors(node):
            if parent not in grafo_json:
                grafo_json[parent] = {"Productos": {}}
            if node not in grafo_json[parent]["Productos"]:
                grafo_json[parent]["Productos"][node] = {"Controla a": {}}

    elif tipo == "plaga":
        # Agregar cada plaga al producto correspondiente
        for parent in G.predecessors(node):
            for grandparent in G.predecessors(parent):
                # Asegurarse de que las claves existen
                if grandparent not in grafo_json:
                    grafo_json[grandparent] = {"Productos": {}}
                if parent not in grafo_json[grandparent]["Productos"]:
                    grafo_json[grandparent]["Productos"][parent] = {"Controla a": {}}
                if node not in grafo_json[grandparent]["Productos"][parent]["Controla a"]:
                    grafo_json[grandparent]["Productos"][parent]["Controla a"][node] = {"Momento de aplicacion": []}
    
    elif tipo == "aplicacion":
        # Agregar el momento de aplicación a la plaga correspondiente
        for parent in G.predecessors(node):
            for grandparent in G.predecessors(parent):
                for ancestor in G.predecessors(grandparent):
                    # Asegurarse de que las claves existen antes de agregar momentos de aplicación
                    if ancestor not in grafo_json:
                        grafo_json[ancestor] = {"Productos": {}}
                    if grandparent not in grafo_json[ancestor]["Productos"]:
                        grafo_json[ancestor]["Productos"][grandparent] = {"Controla a": {}}
                    if parent not in grafo_json[ancestor]["Productos"][grandparent]["Controla a"]:
                        grafo_json[ancestor]["Productos"][grandparent]["Controla a"][parent] = {"Momento de aplicacion": []}
                    grafo_json[ancestor]["Productos"][grandparent]["Controla a"][parent]["Momento de aplicacion"].append(node)

# Guardar la estructura jerárquica en un archivo JSON
with open("grafo_hierarquia.json", "w", encoding="utf-8") as file:
    json.dump(grafo_json, file, indent=4, ensure_ascii=False)

print("Estructura jerárquica guardada en grafo_hierarquia.json")
