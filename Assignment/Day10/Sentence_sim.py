from sentence_transformers import SentenceTransformer
import numpy as np
import streamlit as st

st.title("Sentence similarity")

def consine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

embed_model = SentenceTransformer("all-MiniLM-L6-v2")
sentences=[]
for i in range(0,3):
    sen=st.chat_input(f"Enter {i+1} Sentence")
    sentences.append(sen)

emebeddings = embed_model.encode(sentences)

for embed_vect in emebeddings:
    st.write("Len:", len(embed_vect), " --> ", embed_vect[:4])

st.write("Sentence 1 & 2 similarity:", consine_similarity(emebeddings[0], emebeddings[1]))
st.write("Sentence 1 & 3 similarity:", consine_similarity(emebeddings[0], emebeddings[2]))
