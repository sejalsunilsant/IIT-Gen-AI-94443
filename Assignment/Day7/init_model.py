import os
import uuid
import datetime
import streamlit as st
import chromadb
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings import init_embeddings
from langchain.chat_models import init_chat_model

# ================= ENV =================
load_dotenv()

# ================= STREAMLIT CONFIG =================
st.set_page_config(
    page_title="AI Resume Shortlister",
    page_icon="🤖",
    layout="wide"
)

st.title("AI Enabled Resume Shortlisting for HR Teams")

# ================= SESSION STATE =================
if "db_initialized" not in st.session_state:
    st.session_state.db_initialized = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "collection" not in st.session_state:
    st.session_state.collection = None

if "resume_index" not in st.session_state:
    # maps: resume_id -> {file_name, upload_time}
    st.session_state.resume_index = {}

# ================= CONSTANTS =================
PERSIST_DIR = "./Resume_base"        # same directory you used
COLLECTION_NAME = "Resume_collection"


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

# ================= CHROMA CLIENT / COLLECTION =================
def get_chroma_collection():
    chroma_client = chromadb.PersistentClient(path=PERSIST_DIR)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    return collection


def init_vector_db_once():
    if not st.session_state.db_initialized:
        st.session_state.collection = get_chroma_collection()
        st.session_state.db_initialized = True


init_vector_db_once()

# ================= HELPER FUNCTIONS =================
def index_single_pdf(file_bytes, file_name: str, resume_id: str | None = None):
    """
    Load a single PDF from bytes, split, embed, and add to Chroma.
    Stores metadata: resume_id, file_name, upload_time.
    """
    if resume_id is None:
        resume_id = str(uuid.uuid4())

    temp_path = f"./_tmp_{resume_id}.pdf"
    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    loader = PyPDFLoader(temp_path)
    documents = loader.load()

    chunks = text_splitter.split_documents(documents)
    texts = [c.page_content for c in chunks]
    embeddings = embed_model.embed_documents(texts)

    ids = [f"{resume_id}_chunk_{i}" for i in range(len(texts))]
    metadatas = []
    upload_time = datetime.datetime.now().isoformat()

    for i, chunk in enumerate(chunks):
        meta = chunk.metadata.copy()
        meta["resume_id"] = resume_id
        meta["file_name"] = file_name
        meta["chunk_id"] = i
        meta["upload_time"] = upload_time
        metadatas.append(meta)

    st.session_state.collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    # maintain a simple index for listing resumes
    st.session_state.resume_index[resume_id] = {
        "file_name": file_name,
        "upload_time": upload_time
    }

    os.remove(temp_path)
    return resume_id


def delete_resume_from_chroma(resume_id: str):
    """
    Delete all chunks belonging to a resume_id from Chroma and local index.
    """
    collection = st.session_state.collection
    # Filter by metadata resume_id to get all ids
    results = collection.get(
        where={"resume_id": resume_id}
    )

    if len(results.get("ids", [])) > 0:
        collection.delete(ids=results["ids"])

    if resume_id in st.session_state.resume_index:
        del st.session_state.resume_index[resume_id]


def shortlist_resumes(job_description: str, top_k: int = 3):
    """
    Use job description embedding to perform similarity search over Chroma.
    Return top_k grouped by resume_id with simple ranking.
    """
    query_emb = embed_model.embed_query(job_description)
    results = st.session_state.collection.query(
        query_embeddings=[query_emb],
        n_results=20  # fetch more chunks, then aggregate per resume
    )

    # Aggregate scores per resume_id
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0] if "distances" in results else None

    resume_scores = {}
    resume_chunks = {}

    for idx, meta in enumerate(metas):
        resume_id = meta.get("resume_id")
        if resume_id is None:
            continue

        score = dists[idx] if dists is not None else 0.0
        resume_scores.setdefault(resume_id, 0.0)
        # lower distance means more similar; convert to simple relevance
        resume_scores[resume_id] += (1.0 / (1.0 + score))

        resume_chunks.setdefault(resume_id, [])
        resume_chunks[resume_id].append(docs[idx][:500])

    # sort by score desc
    sorted_resumes = sorted(
        resume_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_k]

    shortlisted = []
    for resume_id, score in sorted_resumes:
        info = st.session_state.resume_index.get(resume_id, {})
        shortlisted.append({
            "resume_id": resume_id,
            "file_name": info.get("file_name", "Unknown"),
            "upload_time": info.get("upload_time", "Unknown"),
            "score": score,
            "sample_context": "\n\n".join(resume_chunks.get(resume_id, [])[:2])
        })

    return shortlisted


def explain_shortlist_with_llm(job_description: str, resume_context: str, file_name: str):
    """
    Use LLM to justify why a resume was shortlisted for the JD.
    """
    prompt = f"""
You are an AI assistant helping an HR team to shortlist resumes.

TASK:
Explain briefly why this candidate's resume is relevant for the given Job Description.

RULES:
1. Use only the RESUME CONTEXT provided.
2. Do not invent skills or experience.
3. Give a short, bullet-style explanation (3-5 points).
4. Focus on matching skills, experience, and domain.

JOB DESCRIPTION:
{job_description}

RESUME CONTEXT (from {file_name}):
{resume_context}

Now respond with a concise explanation for HR.
"""
    resp = llm.invoke(prompt)
    return resp.content


# ================= SIDEBAR NAVIGATION =================
st.sidebar.header("HR Actions")
page = st.sidebar.radio(
    "Choose action",
    ["Upload / Update Resume", "List & Delete Resumes", "Shortlist by Job Description"]
)

# ================= PAGE: UPLOAD / UPDATE =================
if page == "Upload / Update Resume":
    st.subheader("Upload New Resume (PDF) or Update Existing")

    uploaded_files = st.file_uploader(
        "Upload one or more PDF resumes",
        type=["pdf"],
        accept_multiple_files=True
    )

    st.markdown("If you want to update an existing resume, choose its ID from the list below.")
    existing_ids = list(st.session_state.resume_index.keys())
    selected_resume_id = st.selectbox(
        "Select existing Resume ID to update (optional)",
        options=["-- New Resume --"] + existing_ids
    )

    if st.button("Process Uploaded Resumes") and uploaded_files:
        for f in uploaded_files:
            file_bytes = f.read()
            file_name = f.name

            if selected_resume_id != "-- New Resume --":
                # Update flow: delete old and reindex
                delete_resume_from_chroma(selected_resume_id)
                index_single_pdf(file_bytes, file_name, resume_id=selected_resume_id)
                st.success(f"Updated resume for ID: {selected_resume_id} with file: {file_name}")
            else:
                # New resume
                new_id = index_single_pdf(file_bytes, file_name)
                st.success(f"Uploaded new resume: {file_name} with ID: {new_id}")

# ================= PAGE: LIST & DELETE =================
elif page == "List & Delete Resumes":
    st.subheader("All Stored Resumes")

    if not st.session_state.resume_index:
        st.info("No resumes found. Please upload some PDFs first.")
    else:
        # Show as table
        rows = []
        for rid, info in st.session_state.resume_index.items():
            rows.append((rid, info["file_name"], info["upload_time"]))
        st.table(rows)

        delete_id = st.text_input("Enter Resume ID to delete")
        if st.button("Delete Resume"):
            if delete_id in st.session_state.resume_index:
                delete_resume_from_chroma(delete_id)
                st.success(f"Deleted resume with ID: {delete_id}")
            else:
                st.error("Invalid Resume ID.")

# ================= PAGE: SHORTLIST BY JD =================
elif page == "Shortlist by Job Description":
    st.subheader("Shortlist Resumes for a Job Description")

    jd_text = st.text_area("Paste Job Description here")
    top_k = st.number_input(
        "Number of resumes to shortlist",
        min_value=1,
        max_value=10,
        value=3,
        step=1
    )

    if st.button("Shortlist Resumes"):
        if not jd_text.strip():
            st.warning("Please enter a Job Description.")
        else:
            shortlisted = shortlist_resumes(jd_text, top_k=int(top_k))
            if not shortlisted:
                st.warning("No resumes found to shortlist. Upload resumes first.")
            else:
                for item in shortlisted:
                    st.markdown("---")
                    st.markdown(f"**Resume ID:** `{item['resume_id']}`")
                    st.markdown(f"File: {item['file_name']}")
                    st.markdown(f"Uploaded: {item['upload_time']}")
                    st.markdown(f"Relevance Score: `{item['score']:.4f}`")

                    with st.expander("View sampled matching context"):
                        st.write(item["sample_context"])

                    if st.button(f"Explain why shortlist: {item['resume_id']}", key=item["resume_id"]):
                        explanation = explain_shortlist_with_llm(
                            jd_text,
                            item["sample_context"],
                            item["file_name"]
                        )
                        st.markdown("**AI Justification for Shortlisting:**")
                        st.write(explanation)

# ================= OPTIONAL: SIMPLE CHAT VIEW (LOG) =================
st.sidebar.subheader("System Log")
st.sidebar.write(f"Total resumes indexed: {len(st.session_state.resume_index)}")
