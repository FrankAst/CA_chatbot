import pandas as pd
import spacy
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

import pickle
from transformers import AutoTokenizer, AutoModel, pipeline
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer


import torch
from transformers import pipeline

import logging
import os
import json

###################################### Set up ######################################

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Path to dataset
PATH_TO_TRAIN = os.path.abspath('..') + "/CA_chatbot/datasets/textorag/grafo_hierarquia.json"

# Initialize SpaCy and Hugging Face Models
logging.info("Loading SpaCy and Hugging Face models for entity recognition and embeddings.")
nlp = spacy.load("es_core_news_sm")  # Spanish model for entity recognition
stop_words = set(stopwords.words('spanish'))
stemmer = SnowballStemmer('spanish')

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
model = AutoModel.from_pretrained("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


# Seteamos torch en gpu si esta disponible
device = "cuda" if torch.cuda.is_available() else "cpu"

logging.info(f"Torch running on: {device}")

###################################### Main ######################################

### Step 1: Load json
# Cargar el archivo de la jerarquía JSON
with open(PATH_TO_TRAIN, "r", encoding="utf-8") as f:
    grafo_json = json.load(f)

filas = []
for cultivo, info_cultivo in grafo_json.items():
    for producto, info_producto in info_cultivo['Productos'].items():
        for plaga, info_plaga in info_producto['Controla a'].items():
            fila = {
                'Cultivo': cultivo,
                'Producto': producto,
                'Plaga': plaga,
                'Momento de aplicación': ', '.join(info_plaga['Momento de aplicacion'])
            }
            filas.append(fila)

df = pd.DataFrame(filas)


### Step 2: Estandarizacion de strings
logging.info("Creacion corpus")

df['Producto'] = df['Producto'].str.lower()
df['Plaga'] = df['Plaga'].str.lower()
df['Cultivo'] = df['Cultivo'].str.lower()
df['Momento de aplicación'] = df['Momento de aplicación'].str.lower()

df['texto'] = df.apply(
    lambda row: (
        f"El producto {row['Producto']} combate a la plaga {row['Plaga']} "
        f"y se usa en el cultivo {row['Cultivo']}, y {row['Momento de aplicación']}."
    ),
    axis=1
)


# Creamos corpus y lo guardamos en un .txt
documents = [f'"{texto}."' for texto in df['texto']]


# Ensure the directory exists
os.makedirs("./datasets/textorag", exist_ok=True)

with open("./datasets/textorag/corpus.txt", "w", encoding="utf-8") as f:
    f.writelines([texto + "\n" for texto in documents])


### Step 3: Definimos modelo vectorizador
logging.info("Vectorizando corpus")

vectorizer = SentenceTransformer("distiluse-base-multilingual-cased-v1", device = device)
doc_vectors = vectorizer.encode(documents)



### Step 4: Guardamos corpus vectorizado y vectorizer.

logging.info("Saving vectorized corpus & Vectorizer.")
with open("./datasets/textorag/tfidf_vectorizer_and_vectors.pkl", "wb") as f:
    pickle.dump((vectorizer, doc_vectors), f)
    


########################################### TO implement #########################################
# Tokenize + stop words + Stemming.
logging.info("Removing stop words and stemming corpus")
def preprocess(text):
    # Tokenizar la consulta
    doc = nlp(text)
    # Stemming y eliminación de stopwords
    stemmed_tokens = [
        stemmer-.stem(token.text.lower())
        for token in doc
        if token.text.lower() not in stop_words and not token.is_punct
    ]
    return " ".join(stemmed_tokens)
