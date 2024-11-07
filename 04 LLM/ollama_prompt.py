# Bajar: https://github.com/ollama/ollama/tree/main
#pip install -U langchain-community
#pip install streamlit

#Para ejecutar en el pormpt: streamlit run ollama_prompt.py


import streamlit as st
from langchain.llms import Ollama

llm = Ollama(model="llama2:latest")

colA, colB = st.columns([.90, .10])
with colA:
    prompt = st.text_input("Prompt", value="", key="prompt")

response = ""

with colB:
    st.markdown("")
    if st.button("Click", key="button"):
        response = llm.predict(prompt)
st.markdown(response)
