# embeddings.py
import json
import pinecone
import config
from sentence_transformers import SentenceTransformer

# --- Init local embedding model ---
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# --- Init Pinecone ---
pc = pinecone.Pinecone(api_key=config.PINECONE_API_KEY)

# Create / connect to index
if config.PINECONE_INDEX_NAME not in [i["name"] for i in pc.list_indexes()]:
    pc.create_index(
        name=config.PINECONE_INDEX_NAME,
        dimension=384,   # MiniLM-L6-v2 has 384-d embeddings
        metric="cosine"
    )
index = pc.Index(config.PINECONE_INDEX_NAME)

# --- Load knowledge base JSON ---
with open(r"C:\Users\ashraf deen\Downloads\Cognitives- Member Risk Stratification and Care Management\Cognitives---Member-Risk-Stratification-and-Care-Management\medical_suggestions_kb.json", "r") as f:
    knowledge_base = json.load(f)

# --- Upsert into Pinecone ---
for entry in knowledge_base:   # now it's a list
    feature = entry.get("feature")
    condition = entry.get("condition", "")
    suggestion = entry.get("suggestion", "")

    description = f"Feature {feature} has condition {condition} with suggestion: {suggestion}"

    try:
        emb = model.encode(description).tolist()

        index.upsert([
            {
                "id": feature,        # feature name as unique ID
                "values": emb,
                "metadata": entry     # store full entry (condition, suggestion etc.)
            }
        ])
        print(f"✅ Uploaded: {feature}")
    except Exception as e:
        print(f"⚠️ Failed for {feature}: {e}")
