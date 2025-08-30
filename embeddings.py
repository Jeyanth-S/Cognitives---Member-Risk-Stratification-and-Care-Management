"""
Index the cleaned medical text into Pinecone.
Run this script once (or whenever you update the medical text).
"""

import os
import time
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import config 

# Load embedding model
print("Loading embedding model:", config.EMBEDDING_MODEL)
embedder = SentenceTransformer(config.EMBEDDING_MODEL)

# Initialize Pinecone client
pc = Pinecone(api_key=config.PINECONE_API_KEY)

# Check if index exists, else create
if config.PINECONE_INDEX_NAME not in pc.list_indexes().names():
    print(f"Creating index {config.PINECONE_INDEX_NAME} (dim={config.EMBEDDING_DIM}) ...")
    pc.create_index(
        name=config.PINECONE_INDEX_NAME,
        dimension=config.EMBEDDING_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-west-2")  # change region if needed
    )
    # Give Pinecone a moment
    time.sleep(5)

# Connect to index
index = pc.Index(config.PINECONE_INDEX_NAME)


def chunk_text(text, chunk_size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP):
    words = text.split()
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be larger than overlap")
    chunks = []
    start = 0
    n = len(words)
    while start < n:
        end = min(start + chunk_size, n)
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap  # apply overlap
    return chunks


def upload_chunks(file_path=config.MEDICAL_TEXT_PATH, batch_size=16):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Medical text not found at: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        full_text = f.read().strip()

    print("Chunking text...")
    chunks = chunk_text(full_text, chunk_size=config.CHUNK_SIZE, overlap=config.CHUNK_OVERLAP)
    print(f"Generated {len(chunks)} chunks.")

    for batch_start in range(0, len(chunks), batch_size):
        batch_chunks = chunks[batch_start:batch_start + batch_size]
        embs = embedder.encode(batch_chunks).tolist()
        batch = []
        for i, (chunk, emb) in enumerate(zip(batch_chunks, embs)):
            idx = batch_start + i
            metadata = {
                "chunk_id": f"chunk_{idx}",
                "text": chunk,
                "source": os.path.basename(file_path)
            }
            batch.append({"id": metadata["chunk_id"], "values": emb, "metadata": metadata})

        index.upsert(vectors=batch)
        print(f"Upserted {len(batch)} vectors (last id={batch[-1]['id']})")

    print("Indexing complete.")

if __name__ == "__main__":
    upload_chunks()
