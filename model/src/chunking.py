import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

# Load the corpus
records = []
with open("ps25/model/data/legalstuff/kyr_relevant.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

print(f"Loaded {len(records)} records")

model = SentenceTransformer("all-MiniLM-L6-v2")

texts = [r["legal_text"] for r in records]
embeddings = model.encode(texts, show_progress_bar=True)

print("Embedding shape:", embeddings.shape)

# Make sure the output folder exists before writing into it
output_dir = "ps25/model/data/legalstuff/chunks"
os.makedirs(output_dir, exist_ok=True)

with open(f"{output_dir}/legal_chunks.jsonl", "w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

np.save(f"{output_dir}/embeddings.npy", embeddings)

print("Saved chunks and embeddings to:", output_dir)