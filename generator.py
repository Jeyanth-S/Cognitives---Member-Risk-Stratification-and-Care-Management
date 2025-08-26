# generator.py
from sentence_transformers import SentenceTransformer
import config

# Load embedding model
model = SentenceTransformer(config.EMBEDDING_MODEL)

def generate_embedding(text: str):
    """Generate vector embedding for input text"""
    return model.encode(text).tolist()
