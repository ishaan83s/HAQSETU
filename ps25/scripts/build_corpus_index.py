"""Manually build the FAISS corpus index from curated JSON source documents."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

CORPUS = ROOT / "backend" / "triage" / "corpus"
DOCUMENTS = CORPUS / "documents"
INDEX = CORPUS / "index" / "legal_corpus.index"
METADATA = CORPUS / "index" / "legal_corpus_meta.json"


class CorpusDocument(BaseModel):
    source_id: str = Field(alias="sourceId")
    title: str
    section: str | None
    domain: str
    jurisdiction_state: str = Field(alias="jurisdictionState")
    source_url: str = Field(alias="sourceUrl")
    effective_date: str | None = Field(alias="effectiveDate")
    version_label: str | None = Field(alias="versionLabel")
    text: str


def _chunks(document: CorpusDocument):
    text = document.text
    if len(text) <= 1500:
        yield text
        return
    paragraphs = text.split("\n\n")
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > 1200:
            yield current
            current = f"{current[-150:]}\n\n{paragraph}".strip()
        else:
            current = candidate
    if current:
        yield current


def build() -> None:
    paths = sorted(DOCUMENTS.glob("*.json"))
    if not paths:
        raise RuntimeError("No curated corpus documents found; refusing to build an empty index")
    documents = [CorpusDocument.model_validate_json(path.read_text(encoding="utf-8")) for path in paths]
    for document in documents:
        if document.domain not in {"wage_employment", "tenancy"} or document.jurisdiction_state not in {"Maharashtra", "central"}:
            raise ValueError(f"Invalid corpus vocabulary for {document.source_id}")
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np

    metadata = []
    passages = []
    for document in documents:
        for index, chunk in enumerate(_chunks(document)):
            passages.append(f"passage: {document.title} — {document.section or ''}: {chunk}")
            metadata.append({"source_id": document.source_id, "domain": document.domain, "state": document.jurisdiction_state, "title": document.title, "section": document.section, "source_url": document.source_url, "effective_date": document.effective_date, "version_label": document.version_label, "text": chunk, "chunk_index": index})
    vectors = np.asarray(SentenceTransformer("intfloat/multilingual-e5-small", device="cpu").encode(passages, normalize_embeddings=True), dtype="float32")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX))
    METADATA.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    build()
