# import pandas as pd
# from sentence_transformers import SentenceTransformer
# import config
# import generator
# import os
# from pinecone import Pinecone


# # Load embedding model for queries
# embedder = SentenceTransformer(config.EMBEDDING_MODEL)

# # Init Pinecone
# pc = Pinecone(api_key=config.PINECONE_API_KEY)
# index = pc.Index(config.PINECONE_INDEX_NAME)

# # Map CSV flags to human disease names
# DISEASE_MAP = {
#     "SP_ALZHDMTA": "Alzheimer's disease",
#     "SP_CHF": "Congestive heart failure",
#     "SP_CHRNKIDN": "Chronic kidney disease",
#     "SP_CNCR": "Cancer",
#     "SP_COPD": "Chronic obstructive pulmonary disease",
#     "SP_DEPRESSN": "Depression",
#     "SP_DIABETES": "Diabetes",
#     "SP_ISCHMCHT": "Ischemic heart disease",
#     "SP_OSTEOPRS": "Osteoporosis",
#     "SP_RA_OA": "Rheumatoid arthritis or Osteoarthritis",
#     "SP_STRKETIA": "Stroke/TIA"
# }

# def load_patient_data(path=config.PATIENT_CSV_PATH):
#     if not os.path.exists(path):
#         raise FileNotFoundError(f"Patient CSV not found at {path}")
#     df = pd.read_csv(path, dtype=str)  # keep safe with strings
#     for col in DISEASE_MAP:
#         if col in df.columns:
#             df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
#     return df

# def get_patient_diseases(row):
#     diseases = []
#     for flag_col, name in DISEASE_MAP.items():
#         if flag_col in row and int(row[flag_col]) == 1:
#             diseases.append(name)
#     return diseases

# # def retrieve_chunks_for_disease(disease, top_k=config.TOP_K):
# #     """Retrieve relevant chunks from Pinecone for a disease."""
# #     query_text = disease
# #     q_emb = embedder.encode(query_text).tolist()
# #     try:
# #         resp = index.query(vector=q_emb, top_k=top_k, include_metadata=True)
# #     except Exception as e:
# #         print("❌ Pinecone query error:", e)
# #         return []

# #     matches = []
# #     if hasattr(resp, "matches"):
# #         matches = resp.matches
# #     elif isinstance(resp, dict) and "matches" in resp:
# #         matches = resp["matches"]

# #     texts = []
# #     for m in matches:
# #         md = getattr(m, "metadata", None) or (m.get("metadata") if isinstance(m, dict) else {})
# #         txt = md.get("text") or md.get("content") or ""
# #         if txt:
# #             texts.append(txt.strip())
# #     return texts


# def retrieve_chunks_for_disease(disease, top_k=config.TOP_K):
#     """Retrieve relevant chunks from Pinecone for a disease, filter to avoid cross-disease contamination."""
#     query_text = disease
#     q_emb = embedder.encode(query_text).tolist()
#     try:
#         resp = index.query(vector=q_emb, top_k=top_k, include_metadata=True)
#     except Exception as e:
#         print("❌ Pinecone query error:", e)
#         return []

#     matches = []
#     if hasattr(resp, "matches"):
#         matches = resp.matches
#     elif isinstance(resp, dict) and "matches" in resp:
#         matches = resp["matches"]

#     texts = []
#     for m in matches:
#         md = getattr(m, "metadata", None) or (m.get("metadata") if isinstance(m, dict) else {})
#         txt = md.get("text") or md.get("content") or ""

#         # 🔹 Filter: keep only chunks that explicitly mention the disease
#         if txt and disease.lower() in txt.lower():
#             texts.append(txt.strip())

#     return texts


# def get_patient_info(desynpuf_id):
#     df = load_patient_data()
#     row_df = df[df["DESYNPUF_ID"].astype(str) == str(desynpuf_id)]
#     if row_df.empty:
#         return {"error": f"No patient with DESYNPUF_ID={desynpuf_id}"}

#     row = row_df.iloc[0].to_dict()
#     diseases = get_patient_diseases(row)

#     if not diseases:
#         return {"DESYNPUF_ID": desynpuf_id, "diseases": [], "suggestions": []}

#     suggestions = []
#     # for disease in diseases:
#     #     chunks = retrieve_chunks_for_disease(disease, top_k=config.TOP_K)
#     #     chunks = list(dict.fromkeys(chunks))
#     #     suggestion_text = generator.summarize_context(disease, chunks)
#     #     suggestions.append({
#     #         "disease": disease,
#     #         "source_chunks": chunks,
#     #         "suggestion": suggestion_text
#     #     })

#     for disease in diseases:
#         chunks = retrieve_chunks_for_disease(disease, top_k=config.TOP_K)
#         chunks = list(dict.fromkeys(chunks))
#         suggestion = generator.summarize_context(disease, chunks)
#         suggestions.append(suggestion)   # ✅ directly append




#     return {
#         "DESYNPUF_ID": desynpuf_id,
#         "diseases": diseases,
#         "suggestions": suggestions
#     }





# import os
# import re
# import pandas as pd
# from sentence_transformers import SentenceTransformer
# import config
# import generator
# from pinecone import Pinecone

# # Load embedding model for queries
# embedder = SentenceTransformer(config.EMBEDDING_MODEL)

# # Init Pinecone
# pc = Pinecone(api_key=config.PINECONE_API_KEY)
# index = pc.Index(config.PINECONE_INDEX_NAME)

# # Map CSV flags to human disease names
# DISEASE_MAP = {
#     "SP_ALZHDMTA": "Alzheimer's disease",
#     "SP_CHF": "Congestive heart failure",
#     "SP_CHRNKIDN": "Chronic kidney disease",
#     "SP_CNCR": "Cancer",
#     "SP_COPD": "Chronic obstructive pulmonary disease",
#     "SP_DEPRESSN": "Depression",
#     "SP_DIABETES": "Diabetes",
#     "SP_ISCHMCHT": "Ischemic heart disease",
#     "SP_OSTEOPRS": "Osteoporosis",
#     "SP_RA_OA": "Rheumatoid arthritis or Osteoarthritis",
#     "SP_STRKETIA": "Stroke/TIA"
# }

# # simple sentence splitter - keeps punctuation
# _SENT_SPLIT_RE = re.compile(r'(?<=[\.\?\!])\s+')

# def clean_text_for_sentences(text: str) -> str:
#     """Remove control chars, normalize bullets and whitespace (keeps printable sentences)."""
#     if not text:
#         return ""
#     # replace common bullet-like characters with hyphen
#     text = re.sub(r'[•\u2022\u2023\u25E6\u2023\u2024\u2027\u00B7\uF0B7\u2022]', '-', text)
#     # remove control chars
#     text = re.sub(r'[\x00-\x1F\x7F]', ' ', text)
#     # collapse multiple spaces/newlines
#     text = re.sub(r'\s+', ' ', text).strip()
#     return text

# def split_into_sentences(text: str):
#     text = clean_text_for_sentences(text)
#     if not text:
#         return []
#     # split by punctuation + whitespace; keep short segments as separate "sentences"
#     sentences = _SENT_SPLIT_RE.split(text)
#     # strip each sentence
#     return [s.strip() for s in sentences if s.strip()]

# def load_patient_data(path=config.PATIENT_CSV_PATH):
#     if not os.path.exists(path):
#         raise FileNotFoundError(f"Patient CSV not found at {path}")
#     df = pd.read_csv(path, dtype=str)
#     for col in DISEASE_MAP:
#         if col in df.columns:
#             df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
#     return df

# def get_patient_diseases(row):
#     diseases = []
#     for flag_col, name in DISEASE_MAP.items():
#         if flag_col in row and int(row[flag_col]) == 1:
#             diseases.append(name)
#     return diseases

# def _get_matches_from_response(resp):
#     if hasattr(resp, "matches"):
#         return resp.matches
#     if isinstance(resp, dict):
#         return resp.get("matches", [])
#     return []

# def _get_text_from_match(m):
#     # works whether m is an object or dict
#     md = getattr(m, "metadata", None) or (m.get("metadata") if isinstance(m, dict) else {})
#     txt = ""
#     if isinstance(md, dict):
#         txt = md.get("text") or md.get("content") or ""
#     else:
#         txt = ""
#     # fallback if match directly contains 'metadata' differently
#     if not txt and isinstance(m, dict):
#         txt = m.get("text") or m.get("content") or ""
#     return txt or ""

# def retrieve_chunks_for_disease(disease, top_k=config.TOP_K, max_sentences=6):
#     """
#     Retrieve relevant sentences/chunks for a disease.
#     Filtering approach:
#       1) Query Pinecone for top_k matches.
#       2) For each matched chunk, split into sentences.
#       3) Keep sentences that mention the disease or important keywords (treat/diagnos/prevent/etc.).
#       4) Stop when we have up to max_sentences unique sentences.
#     """
#     query_text = disease
#     q_emb = embedder.encode(query_text).tolist()
#     try:
#         resp = index.query(vector=q_emb, top_k=top_k * 3, include_metadata=True)  # retrieve a few more and filter
#     except Exception as e:
#         print("❌ Pinecone query error:", e)
#         return []

#     matches = _get_matches_from_response(resp)

#     # keywords to pick up treatment/diagnosis/prevention sentences
#     keywords = [
#         disease.lower(), "treat", "treatment", "manage", "management", "diagnos", "symptom",
#         "prevent", "screen", "therapy", "surgery", "medic", "vaccine", "recommend"
#     ]

#     results = []
#     seen = set()
#     for m in matches:
#         txt = _get_text_from_match(m)
#         if not txt:
#             continue
#         sentences = split_into_sentences(txt)
#         # prefer sentences that contain the disease name or a keyword
#         for s in sentences:
#             low = s.lower()
#             if any(k in low for k in keywords):
#                 # dedupe by exact sentence text
#                 if low not in seen:
#                     seen.add(low)
#                     results.append(s)
#                     if len(results) >= max_sentences:
#                         return results
#     # If we still have nothing, fallback to returning full chunks (shortened)
#     if not results:
#         for m in matches[:top_k]:
#             txt = _get_text_from_match(m)
#             if txt:
#                 candidate = clean_text_for_sentences(txt)
#                 low = candidate.lower()
#                 if low not in seen:
#                     seen.add(low)
#                     results.append(candidate)
#                     if len(results) >= max_sentences:
#                         break

#     # final dedupe keep order
#     return results[:max_sentences]


# def get_patient_info(desynpuf_id):
#     df = load_patient_data()
#     row_df = df[df["DESYNPUF_ID"].astype(str) == str(desynpuf_id)]
#     if row_df.empty:
#         return {"error": f"No patient with DESYNPUF_ID={desynpuf_id}"}

#     row = row_df.iloc[0].to_dict()
#     diseases = get_patient_diseases(row)

#     if not diseases:
#         return {"DESYNPUF_ID": desynpuf_id, "diseases": [], "suggestions": []}

#     suggestions = []
#     for disease in diseases:
#         chunks = retrieve_chunks_for_disease(disease, top_k=config.TOP_K)
#         # generator.summarize_context expects a list of texts (short sentences/chunks)
#         suggestion = generator.summarize_context(disease, chunks)
#         suggestions.append(suggestion)

#     return {
#         "DESYNPUF_ID": desynpuf_id,
#         "diseases": diseases,
#         "suggestions": suggestions
#     }




import os
import re
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import config
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

_SENT_SPLIT_RE = re.compile(r'(?<=[\.\?\!])\s+')
ETHNICITY_KEYWORDS = {"african", "asian", "hispanic", "latino", "white", "black", "american indian", "native", "pacific islander"}

def clean_text_for_sentences(text: str) -> str:
    if not text:
        return ""
    # replace bullet chars with dash, remove control chars, collapse whitespace
    text = re.sub(r'[•\u2022\u2023\u25E6\u2023\u2024\u2027\u00B7]', '-', text)
    text = re.sub(r'[\x00-\x1F\x7F]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_into_sentences(text: str):
    text = clean_text_for_sentences(text)
    if not text:
        return []
    sentences = _SENT_SPLIT_RE.split(text)
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
    md = getattr(m, "metadata", None) or (m.get("metadata") if isinstance(m, dict) else {})
    txt = ""
    if isinstance(md, dict):
        txt = md.get("text") or md.get("content") or ""
    if not txt and isinstance(m, dict):
        txt = m.get("text") or m.get("content") or ""
    return txt or ""

def _is_demographic_only(sentence: str) -> bool:
    s = sentence.lower()
    # if sentence mostly short and mentions ethnicity keywords, treat as demographic-only
    if len(s) < 80 and any(k in s for k in ETHNICITY_KEYWORDS):
        # e.g. "You are African American."
        return True
    return False

def _is_question_or_fragment(sentence: str) -> bool:
    s = sentence.strip()
    if s.endswith('?'):
        return True
    # too short fragment
    if len(s) < 30:
        return True
    # sentences that are only headings: start with "What are" / "Who is" etc.
    if re.match(r'^(what|who|how|when)\b', s.lower()):
        return True
    return False

def _rank_sentences_by_query(sentences, query, top_n=3, min_similarity=0.20):
    if not sentences:
        return []
    # compute embeddings
    s_emb = embedder.encode(sentences, convert_to_numpy=True, normalize_embeddings=True)
    q_emb = embedder.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    sims = (s_emb @ q_emb).flatten()  # cosine because normalized
    # get indices sorted high->low
    idxs = np.argsort(sims)[::-1]
    selected = []
    for i in idxs:
        if sims[i] < min_similarity:
            break
        cand = sentences[int(i)]
        if _is_question_or_fragment(cand) or _is_demographic_only(cand):
            continue
        if cand not in selected:
            selected.append(cand)
        if len(selected) >= top_n:
            break
    return selected

def retrieve_chunks_for_disease(disease, top_k=config.TOP_K, per_section=2):
    """
    Semantic sentence-level retrieval:
      - query Pinecone for candidate chunks
      - split into sentences and rank sentences against three short queries:
        'symptoms of {disease}', 'treatment for {disease}', 'prevention of {disease}'
      - return best sentences (extractive) and a neat suggestion string
    """
    query_text = disease
    q_emb = embedder.encode(query_text).tolist()
    try:
        resp = index.query(vector=q_emb, top_k=max(10, top_k*3), include_metadata=True)
    except Exception as e:
        print("❌ Pinecone query error:", e)
        return [], ""  # empty sources, empty suggestion

    matches = _get_matches_from_response(resp)
    candidate_sentences = []
    seen = set()
    for m in matches:
        txt = _get_text_from_match(m)
        if not txt:
            continue
        sents = split_into_sentences(txt)
        for s in sents:
            low = s.lower()
            if low in seen:
                continue
            seen.add(low)
            candidate_sentences.append(s)

    # if nothing, fallback to returning full chunk texts
    if not candidate_sentences:
        fallback_texts = []
        for m in matches[:top_k]:
            txt = _get_text_from_match(m)
            if txt:
                fallback_texts.append(clean_text_for_sentences(txt)[:1000])
        suggestion_text = "\n".join(f"- " + t for t in fallback_texts) if fallback_texts else ""
        return fallback_texts, suggestion_text

    # build three queries for ranking
    diagnosis_queries = [f"symptoms of {disease}", f"diagnosis of {disease}"]
    treatment_queries = [f"treatment for {disease}", f"management of {disease}"]
    prevention_queries = [f"prevention of {disease}", f"screening for {disease}"]

    # rank sentences for each section and pick top items
    diag_candidates = []
    for q in diagnosis_queries:
        diag_candidates.extend(_rank_sentences_by_query(candidate_sentences, q, top_n=per_section))
    treatment_candidates = []
    for q in treatment_queries:
        treatment_candidates.extend(_rank_sentences_by_query(candidate_sentences, q, top_n=per_section))
    prevention_candidates = []
    for q in prevention_queries:
        prevention_candidates.extend(_rank_sentences_by_query(candidate_sentences, q, top_n=per_section))

    # dedupe while preserving order and limit
    def dedupe_keep_order(lst, limit):
        out = []
        seen2 = set()
        for x in lst:
            if x not in seen2:
                seen2.add(x)
                out.append(x)
            if len(out) >= limit:
                break
        return out

    diag_final = dedupe_keep_order(diag_candidates, per_section)
    treat_final = dedupe_keep_order(treatment_candidates, per_section)
    prev_final = dedupe_keep_order(prevention_candidates, per_section)

    # If a section is empty, try to pick general sentences (best overall)
    if not (diag_final or treat_final or prev_final):
        # fallback: pick top sentences by similarity to disease
        diag_final = _rank_sentences_by_query(candidate_sentences, disease, top_n=per_section)

    # build suggestion string (extractive, verbatim from KB)
    def build_section_text(title, items):
        if not items:
            return f"{title}:\n- Not available.\n"
        lines = [f"- {it}" for it in items]
        return f"{title}:\n" + "\n".join(lines) + "\n"

    suggestion_parts = []
    suggestion_parts.append(build_section_text("Diagnosis", diag_final))
    suggestion_parts.append(build_section_text("Treatment", treat_final))
    suggestion_parts.append(build_section_text("Prevention", prev_final))
    suggestion_text = "\n".join(suggestion_parts).strip()

    # combined source chunks (for auditing) - include only the chosen sentences
    source_chunks = diag_final + treat_final + prev_final

    return source_chunks, suggestion_text

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
        source_sentences, suggestion_text = retrieve_chunks_for_disease(disease, top_k=config.TOP_K, per_section=2)
        suggestions.append({
            "disease": disease,
            "source_chunks": source_sentences,
            "suggestion": suggestion_text
        })

    return {
        "DESYNPUF_ID": desynpuf_id,
        "diseases": diseases,
        "suggestions": suggestions
    }
