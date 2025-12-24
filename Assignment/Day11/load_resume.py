import os
import streamlit as st
import chromadb
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings import init_embeddings
from langchain.chat_models import init_chat_model

# ================= ENV =================
load_dotenv()

# ================= STREAMLIT CONFIG =================
st.set_page_config(
    page_title="Resume Refiner",
    page_icon="🤖",
    layout="centered"
)

# ================= SESSION STATE =================
if "db_initialized" not in st.session_state:
    st.session_state.db_initialized = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "context_docs" not in st.session_state:
    st.session_state.context_docs = []

# ================= LLM =================
llm = init_chat_model(
    model="phi-3.1-mini-4k-instruct",
    model_provider="openai",
    base_url="http://127.0.0.1:1234/v1",
    api_key="not-needed"
)

# ================= EMBEDDINGS =================
embed_model = init_embeddings(
    model="text-embedding-nomic-embed-text-v1.5-embedding",
    provider="openai",
    base_url="http://127.0.0.1:1234/v1",
    api_key="not-needed",
    check_embedding_ctx_length=False
)

# ================= TEXT SPLITTER =================
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=60
)

# ================= PDF LOADER =================
dir_loader = DirectoryLoader(
    path=r"D:\Sunbeam\IIT-Gen-AI-94443\Assignment\Day11\fake resume",
    glob="*.pdf",
    loader_cls=PyPDFLoader
)

# ================= DISPLAY CHAT HISTORY =================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ================= LOAD & STORE RESUMES =================
def load_pdf_resumes():
    return dir_loader.load()

if not st.session_state.db_initialized:
    with st.spinner("Loading resumes and creating vector DB..."):
        documents = load_pdf_resumes()
        chunks = text_splitter.split_documents(documents)
        texts = [chunk.page_content for chunk in chunks]

        embeddings = embed_model.embed_documents(texts)

        chroma_client = chromadb.PersistentClient(path="./Resume_base")
        collection = chroma_client.get_or_create_collection(
            name="Resume_collection"
        )

        ids = [f"resume_{i}" for i in range(len(texts))]
        metadatas = []

        for i, chunk in enumerate(chunks):
            meta = chunk.metadata.copy()
            meta["chunk_id"] = i
            metadatas.append(meta)

        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        st.session_state.context_docs.append(
        f"Resume Source: {documents}\nContent: {texts}"
        )

        st.session_state.collection = collection
        st.session_state.db_initialized = True

    st.success("Vector database created successfully!")

# ================= USER INPUT =================
user_query = st.chat_input("Ask about resumes (type 'clear' to reset)")

if user_query:
    # Clear chat
    if user_query.lower() == "clear":
        st.session_state.messages = []
        st.session_state.context_docs = []
        st.experimental_rerun()

    # Save user message
    st.session_state.messages.append(
        {"role": "user", "content": user_query}
    )

    with st.chat_message("user"):
        st.markdown(user_query)

    # ================= SIMILARITY SEARCH =================
    query_embedding = embed_model.embed_query(user_query)

    results = st.session_state.collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    st.session_state.context_docs = []

    
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        source = meta.get("source", "Unknown PDF")
        chunk_text = doc[:300]
        st.session_state.context_docs.append(chunk_text)

    # ================= PROMPT =================
    prompt = f"""
You are a resume identification assistant.

TASK:
Identify the  persons who best matches the user's query.

RULES:
1. Use ONLY the resume information provided in the CONTEXT.
2. Select ONLY relevant resume.
3. Do NOT compare multiple candidates.
4. Do NOT add extra explanation.
5. If no clear match exists, respond exactly:
   "No matching resume found."

CONTEXT (Resume Data):
{st.session_state.context_docs}

USER QUERY:
{user_query}

ANSWER FORMAT (STRICT):
This person is a <role/skill> expert according to the resume: <Resume Source>.
"""



    # ================= LLM RESPONSE =================
    with st.chat_message("assistant"):
        response = llm.invoke(prompt)
        st.markdown(response.content)

    st.session_state.messages.append(
        {"role": "assistant", "content": response.content}
    )


