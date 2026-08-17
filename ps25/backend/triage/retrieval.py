"""FAISS retrieval and deterministic corpus readiness handling."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from triage.exceptions import RetrievalError
from triage.schemas import RetrievalResult, RetrievedChunk, UnderstandingResult

CORPUS_DIR = Path(__file__).resolve().parent / "corpus"
INDEX_PATH = CORPUS_DIR / "index" / "legal_corpus.index"
METADATA_PATH = CORPUS_DIR / "index" / "legal_corpus_meta.json"
_index = None
_metadata: list[dict] | None = None
_embedding_model = None
_load_error: str | None = None


def load_index() -> bool:
    """Load the curated index once, returning readiness rather than degrading."""
    global _index, _metadata, _load_error
    if _index is not None and _metadata is not None:
        return True
    try:
        if not INDEX_PATH.is_file() or not METADATA_PATH.is_file():
            raise FileNotFoundError("Curated FAISS index or metadata is missing")
        import faiss

        index = faiss.read_index(str(INDEX_PATH))
        metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
        if not isinstance(metadata, list) or index.ntotal != len(metadata):
            raise ValueError("FAISS index and metadata rows do not match")
        _index, _metadata, _load_error = index, metadata, None
        return True
    except Exception as exc:
        _index, _metadata, _load_error = None, None, str(exc)
        return False


def is_ready() -> bool:
    return load_index()


def readiness_error() -> str | None:
    load_index()
    return _load_error


def _embedding():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer

        _embedding_model = SentenceTransformer("intfloat/multilingual-e5-small", device="cpu")
    return _embedding_model


def _domain(issue: str) -> str | None:
    if issue in {"wage_nonpayment", "wrongful_termination"}:
        return "wage_employment"
    if issue == "tenancy_eviction":
        return "tenancy"
    return None


async def retrieve(*, incident_text: str, understanding: UnderstandingResult) -> RetrievalResult:
    """Apply the frozen metadata → top-8 → boost → threshold → dedup pipeline."""
    if [issue.type for issue in understanding.issues] == ["unsupported"]:
        return RetrievalResult(results=[])
    if not load_index() or _index is None or _metadata is None:
        raise RetrievalError("Legal retrieval index is unavailable")

    domains = {_domain(issue.type) for issue in understanding.issues}
    domains.discard(None)
    allowed_states = {"Maharashtra", "central"} if understanding.jurisdiction_state == "Maharashtra" else {"central"}
    candidates = [
        (position, item) for position, item in enumerate(_metadata)
        if item.get("state") in allowed_states and item.get("domain") in domains
    ]
    if not candidates:
        return RetrievalResult(results=[])

    import faiss
    import numpy as np

    vector = await asyncio.to_thread(_embedding().encode, [f"query: {incident_text}"], normalize_embeddings=True)
    query = np.asarray(vector, dtype="float32")
    # Search the exact candidate subset without adding a second index structure.
    vectors = np.vstack([_index.reconstruct(position) for position, _ in candidates]).astype("float32")
    candidate_index = faiss.IndexFlatIP(vectors.shape[1])
    candidate_index.add(vectors)
    scores, positions = candidate_index.search(query, min(8, len(candidates)))

    keyword = understanding.what.lower()
    best_by_source: dict[str, RetrievedChunk] = {}
    for score, local_position in zip(scores[0], positions[0], strict=True):
        if local_position < 0:
            continue
        _, metadata = candidates[int(local_position)]
        haystack = " ".join(str(metadata.get(key, "") or "") for key in ("title", "section", "text")).lower()
        boosted = min(1.0, float(score) + (0.1 if keyword and keyword in haystack else 0.0))
        if boosted < 0.55:
            continue
        source_id = metadata["source_id"]
        chunk = RetrievedChunk.model_validate({
            "source": {
                "title": metadata["title"], "section": metadata.get("section"),
                "jurisdictionState": metadata["state"], "sourceUrl": metadata["source_url"],
                "effectiveDate": metadata.get("effective_date"), "versionLabel": metadata.get("version_label"),
            },
            "sourceId": source_id, "passage": metadata["text"], "score": boosted,
        })
        if source_id not in best_by_source or chunk.score > best_by_source[source_id].score:
            best_by_source[source_id] = chunk
    return RetrievalResult(results=sorted(best_by_source.values(), key=lambda result: result.score, reverse=True)[:3])
