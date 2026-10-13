"""
AI-Based Digital Memory Reconstruction System
Flask application with all routes for memory management, document handling,
search, chat reconstruction, and timeline views.
"""

import os
import uuid
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    redirect,
    url_for,
    flash,
)

import database as db
from document_processor import (
    allowed_file,
    extract_text,
    get_file_extension,
    validate_file_size,
)
from memory_engine import reconstruct_memory, smart_search

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CATEGORIES = ["Personal", "Education", "Projects", "Work", "Important Events"]


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    stats = db.get_dashboard_stats()
    return render_template("dashboard.html", active_page="dashboard", stats=stats, categories=CATEGORIES)


@app.route("/memories")
def memories_page():
    category = request.args.get("category", "All")
    memories = db.get_all_memories(category_filter=category)
    return render_template(
        "memories.html",
        active_page="memories",
        memories=memories,
        categories=CATEGORIES,
        current_category=category,
    )


@app.route("/memories/add")
def add_memory_page():
    return render_template("add_memory.html", active_page="add", categories=CATEGORIES)


@app.route("/memories/edit/<int:memory_id>")
def edit_memory_page(memory_id: int):
    memory = db.get_memory_by_id(memory_id)
    if memory is None:
        flash("Memory not found.", "error")
        return redirect(url_for("memories_page"))
    return render_template(
        "edit_memory.html",
        active_page="memories",
        memory=memory,
        categories=CATEGORIES,
    )


@app.route("/documents")
def documents_page():
    documents = db.get_all_documents()
    return render_template("documents.html", active_page="documents", documents=documents)


@app.route("/reconstruct")
def reconstruct_page():
    return render_template("reconstruct.html", active_page="reconstruct")


@app.route("/timeline")
def timeline_page():
    category = request.args.get("category", "All")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    memories = db.get_timeline_memories(
        category_filter=category, date_from=date_from or None, date_to=date_to or None
    )
    return render_template(
        "timeline.html",
        active_page="timeline",
        memories=memories,
        categories=CATEGORIES,
        current_category=category,
        date_from=date_from,
        date_to=date_to,
    )


@app.route("/settings")
def settings_page():
    return render_template("settings.html", active_page="settings")


# ---------------------------------------------------------------------------
# Memory API routes
# ---------------------------------------------------------------------------

@app.route("/api/memories", methods=["POST"])
def api_create_memory():
    data = request.get_json(silent=True) or request.form
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    category = data.get("category") or "Personal"
    tags = (data.get("tags") or "").strip()
    memory_date = data.get("memory_date") or datetime.now().strftime("%Y-%m-%d")

    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not content:
        return jsonify({"error": "Content is required"}), 400
    if category not in CATEGORIES:
        category = "Personal"

    mem_id = db.create_memory(title, content, category, tags, memory_date)
    return jsonify({"id": mem_id, "message": "Memory saved successfully"}), 201


@app.route("/api/memories/<int:memory_id>", methods=["PUT"])
def api_update_memory(memory_id: int):
    data = request.get_json(silent=True) or request.form
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    category = data.get("category") or "Personal"
    tags = (data.get("tags") or "").strip()
    memory_date = data.get("memory_date") or datetime.now().strftime("%Y-%m-%d")

    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not content:
        return jsonify({"error": "Content is required"}), 400

    updated = db.update_memory(memory_id, title, content, category, tags, memory_date)
    if not updated:
        return jsonify({"error": "Memory not found"}), 404
    return jsonify({"message": "Memory updated successfully"}), 200


@app.route("/api/memories/<int:memory_id>", methods=["DELETE"])
def api_delete_memory(memory_id: int):
    deleted = db.delete_memory(memory_id)
    if not deleted:
        return jsonify({"error": "Memory not found"}), 404
    return jsonify({"message": "Memory deleted successfully"}), 200


@app.route("/api/memories/<int:memory_id>")
def api_get_memory(memory_id: int):
    memory = db.get_memory_by_id(memory_id)
    if memory is None:
        return jsonify({"error": "Memory not found"}), 404
    return jsonify(
        {
            "id": memory["id"],
            "title": memory["title"],
            "content": memory["content"],
            "category": memory["category"],
            "tags": memory["tags"],
            "memory_date": memory["memory_date"],
            "created_at": memory["created_at"],
            "updated_at": memory["updated_at"],
        }
    )


# ---------------------------------------------------------------------------
# Document API routes
# ---------------------------------------------------------------------------

@app.route("/api/documents/upload", methods=["POST"])
def api_upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF and TXT files are allowed"}), 400

    # Read file content to check size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if not validate_file_size(file_size):
        return jsonify({"error": "File too large. Maximum size is 10 MB"}), 400

    # Generate safe filename
    ext = get_file_extension(file.filename)
    safe_name = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, safe_name)

    try:
        file.save(filepath)
    except Exception:
        return jsonify({"error": "Failed to save file"}), 500

    # Extract text
    extracted_text, error = extract_text(filepath, ext)
    if error:
        # Clean up the uploaded file
        try:
            os.remove(filepath)
        except OSError:
            pass
        return jsonify({"error": error}), 422

    original_filename = os.path.basename(file.filename)
    doc_id = db.create_document(
        safe_name, original_filename, ext, file_size, extracted_text
    )

    return jsonify(
        {
            "id": doc_id,
            "message": "Document uploaded and text extracted successfully",
            "filename": original_filename,
        }
    ), 201


@app.route("/api/documents/<int:doc_id>")
def api_get_document(doc_id: int):
    doc = db.get_document_by_id(doc_id)
    if doc is None:
        return jsonify({"error": "Document not found"}), 404
    return jsonify(
        {
            "id": doc["id"],
            "filename": doc["original_filename"],
            "file_type": doc["file_type"],
            "file_size": doc["file_size"],
            "extracted_text": doc["extracted_text"],
            "upload_date": doc["upload_date"],
        }
    )


@app.route("/api/documents/<int:doc_id>", methods=["DELETE"])
def api_delete_document(doc_id: int):
    stored_filename = db.delete_document(doc_id)
    if stored_filename is None:
        return jsonify({"error": "Document not found"}), 404

    # Remove file from disk
    filepath = os.path.join(UPLOAD_FOLDER, stored_filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except OSError:
            pass

    return jsonify({"message": "Document deleted successfully"}), 200


# ---------------------------------------------------------------------------
# Search API
# ---------------------------------------------------------------------------

@app.route("/api/search")
def api_search():
    query = (request.args.get("q") or "").strip()
    category = request.args.get("category", "All")

    if not query:
        return jsonify({"results": [], "count": 0, "query": ""})

    results = smart_search(query, category)
    db.save_search(query, len(results))

    return jsonify(
        {
            "results": results,
            "count": len(results),
            "query": query,
        }
    )


# ---------------------------------------------------------------------------
# Reconstruct (chat) API
# ---------------------------------------------------------------------------

@app.route("/api/reconstruct", methods=["POST"])
def api_reconstruct():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not query:
        return jsonify({"error": "Question is required"}), 400

    result = reconstruct_memory(query)

    # Save conversation
    db.save_chat_message(session_id, "user", query)
    db.save_chat_message(
        session_id,
        "assistant",
        result["answer"],
        result["sources"] and str(result["sources"]) or "",
    )

    return jsonify(
        {
            "answer": result["answer"],
            "sources": result["sources"],
            "found": result["found"],
            "session_id": session_id,
        }
    )


@app.route("/api/chat/history/<session_id>")
def api_chat_history(session_id: str):
    history = db.get_chat_history(session_id)
    messages = []
    for row in history:
        messages.append(
            {
                "role": row["role"],
                "message": row["message"],
                "created_at": row["created_at"],
            }
        )
    return jsonify({"messages": messages, "session_id": session_id})


@app.route("/api/chat/clear/<session_id>", methods=["DELETE"])
def api_chat_clear(session_id: str):
    db.clear_chat_history(session_id)
    return jsonify({"message": "Chat history cleared"}), 200


# ---------------------------------------------------------------------------
# Dashboard API
# ---------------------------------------------------------------------------

@app.route("/api/dashboard/stats")
def api_dashboard_stats():
    stats = db.get_dashboard_stats()
    # Convert Row objects to dicts for JSON
    stats["recent_memories"] = [
        {
            "id": r["id"],
            "title": r["title"],
            "category": r["category"],
            "memory_date": r["memory_date"],
            "created_at": r["created_at"],
        }
        for r in stats["recent_memories"]
    ]
    stats["recent_searches"] = [
        {
            "query": r["query"],
            "results_count": r["results_count"],
            "searched_at": r["searched_at"],
        }
        for r in stats["recent_searches"]
    ]
    return jsonify(stats)


# ---------------------------------------------------------------------------
# Settings API
# ---------------------------------------------------------------------------

@app.route("/api/settings/reinsert-samples", methods=["POST"])
def api_reinsert_samples():
    db.insert_sample_data()
    return jsonify({"message": "Sample data reinserted (if table was empty)"}), 200


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Resource not found"}), 404
    return render_template("error.html", error_code=404, error_message="Page not found"), 404


@app.errorhandler(500)
def server_error(_e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "An internal server error occurred"}), 500
    return render_template(
        "error.html", error_code=500, error_message="Something went wrong on our end"
    ), 500


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def initialize():
    """Initialize database and insert sample data on first run."""
    db.init_db()
    db.insert_sample_data()


# Initialize on import
initialize()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
