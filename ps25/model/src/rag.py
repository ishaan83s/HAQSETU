import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import joblib

CHUNKS_DIR = "ps25/model/data/legalstuff/chunks"
CLASSIFIER_DIR = "ps25/model/data/classifier"
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

vectorizer = joblib.load(f"{CLASSIFIER_DIR}/tfidf_vectorizer.joblib")
intent_model = joblib.load(f"{CLASSIFIER_DIR}/intent_classifier.joblib")
intent_to_domain = joblib.load(f"{CLASSIFIER_DIR}/intent_to_domain.joblib")

# ---- CoE Gateway client (OpenAI-compatible) ----
client = OpenAI(
    api_key=os.environ["COE_API_KEY"],
    base_url="https://ai.tcetcercd.in/v1",
)
def predict_domain(query):
    X = vectorizer.transform([query])
    predicted_intent = intent_model.predict(X)[0]
    domain = intent_to_domain.get(predicted_intent)
    return domain, predicted_intent

def retrieve(query, top_k=5, use_domain_filter=True):
    domain = None
    if use_domain_filter:
        domain, predicted_intent = predict_domain(query)
        print(f"[classifier] predicted intent: {predicted_intent} -> domain: {domain}")

    if domain:
        # Only search among chunks matching the predicted domain
        domain_indices = [i for i, r in enumerate(records) if r["domain"] == domain]
        if domain_indices:
            domain_embeddings = embeddings[domain_indices]
            temp_index = faiss.IndexFlatL2(domain_embeddings.shape[1])
            temp_index.add(domain_embeddings)

            query_vector = embed_model.encode([query])
            k = min(top_k, len(domain_indices))
            distances, local_idx = temp_index.search(query_vector, k)
            return [records[domain_indices[i]] for i in local_idx[0]]

    # Fallback: no domain predicted, or no chunks in that domain -> search everything
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