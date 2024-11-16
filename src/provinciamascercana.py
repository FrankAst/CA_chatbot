import unicodedata
from Levenshtein import distance as levenshtein_distance


def normalizar_texto(texto):
    
    """
    Normaliza el texto eliminando tildes y caracteres especiales.
    
    """
    texto_normalizado = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto_normalizado.upper()  # Convertir a mayúsculas


def encontrar_provincia_mas_cercana(texto, locations,umbral=3):
    """
    Encuentra la provincia más cercana a partir del texto ingresado utilizando la distancia de Levenshtein.
    
    """
    texto_normalizado = normalizar_texto(texto)
    mejor_coincidencia = None
    menor_distancia = float('inf')

    for loc in locations:
        loc_normalizada = normalizar_texto(loc)
        distancia = levenshtein_distance(texto_normalizado, loc_normalizada)
        
        if distancia < menor_distancia and distancia <= umbral:
            menor_distancia = distancia
            mejor_coincidencia = loc
        

    return mejor_coincidencia




