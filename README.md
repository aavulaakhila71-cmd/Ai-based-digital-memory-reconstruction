# AI-Based Digital Memory Reconstruction System

A personal digital memory management system that stores, organizes, searches, and reconstructs relevant information from previously saved notes, events, and documents. Built with Python Flask, SQLite, and PyPDF.

## Features

- **Memory Management** — Add, edit, delete, and organize memories with categories, tags, and dates
- **Document Management** — Upload PDF and TXT files, extract text automatically, view and delete documents
- **Memory Reconstruction Chat** — Ask questions about your stored information; the system retrieves relevant memories and documents and composes an answer with cited sources
- **Smart Search** — Keyword search across memory titles, content, tags, and document text with relevance ranking and category filters
- **Memory Timeline** — View memories chronologically with date and category filters
- **Dashboard** — Overview of total memories, documents, categories, and recent activity
- **Settings** — System info, privacy details, and data management

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python Flask |
| Database | SQLite |
| Document Processing | PyPDF2 |
| Frontend | HTML5, CSS3, JavaScript (vanilla) |
| Search | Keyword-based retrieval engine (SQLite) |

## Project Structure

```
AI-Based-Digital-Memory-Reconstruction-System/
├── app.py                  # Flask application with all routes
├── database.py             # SQLite database schema and CRUD operations
├── memory_engine.py        # Retrieval-based search and answer composition
├── document_processor.py   # PDF/TXT text extraction
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── templates/             # HTML templates (Jinja2)
│   ├── base.html
│   ├── dashboard.html
│   ├── memories.html
│   ├── add_memory.html
│   ├── edit_memory.html
│   ├── documents.html
│   ├── reconstruct.html
│   ├── timeline.html
│   ├── settings.html
│   └── error.html
├── static/
│   ├── css/style.css       # Application styles
│   └── js/
│       ├── app.js          # Shared functionality
│       ├── memories.js     # Memory form handling
│       ├── documents.js    # Document upload/view/delete
│       └── reconstruct.js  # Chat interface
├── uploads/                # Uploaded files (created automatically)
├── tests/
│   ├── test_database.py
│   ├── test_memory_engine.py
│   ├── test_document_processor.py
│   ├── test_app.py
│   └── run_all.py
└── memory.db              # SQLite database (created automatically on first run)
```

## Setup Instructions (Windows)

### Step 1: Install Python

1. Download Python 3.9 or later from [python.org](https://www.python.org/downloads/)
2. During installation, check **"Add Python to PATH"**
3. Verify installation by opening Command Prompt and running:
   ```
   python --version
   ```

### Step 2: Create a Virtual Environment

1. Open Command Prompt and navigate to the project folder:
   ```
   cd path\to\AI-Based-Digital-Memory-Reconstruction-System
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   ```
   venv\Scripts\activate
   ```
   You should see `(venv)` at the beginning of your command prompt.

### Step 3: Install Dependencies

With the virtual environment activated, run:
```
pip install -r requirements.txt
```

### Step 4: Run the Application

```
python app.py
```

The application will start and you should see:
```
 * Running on http://127.0.0.1:5000
```

Open your web browser and go to **http://127.0.0.1:5000**

### Step 5: Run Tests (Optional)

To verify everything is working correctly:
```
python tests\run_all.py
```

## Usage Guide

### Adding a Memory
1. Click **"Add Memory"** in the sidebar
2. Enter a title, select a category, add optional tags, and write the content
3. Click **"Save Memory"**

### Uploading Documents
1. Go to the **"Documents"** page
2. Drag and drop a PDF or TXT file onto the upload zone, or click to browse
3. The system extracts text automatically — click **"View"** to see extracted content

### Reconstructing a Memory (Chat)
1. Click **"Reconstruct Memory"** in the sidebar
2. Type a question about your stored information (or click a suggestion chip)
3. The system searches your memories and documents and returns an answer with source citations
4. If no relevant information is found, the system says so clearly — it does not fabricate answers

### Searching
Use the search endpoint via the chat or search API to find memories and documents by keyword. Results are ranked with title matches weighted higher than content matches.

### Timeline
1. Go to **"Memory Timeline"**
2. Filter by category or date range
3. Click any timeline entry to view the full memory

## Important Notes

- **Privacy**: All data is stored locally on your machine. No data is sent to external services.
- **Retrieval-based, not AI**: The reconstruction chat uses a keyword-based retrieval engine, not an LLM. It searches your stored data and composes answers from the findings. When no matching data exists, it clearly states that instead of inventing an answer.
- **Future LLM Integration**: The architecture is designed so an LLM can be plugged in by replacing the `compose_answer` function in `memory_engine.py`. The retrieval layer would feed context to the LLM for natural-language generation.
- **File Upload Limits**: Maximum file size is 10 MB. Only PDF and TXT files are accepted.
- **Sample Data**: Five sample memories are inserted automatically on first run for demonstration purposes.

## Security Features

- Parameterized SQL queries throughout (prevents SQL injection)
- File extension validation for uploads
- File size limit enforcement
- Safe file naming with UUID (prevents path traversal)
- No stack traces or server errors exposed to the UI
- No external data transmission

## Categories

- Personal
- Education
- Projects
- Work
- Important Events

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard page |
| GET | `/memories` | Memories list page |
| GET | `/memories/add` | Add memory form |
| GET | `/memories/edit/<id>` | Edit memory form |
| GET | `/documents` | Documents page |
| GET | `/reconstruct` | Chat page |
| GET | `/timeline` | Timeline page |
| GET | `/settings` | Settings page |
| POST | `/api/memories` | Create a memory |
| GET | `/api/memories/<id>` | Get a memory |
| PUT | `/api/memories/<id>` | Update a memory |
| DELETE | `/api/memories/<id>` | Delete a memory |
| POST | `/api/documents/upload` | Upload a document |
| GET | `/api/documents/<id>` | Get document details |
| DELETE | `/api/documents/<id>` | Delete a document |
| GET | `/api/search?q=...` | Search memories and documents |
| POST | `/api/reconstruct` | Reconstruct an answer |
| GET | `/api/chat/history/<session_id>` | Get chat history |
| DELETE | `/api/chat/clear/<session_id>` | Clear chat history |
| GET | `/api/dashboard/stats` | Dashboard statistics |
| POST | `/api/settings/reinsert-samples` | Reinsert sample data |

## License

This project is created for educational purposes as a B.Tech project.
