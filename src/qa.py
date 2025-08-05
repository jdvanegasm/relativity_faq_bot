"""
qa.py
retrieval + simple answer builder for the relativity faq bot

loads the faiss index + chunks_emb.json produced by build_index.py
given a user question:
    1) embeds the question with the same sentence-transformers model
    2) does a cosine search (faiss ip)
    3) if similarity >= threshold -> returns a crafted answer
       else -> returns None  (ui will trigger contact flow)
"""

# imports --------------------------------------------------------------
from __future__ import annotations

import json
import pathlib
from typing import Dict, List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

# paths ----------------------------------------------------------------
repo_root = pathlib.Path(__file__).resolve().parent.parent
data_dir  = repo_root / "data"

faiss_path  = data_dir / "faiss_index.bin"
chunks_path = data_dir / "chunks_emb.json"

# load artefacts -------------------------------------------------------
index: faiss.Index = faiss.read_index(str(faiss_path))
chunks: List[Dict] = json.loads(chunks_path.read_text())

# load the same emb model used in build_index.py
model = SentenceTransformer("all-MiniLM-L6-v2")
model.eval()

# quick helpers --------------------------------------------------------
def embed(text: str) -> np.ndarray:
    with torch.no_grad():
        vec = model.encode(text[:512], normalize_embeddings=True)
    return np.asarray(vec, dtype="float32")

def retrieve(query: str, k: int = 3) -> List[Tuple[float, Dict]]:
    qvec = embed(query)
    scores, ids = index.search(qvec[None, :], k)
    return [(float(scores[0, i]), chunks[int(ids[0, i])]) for i in range(k)]

# main public api ------------------------------------------------------
SIM_THRESHOLD = 0.30   # tweak if necessary

def answer(user_q: str) -> str | None:
    """
    returns a plain-text answer if similarity > threshold
    else returns None so the ui knows to ask for contact info
    """
    hits = retrieve(user_q, k=3)
    top_score, top_chunk = hits[0]
    if top_score < SIM_THRESHOLD:
        return None

    # build a deterministic answer from the best chunk
    # you can make this fancier or feed context to gpt-x if you regain quota
    ans_lines = [
        f"feature: {top_chunk['feature']}",
        f"type: {top_chunk['type']}",
        f"relativityone date: {top_chunk['relone_date']}",
        "",
        top_chunk['content'].split('description: ', 1)[-1]   # strip header
    ]
    return "\n".join(ans_lines)
