import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

CHUNKS_DIR = "ps25/model/data/legalstuff/chunks"

# Load chunk metadata
records = []
with open(f"{CHUNKS_DIR}/legal_chunks.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

# Load embeddings
embeddings = np.load(f"{CHUNKS_DIR}/embeddings.npy")
print("Loaded embeddings:", embeddings.shape)

# Build a FAISS index
# IndexFlatL2 = brute-force nearest neighbor search using Euclidean distance.
# For 9 (or even 9000) records this is plenty fast — no need for fancier index types yet.
dimension = embeddings.shape[1]  # 384
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)
print("Number of vectors in index:", index.ntotal)

# Load the same embedding model to embed the incoming query
model = SentenceTransformer("all-MiniLM-L6-v2")

def search(query, top_k=5):
    query_vector = model.encode([query])
    distances, indices = index.search(query_vector, top_k)

    print(f"\nQuery: {query}")
    print("-" * 50)
    for rank, idx in enumerate(indices[0]):
        record = records[idx]
        distance = distances[0][rank]
        print(f"{rank+1}. [{record['law_name']} Sec {record['section']}] {record['title']}")
        print(f"   distance: {distance:.4f}")
        print(f"   summary: {record['simplified_summary']}")
        print()

# Test 
search("My company hasn't paid my salary for three months.", top_k=5)