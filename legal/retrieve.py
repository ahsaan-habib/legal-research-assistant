"""Jurisdiction-filtered retrieval.

The law in one place isn't the law in another, so jurisdiction is a hard
metadata filter on the vector query — never a hint in the prompt, never
something the model can widen. There is deliberately no "search everything"
function.
"""
from __future__ import annotations

from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer

from . import config
from .ingest import Provision, load_corpus

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def embedder() -> SentenceTransformer:
    return SentenceTransformer(config.EMBED_MODEL)


@lru_cache(maxsize=1)
def _col():
    return chromadb.PersistentClient(path=config.INDEX_DIR).get_or_create_collection(
        "law", metadata={"hnsw:space": "cosine"})


def index(root: str = config.CORPUS) -> int:
    provs = load_corpus(root)
    for s in range(0, len(provs), 128):
        part = provs[s:s + 128]
        _col().upsert(
            ids=[p.id for p in part],
            documents=[f"{p.section}\n{p.text}" for p in part],
            embeddings=embedder().encode([f"{p.section}\n{p.text}" for p in part], normalize_embeddings=True).tolist(),
            metadatas=[{"jurisdiction": p.jurisdiction, "instrument": p.instrument, "section": p.section}
                       for p in part])
    return len(provs)


def jurisdictions() -> list[str]:
    metas = _col().get(include=["metadatas"])["metadatas"]
    return sorted({m["jurisdiction"] for m in metas})


def search(query: str, jurisdiction: str, k: int = 5, min_score: float = 0.5) -> list[tuple[Provision, float]]:
    if not jurisdiction:
        raise ValueError("jurisdiction is required")
    vec = embedder().encode(QUERY_PREFIX + query, normalize_embeddings=True).tolist()
    res = _col().query(query_embeddings=[vec], n_results=k, where={"jurisdiction": jurisdiction.upper()})
    out = []
    for cid, doc, meta, dist in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
        if 1 - dist < min_score:
            continue
        section, _, text = doc.partition("\n")
        out.append((Provision(cid, meta["jurisdiction"], meta["instrument"], meta["section"], text), 1 - dist))
    return out


if __name__ == "__main__":
    print(f"indexed {index()} provisions across {jurisdictions()}")
