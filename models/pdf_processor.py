# models/pdf_processor.py
import os
import re
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from typing import List

# Configurações
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"   # leve e eficaz
EMBED_DIM = 384                         # dimensão do modelo all-MiniLM-L6-v2
CHUNK_SIZE = 500                        #palavras por chunk
CHUNK_OVERLAP = 80                      # overlap entre chunks (palavras)
TOP_K = 4                               # trechos retornados por busca

PERSIST_DIR = "uploads/indices"
os.makedirs(PERSIST_DIR, exist_ok=True)

# Carrega modelo de embedding
embed_model = SentenceTransformer(EMBED_MODEL_NAME)

# Estruturas em memória
_index = None
_chunks = []
_index_meta = {} 


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", " ")
    text = re.sub(r"\n+", "\n", text)              #agrupa quebras de linha
    text = re.sub(r"-\n+", "", text)               #junta palavras que termina com hífen
    text = re.sub(r"\n", " ", text)                #novas linhas por espaço
    text = re.sub(r"\s+", " ", text)               #muitos espaços
    text = re.sub(r"Página \d+ de \d+", " ", text, flags=re.IGNORECASE)
    return text.strip()


def chunk_text_by_words(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    n = len(words)
    while start < n:
        end = start + chunk_size
        chunk = words[start:end]
        chunks.append(" ".join(chunk))
        if end >= n:
            break
        start = end - overlap
    return chunks


def _build_faiss_index(vectors: np.ndarray):
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(vectors)
    index.add(vectors)
    return index


def _save_index(index: faiss.Index, chunks: List[str], base_filename: str):
    # Salva índice e chunks para persistência
    safe_name = os.path.splitext(os.path.basename(base_filename))[0]
    idx_path = os.path.join(PERSIST_DIR, f"{safe_name}.index")
    chunks_path = os.path.join(PERSIST_DIR, f"{safe_name}_chunks.json")
    faiss.write_index(index, idx_path)
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)


def _load_index(base_filename: str):
    safe_name = os.path.splitext(os.path.basename(base_filename))[0]
    idx_path = os.path.join(PERSIST_DIR, f"{safe_name}.index")
    chunks_path = os.path.join(PERSIST_DIR, f"{safe_name}_chunks.json")
    if not os.path.exists(idx_path) or not os.path.exists(chunks_path):
        return None, None
    index = faiss.read_index(idx_path)
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    return index, chunks


def learn_pdf(text: str, source_filename: str = "document"):
    """
    Processa texto: limpa, chunk, gera embeddings, cria e salva índice FAISS.
    Retorna meta com número de chunks.
    """
    global _index, _chunks, _index_meta

    cleaned = clean_text(text)
    chunks = chunk_text_by_words(cleaned)

    if not chunks:
        _chunks = []
        _index = None
        return {"success": False, "reason": "no_text", "chunks": 0}

    # Gera embeddings
    embeddings = embed_model.encode(chunks, show_progress_bar=False, convert_to_numpy=True)
    # Converter para float32
    if embeddings.dtype != np.float32:
        embeddings = embeddings.astype("float32")

    faiss.normalize_L2(embeddings)

    # Constroi índice FAISS
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    # Atualiza memória
    _index = index
    _chunks = chunks
    _index_meta = {"source_filename": source_filename, "n_chunks": len(chunks)}

    # Persiste índice e chunks
    _save_index(index, chunks, source_filename)

    return {"success": True, "chunks": len(chunks)}


def search(query: str, top_k: int = TOP_K):
    """
    Retorna os top_k chunks mais relevantes para a query.
    """
    global _index, _chunks
    if _index is None or not _chunks:
        return []

    q_emb = embed_model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(q_emb)
    distances, indices = _index.search(q_emb, top_k)
    indices = indices[0].tolist()
    results = []
    for idx in indices:
        if idx < 0 or idx >= len(_chunks):
            continue
        results.append(_chunks[idx])
    return results


def reset():
    """Limpar índice em memória e arquivos persistidos."""
    global _index, _chunks, _index_meta
    _index = None
    _chunks = []
    _index_meta = {}
    for fname in os.listdir(PERSIST_DIR):
        path = os.path.join(PERSIST_DIR, fname)
        try:
            os.remove(path)
        except Exception:
            pass
