import pandas as pd
import provinciamascercana as pmc

import sys
from pathlib import Path

# Path de datasets
directory = Path(__file__).resolve()
config_path = directory.parent.parent 

#sys.path.append(str(config_path / "datasets" / "processed/") )
path = config_path / "datasets" / "processed"

qtype = { "RTV": "merged_DTM.csv",
         "DTM": "merged_RTV.csv"
    }

abbreviations_dict = {'BS AS': 'BUENOS AIRES',
                      'BSAS' : 'BUENOS AIRES',
                      'CABA' : 'CIUDAD AUTONOMA DE BUENOS AIRES',
                      'STA FE' : 'SANTA FE'}



# Funciones

# Validacion de input:
def val(location, colname, query_type, provincia = None):
    
    # Limpiamos el input
    input = pmc.normalizar_texto(location)
    
    # Chequeo si el input es una abreviacion
    if input in abbreviations_dict.keys():
        input = abbreviations_dict[input]
    else: pass
    
    # Busco match en mis datos
    df = pd.read_csv( str(path / qtype[query_type]))
    
    if provincia is not None:
          match = pmc.encontrar_provincia_mas_cercana(input, df.loc[df['Provincia']==provincia][colname] )
    else: match = pmc.encontrar_provincia_mas_cercana(input, df[colname])
    
    
    return match
        
# Busqueda de resultados
def search(query_type, provincia, departamento = None, localidad = None ):
    
    # Abro el dataset correspondiente:
    df = pd.read_csv( str(path / qtype[query_type]))
    
    # Creo mascara
    filter_mask = (df['Provincia'] == provincia)
    
    if departamento is not None:
        filter_mask &= df['Departamento / Partido'] == departamento
    
    if localidad is not None:
        filter_mask &= df['localidad'] == localidad               
    
    res = df[filter_mask]
    
    # chequeo que haya al menos 1 resultado
    if res.shape[0] >= 1:
        return res
    else: return
    

    
        