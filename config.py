# import pinecone
# import sentence_transformers

# PINECONE_API_KEY = "pcsk_21v5L9_KcXSiqLsDwZLxMYdz5aHu6vvh9EtPAvLZDTBAQqGdwAKMEgPJ7GFsk1VGavdhh2"
# PINECONE_ENV = "us-east-1"
# PINECONE_INDEX_NAME = "cognitives"

# EMBEDDING_MODEL = "all-MiniLM-L6-v2"
# EMBEDDING_DIM = 384

import os 

# Pinecone / Index config - set these as environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "pcsk_21v5L9_KcXSiqLsDwZLxMYdz5aHu6vvh9EtPAvLZDTBAQqGdwAKMEgPJ7GFsk1VGavdhh2")
PINECONE_ENV = os.getenv("PINECONE_ENV", "us-east1-gcp")  # replace if needed
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "demo")

# Embedding model (sentence-transformers)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

# Local file paths (update to your paths)
MEDICAL_TEXT_PATH = os.getenv("MEDICAL_TEXT_PATH", r"C:\Users\ashraf deen\Downloads\Cognitives- Member Risk Stratification and Care Management\cleaned_medical_book.txt")
PATIENT_CSV_PATH = os.getenv("PATIENT_CSV_PATH", r"C:\Users\ashraf deen\Downloads\Cognitives- Member Risk Stratification and Care Management\Cognitives---Member-Risk-Stratification-and-Care-Management\pipeline\notebooks\combined_features_2010.csv")

# Chunking config
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "450"))   # words per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# Retrieval config
TOP_K = int(os.getenv("TOP_K", "4"))

# Generator model (optional local summarizer)
GENERATIVE_MODEL = os.getenv("GENERATIVE_MODEL", "google/flan-t5-small")  # small & fast for demo
USE_LOCAL_GENERATOR = os.getenv("USE_LOCAL_GENERATOR", "true").lower() in ("true", "1", "yes")
