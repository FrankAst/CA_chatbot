from transformers import AutoTokenizer, pipeline
import spacy
import nltk
from nltk.corpus import stopwords

from sklearn.metrics.pairwise import cosine_similarity
import torch
from transformers import pipeline

import logging
import os
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Seteamos torch en gpu si esta disponible
device = "GPU" if torch.cuda.is_available() else "cpu"

logging.info(f"Torch running on: {device}")

# Path to corpus
PATH_TO_CORPUS= os.path.abspath('..') + "/datasets/textorag/tfidf_vectorizer_and_vectors.pkl"
PATH_TO_CORPUS_TXT = os.path.abspath('..') + "/datasets/textorag/corpus.txt"

# Carga embedding corpus + vectorizer
logging.info("Cargando embedding y vectorizer")
with open(PATH_TO_CORPUS, "rb") as f:
    vectorizer, doc_vectors = pickle.load(f)
    
# Carga de corpus
logging.info("Cargando corpus.txt")
with open(PATH_TO_CORPUS_TXT, "r", encoding="utf-8") as f:
    documents = [line.strip() for line in f]


############################### LEVANTAMOS MODELO ###############################

#generation_model_name = "PlanTL-GOB-ES/gpt2-base-bne"
generation_model_name = "datificate/gpt2-small-spanish"
logging.info(f"LLM seleccionado {generation_model_name}")

gen_tokenizer = AutoTokenizer.from_pretrained(generation_model_name)

gen_model = pipeline("text-generation",
                     model=generation_model_name,
                     #tokenizer=gen_tokenizer,
                     device=0)  # set device to 0 if using GPU

    
############################### PROCESAMIENTO QUERY ###############################  

# Quitamos stop words y lematizamos query.

# Cargar recursos necesarios
nltk.download('stopwords')
stop_words = set(stopwords.words('spanish'))
nlp = spacy.load("es_core_news_sm")

def preprocess_query(query):
    
    logging.info("Procesando query..")
    # Tokenizar y analizar la consulta
    doc = nlp(query)
    # Lematización y eliminación de stopwords
    lemmatized_tokens = [
        token.lemma_
        for token in doc
        if token.text.lower() not in stop_words and not token.is_punct
    ]
    return " ".join(lemmatized_tokens)



############################### RAG ############################### 

# Define RAG functions
def retrieve_document(query, vectorizer, doc_vectors, umbral = 0.10):
    # query: pregunta del cliente
    # vectorizer: vectorizador usado para el embbeding
    # doc_vectors: embbeding de corpus
    
    logging.info(f"Buscando similitudes..")
    # Vectorizo la query:
    query_vector = vectorizer.transform([query])
    
    # Busco similitudes
    similarities = cosine_similarity(query_vector, doc_vectors).flatten()
    
    # Similitud maxima e indice
    similarity_max = similarities.max()
    most_similar_idx = similarities.argmax()
    
    
    # Verificacion de umbral
    if similarity_max < umbral:
            logging.info(f"La distancia hallada es de {round(similarity_max,2)}")
            logging.info(f"No se encontró un documento con similitud mayor a {umbral}.")
            
            return "Not found"
    else:
            logging.info(f"Documento encontrado con similitud {similarity_max:.2f}")
            return documents[most_similar_idx]
    

# RAG:
def rag(query):
    query = preprocess_query(query)
    
    document = retrieve_document(query, vectorizer, doc_vectors)
    
    # Verificamos que el documento supere el umbral establecido
    if document == "Not found": 
        return "No hemos hallado una respuesta adecuada, comuniquese con un experto."
                
    logging.info(f"Generando respuesta")
    answer = gen_model(document,
                       max_length=512,
                       num_return_sequences=1,
                       temperature=0.95,
                       top_k=50,  
                       top_p=0.9)
    
    answer = answer[0]["generated_text"].split('.')[0]
    
    return answer


# TESTEO

#query = "Necesito saber como erradicar el nabo en la soja"
#query = "Como elimino la mosca blanca ayuda"

'''
query = "Que producto combate la isoca bolillera en la soja?"

rta = rag(query)

logging.info(f"Query: {query}")
logging.info(f"Respuesta: {rta}")

'''