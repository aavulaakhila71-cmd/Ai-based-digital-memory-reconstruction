"""
Memory reconstruction engine.
Retrieval-based answer system that searches memories and documents
for relevant information and composes answers from the results.

This is NOT an AI/LLM — it is a keyword-based retrieval engine.
The architecture is designed so an LLM can be plugged in later
by replacing the `compose_answer` function.
"""

import re
from typing import List, Dict
from database import get_db_connection


def tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, and split into individual word tokens."""
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    return tokens


def _score_result(query_tokens: List[str], text: str, title: str = "") -> int:
    """
    Score a result based on how many query tokens appear in the text.
    Title matches are weighted higher than content matches.
    """
    text_lower = text.lower()
    title_lower = title.lower()
    score = 0
    for token in query_tokens:
        if len(token) < 2:
            continue
        # Title matches worth 3 points, content matches worth 1
        if token in title_lower:
            score += 3
        count = text_lower.count(token)
        score += min(count, 10)  # cap content frequency
    return score


def search_memories_and_documents(query: str) -> List[Dict]:
    """
    Search memories and documents for the given query.
    Returns a ranked list of result dicts with:
      - type: 'memory' or 'document'
      - id, title, content/snippet, date, score, tags, category
    """
    if not query or not query.strip():
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    results: List[Dict] = []
    conn = get_db_connection()

    # Search memories
    for row in conn.execute("SELECT * FROM memories").fetchall():
        combined = f"{row['title']} {row['content']} {row['tags']}"
        score = _score_result(query_tokens, combined, row["title"])
        if score > 0:
            results.append(
                {
                    "type": "memory",
                    "id": row["id"],
                    "title": row["title"],
                    "snippet": _make_snippet(query_tokens, row["content"]),
                    "content": row["content"],
                    "date": row["memory_date"],
                    "score": score,
                    "tags": row["tags"],
                    "category": row["category"],
                }
            )

    # Search documents
    for row in conn.execute("SELECT * FROM documents").fetchall():
        combined = f"{row['original_filename']} {row['extracted_text']}"
        score = _score_result(query_tokens, combined, row["original_filename"])
        if score > 0:
            results.append(
                {
                    "type": "document",
                    "id": row["id"],
                    "title": row["original_filename"],
                    "snippet": _make_snippet(query_tokens, row["extracted_text"]),
                    "content": row["extracted_text"],
                    "date": row["upload_date"],
                    "score": score,
                    "tags": "",
                    "category": "Document",
                }
            )

    conn.close()

    # Sort by score descending
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def _make_snippet(query_tokens: List[str], text: str, max_len: int = 200) -> str:
    """Create a short snippet around the first matching token."""
    if not text:
        return ""
    text_lower = text.lower()
    best_pos = -1
    for token in query_tokens:
        if len(token) < 2:
            continue
        pos = text_lower.find(token)
        if pos != -1:
            if best_pos == -1 or pos < best_pos:
                best_pos = pos

    if best_pos == -1:
        return text[:max_len] + ("..." if len(text) > max_len else "")

    start = max(0, best_pos - 60)
    end = min(len(text), best_pos + max_len - 60)
    snippet = text[start:end]
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


def smart_search(query: str, category_filter: str = "All") -> List[Dict]:
    """
    Smart search with category filtering. Used by the search page.
    Ranks exact title matches higher than content matches.
    """
    results = search_memories_and_documents(query)
    if category_filter and category_filter != "All":
        results = [r for r in results if r.get("category") == category_filter]
    return results


def compose_answer(query: str, results: List[Dict]) -> Dict:
    """
    Compose a retrieval-based answer from search results.

    Returns a dict with:
      - answer: the composed response text
      - sources: list of source dicts
      - found: boolean indicating whether relevant info was found

    This function does NOT use any AI or LLM. It explicitly states
    when no relevant information is found, rather than inventing answers.
    """
    if not results:
        return {
            "answer": "I couldn't find any relevant information in your stored memories or documents for that question. No data matching your query was found — try rephrasing your question or adding more memories first.",
            "sources": [],
            "found": False,
        }

    # Take top results (max 5)
    top_results = results[:5]
    sources = []
    for r in top_results:
        sources.append(
            {
                "type": r["type"],
                "title": r["title"],
                "date": r["date"],
                "category": r.get("category", ""),
                "snippet": r["snippet"],
            }
        )

    # Build answer by summarizing what was found
    answer_parts: List[str] = []
    answer_parts.append(
        f"I found {len(results)} relevant {'result' if len(results) == 1 else 'results'} in your stored information. Here's what I reconstructed:"
    )

    for i, r in enumerate(top_results, 1):
        source_label = "Memory" if r["type"] == "memory" else "Document"
        answer_parts.append(
            f"\n{i}. [{source_label}] {r['title']}"
        )
        if r["snippet"]:
            # Clean up the snippet for display
            snippet = r["snippet"].replace("\n", " ").strip()
            if len(snippet) > 150:
                snippet = snippet[:150] + "..."
            answer_parts.append(f"   {snippet}")

    answer_parts.append(
        "\nThis answer was reconstructed from your stored memories and documents using keyword-based retrieval. "
        "It is not AI-generated recall — only information you previously saved is included."
    )

    return {
        "answer": "\n".join(answer_parts),
        "sources": sources,
        "found": True,
    }


def reconstruct_memory(query: str) -> Dict:
    """
    Full reconstruction pipeline: search then compose.
    This is the main entry point for the chat interface.
    """
    results = search_memories_and_documents(query)
    return compose_answer(query, results)
