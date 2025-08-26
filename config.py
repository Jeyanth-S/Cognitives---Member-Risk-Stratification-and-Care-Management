# config.py
import pinecone
# from openai import OpenAI

# Keys (replace with your real ones)
# OPENAI_API_KEY = "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"
PINECONE_API_KEY = "pcsk_21v5L9_KcXSiqLsDwZLxMYdz5aHu6vvh9EtPAvLZDTBAQqGdwAKMEgPJ7GFsk1VGavdhh2"
PINECONE_ENV = "us-east-1"
PINECONE_INDEX_NAME = "rag"

# Initialize clients
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384 
