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
    prompt = f"""You are a legal awareness assistant for Indian citizens. Your job is to help people understand their legal rights in plain, simple language — you are NOT a lawyer and do not provide legal advice or representation.

Rules:
1. Answer using ONLY the legal excerpts provided below. Never invent laws, sections, or facts not present in the excerpts.
2. If the excerpts do not adequately address the user's question, say so clearly instead of guessing or stretching the excerpts to fit.
3. Always name the specific law and section you're drawing from (e.g. "Code on Wages, 2019, Section 17").
4. End your answer with one short sentence reminding the user this is general legal awareness information, not personalized legal advice, and that they should consult a lawyer or relevant authority for their specific situation.

Format your answer as:
- A short 1-2 sentence direct answer
- A brief explanation in plain language
- The relevant law/section reference

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
    result = answer_query("My Boss is not paying me.")
    print("ANSWER:\n", result["answer"])
    print("\nSOURCES:\n", result["sources"])