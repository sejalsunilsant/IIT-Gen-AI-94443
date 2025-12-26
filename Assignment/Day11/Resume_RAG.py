import os
import streamlit as st
import chromadb
from dotenv import load_dotenv
from collections import Counter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings import init_embeddings
from langchain.chat_models import init_chat_model
import pandas as pd
load_dotenv()

# ---------------- UI ----------------
st.set_page_config(
    page_title="Resume Refiner",
    page_icon="🤖",
    layout="centered"
)

# ---------------- GLOBAL VARIABLES  ----------------
messages = []
context_docs = []
if "action" not in st.session_state:
    st.session_state.action = "shortlist"


# ---------------- LLM ----------------
llm = init_chat_model(
    model="phi-3.1-mini-4k-instruct",
    model_provider="openai",
    base_url="http://127.0.0.1:1234/v1",
    api_key="not-needed"
)

# ---------------- EMBEDDINGS ----------------
embed_model = init_embeddings(
    model="text-embedding-nomic-embed-text-v1.5-embedding",
    provider="openai",
    base_url="http://127.0.0.1:1234/v1",
    api_key="not-needed",
    check_embedding_ctx_length=False
)

# ---------------- TEXT SPLITTER ----------------
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=60
)

# ---------------- PDF LOADER ----------------
dir_loader = DirectoryLoader(
    path=r"D:\Sunbeam\IIT-Gen-AI-94443\Assignment\Day11\fake resume",
    glob="*.pdf",
    loader_cls=PyPDFLoader
)

def load_pdf_resumes():
    return dir_loader.load()

# ---------------- VECTOR DB ----------------
PERSIST_DIR = "./Resume_base"
COLLECTION_NAME = "Resume_collection"

chroma_client = chromadb.PersistentClient(path=PERSIST_DIR)
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

# ---------------- INITIAL LOAD ----------------
if collection.count() == 0:
    documents = load_pdf_resumes()
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

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

# ---------------- STORE UPLOADED RESUME ----------------
def Store_Collection(uploaded_resume):
    upload_dir = "./fake resume"
    os.makedirs(upload_dir, exist_ok=True)

    temp_path = os.path.join(upload_dir, uploaded_resume.name)

    with open(temp_path, "wb") as f:
        f.write(uploaded_resume.getbuffer())

    loader = PyPDFLoader(temp_path)
    docs = loader.load()

    chunks = text_splitter.split_documents(docs)
    texts = [c.page_content for c in chunks]
    embeddings = embed_model.embed_documents(texts)
    
    ids = [f"{uploaded_resume.name}_{i}" for i in range(len(texts))]
    metadatas = []

    for i, chunk in enumerate(chunks):
        meta = chunk.metadata
        meta["source"] = uploaded_resume.name
        meta["chunk_id"] = i
        metadatas.append(meta)

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )
def list_all_resumes():
    data = collection.get(include=["documents","metadatas"])
    rows = []
    seen = set()
    for doc, meta, doc_id in zip(data["documents"],data["metadatas"],data["ids"]):

        source = meta.get("source", "Unknown")

        # avoid duplicate rows for same resume
        if source not in seen:
            seen.add(source)
            raw_text = doc.strip()
            lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
            first_line = lines[0] if lines else "Unknown Candidate"
            candidate_name = " ".join(first_line.split()[:2])

            rows.append({
                "Candidate Name": candidate_name,
                "Resume Source": source,
                "Resume ID": doc_id
            })

    df = pd.DataFrame(rows)
    return df

#-----------delete resume
def delete_resume(source_name):
    data = collection.get(include=["metadatas"])
    delete_ids = [
        doc_id
        for doc_id, meta in zip(data["ids"], data["metadatas"])
        if meta.get("source") == source_name
    ]
    collection.delete(ids=delete_ids)

def update_resume():
    df = list_all_resumes()
    if df.empty:
        st.info("No resumes available to update")
        return
    st.dataframe(df)
    selected_id = st.selectbox(
        "Select Resume to Update",
        df["Resume ID"].tolist()
    )
    selected_source = df.loc[
        df["Resume ID"] == selected_id, "Resume Source"
    ].values[0]
    uploaded_file = st.file_uploader(
        "Upload Updated Resume (PDF)",
        type=["pdf"]
    )
    if st.button("🔄 Update Resume"):
        if uploaded_file is None:
            st.warning("Please upload a PDF before updating")
            return
        delete_resume(selected_source)
        Store_Collection(uploaded_file)
        st.success("Resume updated successfully ✅")
        st.stop()

# ---------------- CHAT DISPLAY ----------------
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------- USER QUERY ----------------
if st.session_state.action == "upload":
    st.header("📤 Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_file:
        Store_Collection(uploaded_file)
        st.success("Resume uploaded successfully")

elif st.session_state.action == "update":
    st.header("🔄 Update Resume")
    update_resume()

elif st.session_state.action == "list":
    st.header("📋 Resume List")
    df=list_all_resumes()
    st.dataframe(df, use_container_width=True)


elif st.session_state.action == "delete":
    st.header("Delete Resume")
    df = list_all_resumes()
    if df.empty:
        st.info("No resumes available to delete")
    else:
        st.dataframe(df)  # Show table
        options = df["Resume ID"].tolist()
        selected_id = st.selectbox("Select Resume ID to Delete", options)
        selected_source = df.loc[df["Resume ID"] == selected_id, "Resume Source"].values[0]
        
        if st.button("Confirm Delete"):
            delete_resume(selected_source)
            st.success("Resume deleted successfully")
            st.stop()



elif st.session_state.action == "shortlist":
    st.header("Shortlist Candidate")
    user_query = st.chat_input("Ask about resumes (type 'clear' to reset)")

    if user_query:
        if user_query.lower() == "clear":
            messages.clear()
            context_docs.clear()
            st.experimental_rerun()

        messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        query_embedding = embed_model.embed_query(user_query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=5
        )

        sources = [m["source"] for m in results["metadatas"][0]]
        best_source = Counter(sources).most_common(1)[0][0]

        all_docs = collection.get(where={"source": best_source})
        full_resume_text = "\n\n".join(all_docs["documents"])

        context = f"""
    Resume Source: {best_source}
    Full Resume Content:
    {full_resume_text}
    """

        prompt = f"""
    You are a resume identification assistant.

    RULES:
    1. Use ONLY the resume information provided in the CONTEXT.
    2. Select ONLY one relevant resume.
    3. Do NOT invent information.
    4. If no match exists, respond exactly:
    "No matching resume found."

    RESUME DATA:
    {context}

    USER QUERY:
    {user_query}

    OUTPUT:
    Name:
    Current Role:
    Company:
    Contact:
    Total Experience:
    Primary Skills:
    Key Responsibilities:
    Resume Source:
    reasone of selection : <answer based on your own intelligence
    """

        with st.chat_message("assistant"):
            response = llm.invoke(prompt)
            st.markdown(response.content)

        messages.append({"role": "assistant", "content": response.content})



# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.subheader("Navigation")

    if st.button("Upload Resume",width="stretch"):
        st.session_state.action = "upload"

    if st.button("Update Resume",width="stretch"):
        st.session_state.action = "update"

    if st.button("List Resume",width="stretch"):
        st.session_state.action = "list"

    if st.button("Delete Resume",width="stretch"):
        st.session_state.action = "delete"

    if st.button("Shortlist Candidate",width="stretch"):
        st.session_state.action = "shortlist"
