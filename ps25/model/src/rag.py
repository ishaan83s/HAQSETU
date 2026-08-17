import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI

CHUNKS_DIR = "ps25/model/data/legalstuff/chunks"

# ---- Setup (same as retrieval.py) ----
records = []
with open(f"{CHUNKS_DIR}/legal_chunks.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))

embeddings = np.load(f"{CHUNKS_DIR}/embeddings.npy")
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# ---- CoE Gateway client (OpenAI-compatible) ----
# NOTE: replace base_url below with the actual endpoint URL from the CoE gateway docs/DM reply
client = OpenAI(
    api_key=os.environ["COE_API_KEY"],
    base_url="https://ai.tcetcercd.in/v1",
)

def retrieve(query, top_k=5):
    query_vector = embed_model.encode([query])
    distances, indices = index.search(query_vector, top_k)
    return [records[idx] for idx in indices[0]]

def build_prompt(query, chunks):
    context = "\n\n".join(
        f"[{c['law_name']}, Section {c['section']}] {c['title']}\n{c['legal_text']}"
        for c in chunks
    )
    prompt = f"""You are a legal awareness assistant for Indian citizens. Answer the user's question using ONLY the legal excerpts provided below. Do not invent laws or sections that are not in the excerpts. Explain in simple, plain language. If the excerpts don't fully answer the question, say so honestly. Mention the relevant law/section name in your answer.

Legal excerpts:
{context}

User question: {query}

Answer:"""
    return prompt

def answer_query(query, top_k=5):
    chunks = retrieve(query, top_k)
    prompt = build_prompt(query, chunks)

    response = client.chat.completions.create(
        model="qwen3.6-35b-a3b",  # confirm exact model name from CoE docs
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content
    sources = [f"{c['law_name']}, Section {c['section']}" for c in chunks]

    return {"answer": answer, "sources": sources}


# Test it
if __name__ == "__main__":
    result = answer_query("My company hasn't paid my salary for three months.")
    print("ANSWER:\n", result["answer"])
    print("\nSOURCES:\n", result["sources"])