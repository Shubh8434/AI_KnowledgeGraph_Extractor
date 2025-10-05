# AI-Powered Knowledge Graph Builder

A FastAPI-based backend system that extracts entities and relationships from documents using AI/LLM to build knowledge graphs.

## Features

✅ **Document Upload**: Support for PDF, DOCX, TXT, CSV files  
✅ **AI Entity Extraction**: Automatic extraction of nodes (entities) and edges (relationships)  
✅ **Version Control**: Maintain complete graph history for each document  
✅ **RESTful API**: Clean JSON endpoints for all operations  
✅ **Dual LLM Support**: Works with Ollama (local) or OpenAI API  

## Architecture

```
├── main.py              # FastAPI application & routes
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic schemas for validation
├── database.py          # Database configuration
├── services.py          # Document processing & KG extraction
├── config.py            # Application configuration
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── uploads/             # Document storage directory
```

## Prerequisites

- Python 3.8+
- Ollama (for local LLM) OR OpenAI API key
- SQLite (default) or PostgreSQL

## Installation & Setup

### 1. Clone and Setup Environment

```bash
# Create project directory
mkdir knowledge-graph-builder
cd knowledge-graph-builder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Ollama (Recommended - Free Local LLM)

```bash
# Install Ollama from https://ollama.ai
# Pull a model
ollama pull llama3.2

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 4. Run the Application

```bash
# Start the server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

### Base URL
```
http://localhost:8000
```

### Interactive API Docs
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## API Endpoints

### 1. Upload Document

**POST** `/documents/upload`

Upload a document and extract knowledge graph.

**Request:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample.pdf"
```

**Response:**
```json
{
  "id": 1,
  "filename": "sample.pdf",
  "file_type": "pdf",
  "upload_date": "2025-10-05T10:30:00",
  "status": "success",
  "message": "Document processed and knowledge graph extracted"
}
```

---

### 2. List All Documents

**GET** `/documents`

Retrieve all uploaded documents.

**Request:**
```bash
curl -X GET "http://localhost:8000/documents"
```

**Response:**
```json
[
  {
    "id": 1,
    "filename": "sample.pdf",
    "file_type": "pdf",
    "upload_date": "2025-10-05T10:30:00",
    "status": "success"
  }
]
```

---

### 3. Get Knowledge Graph

**GET** `/documents/{document_id}/graph`

Get the latest knowledge graph for a document.

**Request:**
```bash
curl -X GET "http://localhost:8000/documents/1/graph"
```

**Response:**
```json
{
  "document_id": "1",
  "version": 1,
  "nodes": [
    {
      "id": "n1",
      "label": "John Doe",
      "type": "Person"
    },
    {
      "id": "n2",
      "label": "Acme Corp",
      "type": "Organization"
    },
    {
      "id": "n3",
      "label": "New York",
      "type": "Location"
    }
  ],
  "edges": [
    {
      "source": "n1",
      "target": "n2",
      "relationship": "works_at"
    },
    {
      "source": "n2",
      "target": "n3",
      "relationship": "located_in"
    }
  ]
}
```

---

### 4. List Document Versions

**GET** `/documents/{document_id}/versions`

Get all versions of a document's knowledge graph.

**Request:**
```bash
curl -X GET "http://localhost:8000/documents/1/versions"
```

**Response:**
```json
{
  "document_id": 1,
  "versions": [
    {
      "version_number": 2,
      "created_at": "2025-10-05T12:00:00"
    },
    {
      "version_number": 1,
      "created_at": "2025-10-05T10:30:00"
    }
  ]
}
```


---

### 5. Update Document

**POST** `/documents/{document_id}/update`

Get all versions of a document's knowledge graph.

**Request:**
```bash
curl -X POST "http://localhost:8000/documents/1/update" \
  -F "new_text=Shubham also works at Acme Corporation in Patna."

or 

curl -X POST "http://localhost:8000/documents/1/update" \
  -F "file=@updated_sample.txt"
```

**Response:**
```json
{
  "id": 1,
  "filename": "sample.txt",
  "file_type": "txt",
  "upload_date": "2025-10-05T10:30:00",
  "status": "success",
  "message": "Document updated and new version 2 created"
}
```

---
### 6. Get Specific Version

**GET** `/documents/{document_id}/versions/{version_number}`

Retrieve a specific version of the knowledge graph.

**Request:**
```bash
curl -X GET "http://localhost:8000/documents/1/versions/1"
```

**Response:**
```json
{
  "document_id": "1",
  "version": 1,
  "nodes": [...],
  "edges": [...]
}
```

---

## Database Schema

### Documents Table
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    filename VARCHAR NOT NULL,
    file_type VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    text_content TEXT
);
```

### Versions Table
```sql
CREATE TABLE versions (
    id INTEGER PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    version_number INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Nodes Table
```sql
CREATE TABLE nodes (
    id INTEGER PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    version_id INTEGER REFERENCES versions(id),
    node_id VARCHAR NOT NULL,
    label VARCHAR NOT NULL,
    node_type VARCHAR NOT NULL
);
```

### Edges Table
```sql
CREATE TABLE edges (
    id INTEGER PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    version_id INTEGER REFERENCES versions(id),
    source_node_id VARCHAR NOT NULL,
    target_node_id VARCHAR NOT NULL,
    relationship VARCHAR NOT NULL
);
```

---

## Testing with Sample Data

### Create a Sample Document

Create `sample.txt`:
```text
John Doe works at Acme Corporation in New York. 
Jane Smith founded TechStart in San Francisco. 
Acme Corporation acquired TechStart in 2024.
John Doe manages the Engineering Department.
```

### Upload and Test

```bash
# 1. Upload document
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@sample.txt"

# 2. Get the graph
curl -X GET "http://localhost:8000/documents/1/graph"

# 3. List versions
curl -X GET "http://localhost:8000/documents/1/versions"
```

---

## Using with Postman

1. Import the API into Postman
2. Create a new request
3. Set method to `POST` and URL to `http://localhost:8000/documents/upload`
4. Go to Body → form-data
5. Add key `file` (type: File) and select your document
6. Click Send

---

## Configuration Options

### Using PostgreSQL Instead of SQLite

Edit `.env`:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/kg_database
```

Install PostgreSQL driver:
```bash
pip install psycopg2-binary
```

### Using OpenAI Instead of Ollama

Edit `.env`:
```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
```

Update `services.py` to use OpenAI (modify `_extract_with_ollama` method).

---

## Project Structure Details

### `main.py`
- FastAPI application initialization
- API route definitions
- Request/response handling
- Error handling

### `models.py`
- SQLAlchemy ORM models
- Database table definitions
- Relationship mappings

### `schemas.py`
- Pydantic models for request/response validation
- Data serialization schemas

### `services.py`
- `DocumentProcessor`: Extracts text from various file formats
- `KnowledgeGraphExtractor`: Uses LLM to extract entities and relationships

### `database.py`
- Database connection management
- Session handling
- Dependency injection for routes

### `config.py`
- Environment variable management
- Application settings
- Configuration validation

---

## Extraction Methods

### LLM-Based Extraction
- Uses Ollama or OpenAI to understand document semantics
- Extracts meaningful entities and relationships
- Handles complex context and implicit relationships
---

## Troubleshooting

### Ollama Connection Error
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
ollama serve
```

### Database Locked Error
```bash
# Delete and recreate database
rm knowledge_graph.db
python main.py
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### File Upload Fails
- Check file size (default max: 10MB)
- Verify file format is supported (PDF, DOCX, TXT, CSV)
- Ensure `uploads/` directory exists and is writable

---

## Assumptions & Limitations

### Assumptions
1. Documents are in English (can be extended for multilingual support)
2. Ollama is installed locally or OpenAI API key is provided
3. SQLite is sufficient for demo (PostgreSQL recommended for production)
4. Single-user system (add authentication for multi-user)

### Current Limitations
1. No authentication/authorization implemented
2. Maximum file size: 10MB (configurable)
3. No real-time graph updates
4. Basic entity type classification
5. No graph visualization (JSON output only)

### Future Enhancements
- [ ] JWT-based authentication
- [ ] Multi-document graph merging
- [ ] Source text highlighting for entities
- [ ] Export to CSV, JSON-LD, RDF formats
- [ ] Graph visualization frontend
- [ ] Batch document processing
- [ ] Custom entity type definitions
- [ ] Relationship confidence scores

---
