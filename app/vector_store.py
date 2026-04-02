import chromadb
from typing import List, Dict

# One persistent client shared across the whole app
_client = chromadb.PersistentClient(path="./chroma_db")


def get_or_create_collection(namespace: str):
    """
    Get an existing namespace collection or create it.
    cosine similarity is used because it measures the angle between
    two vectors — works better than raw Euclidean distance for text.
    """
    return _client.get_or_create_collection(
        name=namespace,
        metadata={"hnsw:space": "cosine"}
    )


def namespace_exists(namespace: str) -> bool:
    """Check if a document namespace already exists in ChromaDB."""
    try:
        _client.get_collection(namespace)
        return True
    except Exception:
        return False


def index_chunks(namespace: str, chunks: List[Dict],
                 embeddings: List[List[float]]):
    """
    Store all chunks and their embeddings in the document's namespace.
    Each chunk stores:
      - id       : unique identifier
      - document : the raw text (so we can return it to the user)
      - embedding: the vector for similarity search
      - metadata : source filename + page number
    """
    col = get_or_create_collection(namespace)
    col.add(
        ids=[c["chunk_id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=embeddings,
        metadatas=[
            {"source": c["source"], "page": c["page"]}
            for c in chunks
        ]
    )


def search_namespaces(namespaces: List[str],
                      query_embedding: List[float],
                      n_results: int = 5) -> List[Dict]:
    """
    Search across one or multiple document namespaces.
    Merges all results and returns the top N sorted by similarity.

    This is the core of multi-document querying:
      - Loop through each selected namespace
      - Run a similarity search in each
      - Collect all results
      - Sort by distance (lower = more similar)
      - Return the top N overall
    """
    all_results = []

    for ns in namespaces:
        if not namespace_exists(ns):
            continue
        col = get_or_create_collection(ns)
        count = col.count()
        if count == 0:
            continue

        res = col.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, count),
            include=["documents", "metadatas", "distances"]
        )

        for doc, meta, dist in zip(
            res["documents"][0],
            res["metadatas"][0],
            res["distances"][0]
        ):
            all_results.append({
                "text":     doc,
                "source":   meta["source"],
                "page":     meta["page"],
                "distance": dist
            })

    # Sort ascending — lower cosine distance = more relevant
    return sorted(all_results, key=lambda x: x["distance"])[:n_results]


def delete_namespace(namespace: str):
    """Delete a document collection and all its vectors from ChromaDB."""
    if namespace_exists(namespace):
        _client.delete_collection(namespace)


def get_all_namespaces() -> List[str]:
    """Return all collection names currently stored in ChromaDB."""
    return [c.name for c in _client.list_collections()]


def get_namespace_chunk_count(namespace: str) -> int:
    """Return how many chunks are stored in a namespace."""
    if not namespace_exists(namespace):
        return 0
    return get_or_create_collection(namespace).count()