"""
build_index.py
turns the scraped json into:
    • faiss ip index  -> data/faiss_index.bin
    • json embeddings -> data/chunks_emb.json
run right after scrape.py or via refresh_index.sh
"""

# imports
from __future__ import annotations

import json
import pathlib
import sys
from typing import Dict, List

import faiss
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import torch
from tqdm import tqdm

# env
load_dotenv()

# paths
repo_root = pathlib.Path(__file__).resolve().parent.parent
data_dir  = repo_root / "data"

chunks_path = data_dir / "chunks.json"
emb_json    = data_dir / "chunks_emb.json"
faiss_path  = data_dir / "faiss_index.bin"

# guard
if not chunks_path.exists():
    sys.exit("chunks.json not found – run scrape.py first")

# constants
emb_model_name = "all-MiniLM-L6-v2"

# init local model
model = SentenceTransformer(emb_model_name)
model.eval()

# helper
def get_emb(text: str) -> List[float]:
    """local embedding using sentence-transformers; no quota limits"""
    with torch.no_grad():
        vec = model.encode(text[:512],
                           show_progress_bar=False,
                           normalize_embeddings=True)
    return vec.tolist()

# load chunks
chunks: List[Dict] = json.loads(chunks_path.read_text())
print(f"embedding {len(chunks)} chunks -> faiss")

# build matrix
vecs = []
for c in tqdm(chunks, desc="local vectors"):
    if "embedding" not in c:
        c["embedding"] = get_emb(c["content"])
    vecs.append(c["embedding"])

matrix = np.asarray(vecs, dtype="float32")

# faiss index
index = faiss.IndexFlatIP(matrix.shape[1])
index.add(matrix)
faiss.write_index(index, str(faiss_path))
print(f"faiss index saved -> {faiss_path}")

# json with embeddings 
emb_json.write_text(json.dumps(chunks))
print(f"json with embeddings saved -> {emb_json}")

print("indexing done")