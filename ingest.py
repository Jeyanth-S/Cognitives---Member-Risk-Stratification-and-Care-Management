# ingest.py
import os
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    EMBEDDING_MODEL,
    EMBEDDING_DIM,
    MEDICAL_TEXT_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP
)

# -----------------------------
# Helper: split text into chunks
# -----------------------------
def chunk_text(text, chunk_size=450, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

# -----------------------------
# Step 1: Load model & Pinecone
# -----------------------------
print("Loading embedding model...")
embedder = SentenceTransformer(EMBEDDING_MODEL)

print("Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)

# -----------------------------
# Step 2: Create index (if not exists)
# -----------------------------
if PINECONE_INDEX_NAME not in pc.list_indexes().names():
    print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}")
    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=EMBEDDING_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")  # change region if needed
    )

index = pc.Index(PINECONE_INDEX_NAME)

# -----------------------------
# Step 3: Load medical text and embed
# -----------------------------
print("Reading medical text...")
with open(r"C:\Users\ashraf deen\Downloads\Cognitives- Member Risk Stratification and Care Management\cleaned_medical_book.txt", "r", encoding="utf-8") as f:
    text_data = f.read()

chunks = chunk_text(text_data, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
print(f"Total chunks created: {len(chunks)}")

# -----------------------------
# Step 4: Upsert embeddings
# -----------------------------
print("Generating embeddings and uploading to Pinecone...")
vectors = []
for i, chunk in enumerate(chunks):
    emb = embedder.encode(chunk).tolist()
    vectors.append((f"chunk-{i}", emb, {"text": chunk}))

# Batch upload to Pinecone
for i in range(0, len(vectors), 100):
    batch = vectors[i:i+100]
    index.upsert(batch)

print("✅ Ingestion complete! Data is now stored in Pinecone.")
