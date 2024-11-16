import pandas as pd
import spacy
import pickle
from transformers import AutoTokenizer, AutoModel, pipeline
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
PATH_TO_TRAIN = os.path.abspath('..') + "/datasets/textorag/grafo_hierarquia.json"

# Initialize SpaCy and Hugging Face Models
logging.info("Loading SpaCy and Hugging Face models for entity recognition and embeddings.")
nlp = spacy.load("es_core_news_sm")  # Spanish model for entity recognition
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
model = AutoModel.from_pretrained("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Load and initialize a local open-source LLM for response generation
generation_model_name = "PlanTL-GOB-ES/gpt2-base-bne"  # Change to any open-source model of choice
gen_tokenizer = AutoTokenizer.from_pretrained(generation_model_name)
gen_model = pipeline("text-generation",
                     model=generation_model_name,
                     tokenizer=gen_tokenizer,
                     device=0)  # set device to 0 if using GPU

# Seteamos torch en gpu si esta disponible
device = "GPU" if torch.cuda.is_available() else "cpu"

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

df['texto'] = df.apply(lambda row: f"El producto {row['Producto']} combate a la plaga \
                       {row['Plaga']} y se usa en el cultivo {row['Cultivo']}, y \
                       {row['Momento de aplicación']}.", axis=1) 
# Creamos corpus y lo guardamos en un .txt
documents = [f'"{texto}."' for texto in df['texto']]

with open("./textorag/corpus.txt", "w", encoding="utf-8") as f:
    f.writelines([texto + "\n" for texto in documents])

### Step 3: Definimos modelo vectorizador
logging.info("Vectorizando corpus")
vectorizer = TfidfVectorizer()
doc_vectors = vectorizer.fit_transform(documents)


### Step 4: Guardamos corpus vectorizado y vectorizer.

# Ensure the directory exists
os.makedirs("./textorag", exist_ok=True)

logging.info("Saving vectorized corpus & Vectorizer.")
with open("./textorag/tfidf_vectorizer_and_vectors.pkl", "wb") as f:
    pickle.dump((vectorizer, doc_vectors), f)
    








'''
### Step 3: Entity Recognition and Preprocessing
def preprocess_query(query):
    logging.info(f"Preprocessing query: '{query}'")
    doc = nlp(query)
    entities = [ent.text for ent in doc.ents]  # Extract entities
    tokens = [token.lemma_ for token in doc if not token.is_stop]
    cleaned_query = " ".join(tokens)
    logging.info(f"Extracted entities: {entities}")
    logging.info(f"Cleaned query: '{cleaned_query}'")
    return cleaned_query, entities

### Step 4: Embedding and Similarity Search
def get_embedding(text):
    logging.info(f"Generating embedding for texts:")
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        embeddings = model(**inputs).last_hidden_state.mean(dim=1)
    return embeddings

logging.info("Calculating embeddings for product descriptions.")
df["embedding"] = df["composite_description"].apply(lambda x: get_embedding(x))

def find_best_match(query_embedding, df):
    logging.info("Finding the best match for the query embedding.")
    embeddings = torch.vstack(df["embedding"].tolist())
    similarities = cosine_similarity(query_embedding.numpy(), embeddings.numpy())
    best_match_idx = similarities.argmax()
    logging.info(f"Best match index: {best_match_idx}")
    return df.iloc[best_match_idx]

### Step 5: Local Model Response Generation
def generate_response(query, product_info, applic_period):
    logging.info("Generating response using local LLM.")
    prompt = (f"Consulta: {query}\n\n"
              f"Producto sugerido: {product_info}\n\n"
              f"Periodo de aplicación: {applic_period}\n\n"
              "Proporciona una respuesta detallada para el cliente.")
    
    response = gen_model(prompt, max_length=150, num_return_sequences=1)
    logging.info("Response generation completed.")
    return response[0]["generated_text"]

### Step 6: Query Pipeline
def process_query(query, df):
    logging.info("Starting query processing pipeline.")
    cleaned_query, entities = preprocess_query(query)
    query_embedding = get_embedding(cleaned_query)
    best_match = find_best_match(query_embedding, df)
    product_info = best_match["bait"]
    applic_period = best_match["dsc_applic_period"]
    response = generate_response(query, product_info, applic_period)
    logging.info("Query processing completed.")
    return response

### Example Usage
#query = "¿Cuál es el mejor producto para combatir la mosca blanca en esta temporada?"
query = "Que recomienda para tratar sorgo de alepo en soja? "
response = process_query(query, df)
print("Chatbot response:", response)

'''