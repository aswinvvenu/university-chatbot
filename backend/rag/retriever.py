"""
RAG Retriever + LLM Integration
Retrieves relevant chunks and generates grounded responses.
"""
import os
from typing import List, Dict, Any, Tuple, Optional
from openai import OpenAI
from anthropic import Anthropic

from rag.vector_store import get_vector_store


SIMILARITY_THRESHOLD = 0.25  # Minimum similarity score to consider a chunk relevant
TOP_K = 5

SYSTEM_PROMPT = """You are the official AI assistant for Greenfield University. 
Your role is to help students, applicants, and visitors with accurate, friendly information.

STRICT RULES:
1. Answer ONLY based on the provided context from university documents and website content.
2. If the answer is not found in the provided context, politely say you don't have that information and suggest contacting the university directly.
3. Do NOT use any external knowledge or make up information.
4. Be friendly, helpful, and professional.
5. For application status queries, the system will provide the current status from the database.
6. If someone asks something completely unrelated to the university (e.g., general knowledge, weather, cooking), politely decline and redirect them.

Always end responses about admissions or applications with: "For urgent matters, call +1 (555) 234-5678."
"""
def generate_response(
    query: str,
    context: str,
    chat_history=None,
    db_context=None
) -> str:
    """Generate LLM response using retrieved context."""

    user_message = f"""Context from university documents:
{context}
"""
    if db_context:
        user_message += f"\nDatabase Information:\n{db_context}\n"
    user_message += f"\nUser Question: {query}"

    # Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if chat_history:
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    # ── 1. Try Groq (FREE, no credit card) ──────────────────────────
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=1024,
                temperature=0.3
            )
            print("SUCCESS: Used Groq ✓")
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq failed: {e}, trying next...")

    # ── 2. Try Anthropic ─────────────────────────────────────────────
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key and anthropic_key.startswith("sk-ant-"):
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=anthropic_key)
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[m for m in messages if m["role"] != "system"]
            )
            print("SUCCESS: Used Anthropic ✓")
            return response.content[0].text
        except Exception as e:
            print(f"Anthropic failed: {e}, trying next...")

    # ── 3. Try Gemini ────────────────────────────────────────────────
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            full_prompt = f"{SYSTEM_PROMPT}\n\n{user_message}"
            response = model.generate_content(full_prompt)
            print("SUCCESS: Used Gemini ✓")
            return response.text
        except Exception as e:
            print(f"Gemini failed: {e}, trying next...")

    # ── 4. Try OpenAI ────────────────────────────────────────────────
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1024
            )
            print("SUCCESS: Used OpenAI ✓")
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI failed: {e}")

    raise ValueError(
        "No working LLM found. Please get a free Groq key at console.groq.com"
    )

def retrieve_context(query: str) -> Tuple[List[Dict], List[str]]:
    """Retrieve relevant chunks for a query."""
    vector_store = get_vector_store()
    results = vector_store.search(query, top_k=TOP_K)
    
    relevant_chunks = []
    sources = []
    
    for chunk, score in results:
        if score >= SIMILARITY_THRESHOLD:
            relevant_chunks.append(chunk)
            source = chunk["source"]
            if source not in sources:
                sources.append(source)
    
    return relevant_chunks, sources


def build_context_string(chunks: List[Dict]) -> str:
    """Build context string from retrieved chunks."""
    if not chunks:
        return "No relevant context found."
    
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Source: {chunk['source']}]\n{chunk['content']}"
        )
    
    return "\n\n---\n\n".join(context_parts)

def is_out_of_scope(query: str, chunks: List[Dict]) -> bool:
    """Determine if a query is out of scope (no relevant context found)."""
    return len(chunks) == 0


def rag_query(
    query: str,
    chat_history: Optional[List[Dict]] = None,
    db_context: Optional[str] = None
) -> Tuple[str, List[str], bool]:
    """
    Main RAG pipeline:
    1. Retrieve relevant chunks
    2. Build context
    3. Generate grounded response
    Returns: (response, sources, was_answered)
    """
    chunks, sources = retrieve_context(query)
    
    if is_out_of_scope(query, chunks) and not db_context:
        out_of_scope_response = (
            "I'm sorry, I can only answer questions related to Greenfield University — "
            "our programs, admissions, fees, facilities, and policies. "
            "I don't have information on that topic. "
            "Please visit our website or contact us at info@greenfield.edu for other inquiries."
        )
        return out_of_scope_response, [], False
    
    context = build_context_string(chunks)
    response = generate_response(query, context, chat_history, db_context)
    
    return response, sources, True
