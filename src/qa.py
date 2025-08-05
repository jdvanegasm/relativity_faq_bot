"""
qa.py
retrieval + answer builder for the relativity faq bot

workflow:
    1) embed the user question with the same s-transformer model as build_index.py
    2) cosine search in faiss (indexflatip)
    3) pass two gates:
        • sim score ≥ SIM_THRESHOLD
        • keyword overlap ≥ 50 %
    4) if both pass → return a text answer
       else → return None so the ui triggers contact collection
"""

from __future__ import annotations

import json
import pathlib
import re
from typing import Dict, List, Tuple

import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

# paths
repo_root = pathlib.Path(__file__).resolve().parent.parent
data_dir  = repo_root / "data"

faiss_path  = data_dir / "faiss_index.bin"
chunks_path = data_dir / "chunks_emb.json"

# load artefacts
index: faiss.Index = faiss.read_index(str(faiss_path))
chunks: List[Dict] = json.loads(chunks_path.read_text())

# embed model (same as build_index)
model = SentenceTransformer("all-MiniLM-L6-v2")
model.eval()

# helpers
def embed(text: str) -> np.ndarray:
    with torch.no_grad():
        vec = model.encode(text[:512], normalize_embeddings=True)
    return np.asarray(vec, dtype="float32")


def retrieve(query: str, k: int = 3) -> List[Tuple[float, Dict]]:
    qvec = embed(query)
    scores, ids = index.search(qvec[None, :], k)
    return [(float(scores[0, i]), chunks[int(ids[0, i])]) for i in range(k)]


def keywords(text: str) -> set[str]:
    """simple tokenizer: alphanum split + drop tokens ≤2 chars"""
    return {w.lower() for w in re.split(r"[^a-zA-Z0-9]+", text) if len(w) > 2}


# main gateway
SIM_THRESHOLD = 0.40        # stricter than before
KW_RATIO_MIN  = 0.50        # ≥50 % of query keywords must appear in doc


def answer(user_q: str) -> str | None:
    """returns answer string or None when contact flow should kick in"""
    hits = retrieve(user_q, k=3)
    top_score, top_chunk = hits[0]

    # gate 1: vector similarity
    if top_score < SIM_THRESHOLD:
        return None

    # gate 2: keyword overlap ratio
    q_kw  = keywords(user_q)
    doc_kw = keywords(top_chunk["content"])
    if len(q_kw) == 0 or (len(q_kw & doc_kw) / len(q_kw)) < KW_RATIO_MIN:
        return None

    # build answer from the winning chunk
    ans_lines = [
        f"feature: {top_chunk['feature']}",
        f"type: {top_chunk['type']}",
        f"relativityone date: {top_chunk['relone_date']}",
        "",
        top_chunk["content"].split("description: ", 1)[-1],  # strip header
    ]
    return "\n".join(ans_lines)