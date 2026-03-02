"""
Text Chunking Module
Splits documents into overlapping chunks for vector indexing.
"""
from typing import List, Dict, Any


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100
) -> List[str]:
    """
    Split text into overlapping chunks.
    Uses sentence-aware splitting to avoid mid-sentence breaks.
    """
    # Split into sentences (rough)
    sentences = []
    current = ""
    for char in text:
        current += char
        if char in ".!?\n" and len(current) > 30:
            sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())

    # Group sentences into chunks
    chunks = []
    current_chunk = ""
    overlap_buffer = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += " " + sentence
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                # Create overlap from end of previous chunk
                words = current_chunk.split()
                overlap_words = words[-chunk_overlap // 10:] if len(words) > chunk_overlap // 10 else words
                current_chunk = " ".join(overlap_words) + " " + sentence
            else:
                current_chunk = sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return [c for c in chunks if len(c) > 20]


def chunk_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Chunk all documents and return list of chunk dicts with metadata.
    """
    all_chunks = []

    for doc in documents:
        source = doc["source"]
        content = doc["content"]
        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "chunk_id": f"{source}::chunk_{i}",
                "source": source,
                "content": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks)
            })

    print(f"  Created {len(all_chunks)} chunks from {len(documents)} documents")
    return all_chunks
