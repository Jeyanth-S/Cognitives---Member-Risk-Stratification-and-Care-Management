import os
import re
import pandas as pd
from sentence_transformers import SentenceTransformer
import config
import generator
from pinecone import Pinecone

# Load embedding model for queries
embedder = SentenceTransformer(config.EMBEDDING_MODEL)

# Init Pinecone
pc = Pinecone(api_key=config.PINECONE_API_KEY)
index = pc.Index(config.PINECONE_INDEX_NAME)

# Map CSV flags to human disease names
DISEASE_MAP = {
    "SP_ALZHDMTA": "Alzheimer's disease",
    "SP_CHF": "Congestive heart failure",
    "SP_CHRNKIDN": "Chronic kidney disease",
    "SP_CNCR": "Cancer",
    "SP_COPD": "Chronic obstructive pulmonary disease",
    "SP_DEPRESSN": "Depression",
    "SP_DIABETES": "Diabetes",
    "SP_ISCHMCHT": "Ischemic heart disease",
    "SP_OSTEOPRS": "Osteoporosis",
    "SP_RA_OA": "Rheumatoid arthritis or Osteoarthritis",
    "SP_STRKETIA": "Stroke/TIA"
}

# simple sentence splitter - keeps punctuation
_SENT_SPLIT_RE = re.compile(r'(?<=[\.\?\!])\s+')

def clean_text_for_sentences(text: str) -> str:
    """Remove control chars, normalize bullets and whitespace (keeps printable sentences)."""
    if not text:
        return ""
    # replace common bullet-like characters with hyphen
    text = re.sub(r'[•\u2022\u2023\u25E6\u2023\u2024\u2027\u00B7\uF0B7\u2022]', '-', text)
    # remove control chars
    text = re.sub(r'[\x00-\x1F\x7F]', ' ', text)
    # collapse multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_into_sentences(text: str):
    text = clean_text_for_sentences(text)
    if not text:
        return []
    # split by punctuation + whitespace; keep short segments as separate "sentences"
    sentences = _SENT_SPLIT_RE.split(text)
    # strip each sentence
    return [s.strip() for s in sentences if s.strip()]

def load_patient_data(path=config.PATIENT_CSV_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Patient CSV not found at {path}")
    df = pd.read_csv(path, dtype=str)
    for col in DISEASE_MAP:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df

def get_patient_diseases(row):
    diseases = []
    for flag_col, name in DISEASE_MAP.items():
        if flag_col in row and int(row[flag_col]) == 1:
            diseases.append(name)
    return diseases

def _get_matches_from_response(resp):
    if hasattr(resp, "matches"):
        return resp.matches
    if isinstance(resp, dict):
        return resp.get("matches", [])
    return []

def _get_text_from_match(m):
    # works whether m is an object or dict
    md = getattr(m, "metadata", None) or (m.get("metadata") if isinstance(m, dict) else {})
    txt = ""
    if isinstance(md, dict):
        txt = md.get("text") or md.get("content") or ""
    else:
        txt = ""
    # fallback if match directly contains 'metadata' differently
    if not txt and isinstance(m, dict):
        txt = m.get("text") or m.get("content") or ""
    return txt or ""

def retrieve_chunks_for_disease(disease, top_k=config.TOP_K, max_sentences=6):
    """
    Retrieve relevant sentences/chunks for a disease.
    Filtering approach:
      1) Query Pinecone for top_k matches.
      2) For each matched chunk, split into sentences.
      3) Keep sentences that mention the disease or important keywords (treat/diagnos/prevent/etc.).
      4) Stop when we have up to max_sentences unique sentences.
    """
    query_text = disease
    q_emb = embedder.encode(query_text).tolist()
    try:
        resp = index.query(vector=q_emb, top_k=top_k * 3, include_metadata=True)  # retrieve a few more and filter
    except Exception as e:
        print("❌ Pinecone query error:", e)
        return []

    matches = _get_matches_from_response(resp)

    # keywords to pick up treatment/diagnosis/prevention sentences
    keywords = [
        disease.lower(), "treat", "treatment", "manage", "management", "diagnos", "symptom",
        "prevent", "screen", "therapy", "surgery", "medic", "vaccine", "recommend"
    ]

    results = []
    seen = set()
    for m in matches:
        txt = _get_text_from_match(m)
        if not txt:
            continue
        sentences = split_into_sentences(txt)
        # prefer sentences that contain the disease name or a keyword
        for s in sentences:
            low = s.lower()
            if any(k in low for k in keywords):
                # dedupe by exact sentence text
                if low not in seen:
                    seen.add(low)
                    results.append(s)
                    if len(results) >= max_sentences:
                        return results
    # If we still have nothing, fallback to returning full chunks (shortened)
    if not results:
        for m in matches[:top_k]:
            txt = _get_text_from_match(m)
            if txt:
                candidate = clean_text_for_sentences(txt)
                low = candidate.lower()
                if low not in seen:
                    seen.add(low)
                    results.append(candidate)
                    if len(results) >= max_sentences:
                        break

    # final dedupe keep order
    return results[:max_sentences]


def get_patient_info(desynpuf_id):
    df = load_patient_data()
    row_df = df[df["DESYNPUF_ID"].astype(str) == str(desynpuf_id)]
    if row_df.empty:
        return {"error": f"No patient with DESYNPUF_ID={desynpuf_id}"}

    row = row_df.iloc[0].to_dict()
    diseases = get_patient_diseases(row)

    if not diseases:
        return {"DESYNPUF_ID": desynpuf_id, "diseases": [], "suggestions": []}

    suggestions = []
    for disease in diseases:
        chunks = retrieve_chunks_for_disease(disease, top_k=config.TOP_K)
        # generator.summarize_context expects a list of texts (short sentences/chunks)
        suggestion = generator.summarize_context(disease, chunks)
        suggestions.append(suggestion)

    return {
        "DESYNPUF_ID": desynpuf_id,
        "diseases": diseases,
        "suggestions": suggestions
    }
