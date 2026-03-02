from fastapi import APIRouter, BackgroundTasks, HTTPException
from models.schemas import DocumentIngest
from rag.ingestion import load_all_documents
from rag.chunker import chunk_documents
from rag.vector_store import get_vector_store

router = APIRouter()


def run_ingestion_pipeline():
    """Run the full document ingestion pipeline."""
    print("\n=== Starting Document Ingestion Pipeline ===")
    
    # Step 1: Load documents
    print("Step 1: Loading documents...")
    documents = load_all_documents()
    if not documents:
        print("No documents found to ingest!")
        return
    print(f"  Loaded {len(documents)} documents")
    
    # Step 2: Chunk documents
    print("Step 2: Chunking documents...")
    chunks = chunk_documents(documents)
    
    # Step 3: Generate embeddings and build vector index
    print("Step 3: Generating embeddings and building vector index...")
    vector_store = get_vector_store()
    vector_store.build_index(chunks)
    
    print("=== Ingestion Pipeline Complete ===\n")


@router.post("/ingest")
async def ingest_documents(background_tasks: BackgroundTasks):
    """Trigger document ingestion pipeline."""
    background_tasks.add_task(run_ingestion_pipeline)
    return {
        "message": "Document ingestion started in background. This may take a few minutes.",
        "status": "processing"
    }


@router.post("/ingest/sync")
async def ingest_documents_sync():
    """Trigger document ingestion synchronously (blocks until complete)."""
    try:
        run_ingestion_pipeline()
        vector_store = get_vector_store()
        return {
            "message": "Document ingestion complete",
            "chunks_indexed": len(vector_store.chunks),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/status")
async def get_index_status():
    """Check vector store status."""
    vector_store = get_vector_store()
    sources = list(set(c["source"] for c in vector_store.chunks)) if vector_store.chunks else []
    return {
        "total_chunks": len(vector_store.chunks),
        "sources": sources,
        "is_ready": len(vector_store.chunks) > 0
    }
