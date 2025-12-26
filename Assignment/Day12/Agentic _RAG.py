import os
import streamlit as st
import chromadb
import pandas as pd
from dotenv import load_dotenv
from collections import Counter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings import init_embeddings
from langchain.chat_models import init_chat_model
from langchain.tools import tool
import json

load_dotenv()

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Agentic RAG Resume Refiner", page_icon="🤖", layout="wide")

# ---------------- GLOBAL STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resumes_df" not in st.session_state:
    st.session_state.resumes_df = pd.DataFrame()
if "action" not in st.session_state:
    st.session_state.action = "shortlist"   # default view

# ---------------- MODELS ----------------
@st.cache_resource
def init_models():
    """Initialize chat model and embedding model."""
    llm = init_chat_model(
        model="phi-3.1-mini-4k-instruct",
        model_provider="openai",
        base_url="http://127.0.0.1:1234/v1",
        api_key="not-needed"
    )
    embed_model = init_embeddings(
        model="text-embedding-nomic-embed-text-v1.5-embedding",
        provider="openai",
        base_url="http://127.0.0.1:1234/v1",
        api_key="not-needed",
        check_embedding_ctx_length=False
    )
    return llm, embed_model

llm, embed_model = init_models()

# ---------------- TEXT SPLITTER & VECTOR DB ----------------
text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60)

PERSIST_DIR = "./Resume_base"
COLLECTION_NAME = "Resume_collection"

chroma_client = chromadb.PersistentClient(path=PERSIST_DIR)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

# ---------------- INITIAL LOAD ----------------
@st.cache_data
def load_initial_resumes():
    """Load initial PDF resumes from disk into the Chroma collection (only if collection is empty)."""
    if collection.count() == 0:
        try:
            dir_loader = DirectoryLoader(
                path=r"D:\Sunbeam\IIT-Gen-AI-94443\Assignment\Day11\fake resume",
                glob="*.pdf",
                loader_cls=PyPDFLoader
            )
            documents = dir_loader.load()
            chunks = text_splitter.split_documents(documents)
            texts = [c.page_content for c in chunks]
            embeddings = embed_model.embed_documents(texts)

            ids = [f"resume_{i}" for i in range(len(texts))]
            metadatas = []
            for i, chunk in enumerate(chunks):
                meta = chunk.metadata.copy()
                meta["chunk_id"] = i
                meta["source"] = os.path.basename(meta.get("source", "Unknown"))
                metadatas.append(meta)

            collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
            st.success("✅ Initial resumes loaded!")
            return True
        except Exception as e:
            st.warning(f"Initial load skipped: {e}")
            return False
    return False

load_initial_resumes()

# ---------------- UTILITY FUNCTIONS ----------------
def save_uploaded_file(uploaded_file):
    """Save uploaded Streamlit file to disk and return its path."""
    os.makedirs("./uploads", exist_ok=True)
    filepath = f"./uploads/{uploaded_file.name}"
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

def process_resume_file(filepath):
    """Read a PDF from disk, chunk it, embed it, and store in Chroma with metadata."""
    loader = PyPDFLoader(filepath)
    docs = loader.load()
    chunks = text_splitter.split_documents(docs)
    texts = [c.page_content for c in chunks]
    embeddings = embed_model.embed_documents(texts)

    source_name = os.path.basename(filepath)
    ids = [f"{source_name}_{i}" for i in range(len(texts))]
    metadatas = [{"source": source_name, "chunk_id": i} for i in range(len(chunks))]

    collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
    return f"✅ Successfully stored: {source_name}"

def get_resumes_df():
    """Fetch all distinct resumes from Chroma and store them in session_state as a DataFrame."""
    data = collection.get(include=["documents", "metadatas"])
    rows, seen = [], set()

    for doc, meta, doc_id in zip(data["documents"], data["metadatas"], data["ids"]):
        source = meta.get("source", "Unknown")
        if source not in seen:
            seen.add(source)
            lines = [l.strip() for l in doc.strip().split("\n") if l.strip()]
            name = " ".join(lines[0].split()[:2]) if lines else "Unknown"
            rows.append({"Name": name, "Source": source, "ID": doc_id})

    df = pd.DataFrame(rows)
    st.session_state.resumes_df = df
    return df

# ---------------- TOOL FUNCTIONS ----------------
@tool
def list_all_resumes() -> str:
    """
    Return all resumes from the Chroma collection as JSON string.

    The JSON corresponds to a pandas DataFrame with columns:
    - Name
    - Source
    - ID
    """
    df = get_resumes_df()
    return df.to_json(orient="records")

@tool
def delete_resume(resume_source: str) -> str:
    """
    Delete all vector entries belonging to a resume from the Chroma collection.

    Parameters
    ----------
    resume_source : str
        The resume's file name stored in metadata under key 'source'.

    Returns
    -------
    str
        A success or not-found message.
    """
    data = collection.get(include=["metadatas"])
    delete_ids = [
        doc_id
        for doc_id, meta in zip(data["ids"], data["metadatas"])
        if meta.get("source") == resume_source
    ]
    if delete_ids:
        collection.delete(ids=delete_ids)
        get_resumes_df()
        return f"✅ Deleted resume: {resume_source}"
    return f"❌ Resume not found: {resume_source}"

@tool
def shortlist_resume(user_query: str) -> str:
    """
    Shortlist the best matching resume for a given job requirement using vector search and LLM.

    Parameters
    ----------
    user_query : str
        Free-text description of required skills, role, and experience.

    Returns
    -------
    str
        A formatted description of the best-matching candidate and their details.
    """
    try:
        query_embedding = embed_model.embed_query(user_query)
        results = collection.query(query_embeddings=[query_embedding], n_results=3)

        if not results["metadatas"][0]:
            return "❌ No matching resumes found"

        sources = [m["source"] for m in results["metadatas"][0]]
        best_source = Counter(sources).most_common(1)[0][0]

        all_docs = collection.get(where={"source": best_source})
        resume_text = "\n".join(all_docs["documents"][:3])

        prompt = f"""RESUME: {best_source}
CONTENT: {resume_text[:2000]}
JOB REQUIREMENTS: {user_query}

Extract key information:
Name: 
Current Role: 
Company: 
Experience (years): 
Top Skills: 
Match Score (1-10): 
Source: {best_source}"""

        response = llm.invoke(prompt)
        return f"**🎯 BEST MATCH: {best_source}**\n{response.content}"
    except Exception as e:
        return f"❌ Search error: {str(e)}"

# ---------------- SIMPLE AGENT ROUTER ----------------
def run_agent_tool(prompt: str) -> str:
    """
    Very simple rule-based router that calls one of the tools based on keywords
    in the prompt (list, delete, shortlist).
    """
    prompt_lower = prompt.lower()

    if "list" in prompt_lower or "show" in prompt_lower:
        return list_all_resumes.invoke({})
    elif "delete" in prompt_lower or "remove" in prompt_lower:
        resume_name = prompt.split("delete")[-1].strip().split()[0] if "delete" in prompt_lower else ""
        return delete_resume.invoke({"resume_source": resume_name})
    elif "shortlist" in prompt_lower or "find" in prompt_lower or "search" in prompt_lower:
        query = prompt.replace("shortlist", "").replace("find", "").replace("search", "").strip()
        return shortlist_resume.invoke({"user_query": query})
    else:
        return "Use: 'list resumes', 'delete [name]', 'shortlist [requirements]'"

# ---------------- SIDEBAR NAVIGATION ----------------
with st.sidebar:
    st.subheader("Navigation")

    if st.button("Upload Resume", use_container_width=True):
        st.session_state.action = "upload"

    if st.button("Update Resume", use_container_width=True):
        st.session_state.action = "update"

    if st.button("List Resume", use_container_width=True):
        st.session_state.action = "list"

    if st.button("Delete Resume", use_container_width=True):
        st.session_state.action = "delete"

    if st.button("Shortlist Candidate", use_container_width=True):
        st.session_state.action = "shortlist"

    st.markdown("---")
    col1, col2 = st.columns(2)
    col1.metric("Total Chunks", collection.count())
    col2.metric("Total Resumes", len(st.session_state.resumes_df))

# ---------------- MAIN AREA (UI) ----------------
# Shortlist page: like your screenshot
if st.session_state.action == "shortlist":
    st.markdown(
        "<h1 style='text-align: center;'>Shortlist Candidate</h1>",
        unsafe_allow_html=True,
    )

    # previous chat (optional)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("Ask about resumes (type 'clear' to reset)")
    if user_query:
        if user_query.lower() == "clear":
            st.session_state.messages.clear()
            st.experimental_rerun()

        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        reply = shortlist_resume.invoke({"user_query": user_query})
        with st.chat_message("assistant"):
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

elif st.session_state.action == "upload":
    st.header("📤 Upload Resume")
    uploaded_file = st.file_uploader("Choose PDF file", type=["pdf"])
    if uploaded_file:
        col1, col2 = st.columns([3, 1])
        col1.success(f"**{uploaded_file.name}** ready")
        if col2.button("🚀 Upload & Process", type="primary"):
            with st.spinner("Processing..."):
                filepath = save_uploaded_file(uploaded_file)
                result = process_resume_file(filepath)
                st.success(result)
                get_resumes_df()
                st.rerun()

elif st.session_state.action == "list":
    st.header("📋 All Resumes")
    if st.button("🔄 Refresh List", type="primary"):
        get_resumes_df()
        st.success("✅ List refreshed!")
    st.dataframe(st.session_state.resumes_df, use_container_width=True)

elif st.session_state.action == "delete":
    st.header("🗑️ Delete Resume")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(st.session_state.resumes_df, use_container_width=True)
    with col2:
        resume_sources = st.session_state.resumes_df["Source"].tolist() if not st.session_state.resumes_df.empty else []
        selected = st.selectbox("Select to delete:", [""] + resume_sources)
        if st.button("🗑️ Delete", type="primary") and selected:
            with st.spinner("Deleting..."):
                result = delete_resume.invoke({"resume_source": selected})
                st.markdown(f"**{result}**")
                get_resumes_df()
                st.rerun()

elif st.session_state.action == "update":
    st.header("🔄 Update Resume")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(st.session_state.resumes_df, use_container_width=True)
    with col2:
        resume_sources = st.session_state.resumes_df["Source"].tolist() if not st.session_state.resumes_df.empty else []
        old_name = st.selectbox("Select existing resume:", [""] + resume_sources)
        new_file = st.file_uploader("Upload updated PDF", type=["pdf"])
        if st.button("🔄 Update", type="primary") and old_name and new_file:
            with st.spinner("Updating..."):
                _ = delete_resume.invoke({"resume_source": old_name})
                filepath = save_uploaded_file(new_file)
                result = process_resume_file(filepath)
                st.success(result)
                get_resumes_df()
                st.rerun()
