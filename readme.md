# Quick Start Guide

Get the Knowledge Graph Builder running in 5 minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.8+)
python --version

# Check if pip is available
pip --version
```

## Installation Steps

### Step 1: Create Project Structure

```bash
# Create and enter project directory
mkdir knowledge-graph-builder
cd knowledge-graph-builder

# Create all necessary files
touch main.py models.py database.py schemas.py services.py config.py
touch requirements.txt .env.example
```

### Step 2: Copy Code Files

Copy the content from each artifact into the corresponding file:
- `main.py` → FastAPI application
- `models.py` → Database models
- `database.py` → Database configuration
- `schemas.py` → Pydantic schemas
- `services.py` → Document processing & extraction
- `config.py` → Configuration
- `requirements.txt` → Dependencies
- `.env.example` → Environment template

### Step 3: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Step 4: Setup Ollama (Local LLM)

```bash
# Install Ollama from https://ollama.ai
# Or use package manager:

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# In another terminal, pull a model
ollama pull llama3.2
```

### Step 5: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit if needed (default settings work fine)
nano .env
```

### Step 6: Run the Application

```bash
# Start the server
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 7: Test the API

Open your browser to:
- **API Root**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## Quick Test

### Option 1: Using the Demo Script

```bash
# In another terminal (keep server running)
python demo.py
```

### Option 2: Using cURL

```bash
# Create a test file
echo "John Doe works at Acme Corporation in New York." > test.txt

# Upload it
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@test.txt"

# Get the graph (replace 1 with your document ID)
curl http://localhost:8000/documents/1/graph
```

### Option 3: Using Browser

1. Go to http://localhost:8000/docs
2. Click on **POST /documents/upload**
3. Click "Try it out"
4. Upload a file
5. Click "Execute"

## Expected Output

After uploading a document, you should get a JSON response like:

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
      "label": "Acme Corporation",
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

## Troubleshooting

### "Cannot connect to Ollama"
```bash
# Start Ollama service
ollama serve

# Check if it's running
curl http://localhost:11434/api/tags
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "Database locked"
```bash
# Delete and recreate
rm knowledge_graph.db
python main.py
```

### "Port already in use"
```bash
# Use different port
uvicorn main:app --port 8001
```

## What's Next?

1. **Upload Different Files**: Try PDF, DOCX, CSV files
2. **Explore the API**: Check out all endpoints at `/docs`
3. **Customize Extraction**: Modify `services.py` for your needs
4. **Add Features**: Implement authentication, multi-doc merging, etc.

## File Structure

Your project should look like this:

```
knowledge-graph-builder/
├── main.py              # FastAPI app
├── models.py            # Database models
├── database.py          # DB configuration
├── schemas.py           # Pydantic schemas
├── services.py          # Core logic
├── config.py            # Settings
├── requirements.txt     # Dependencies
├── .env                 # Your config (git-ignored)
├── .env.example         # Config template
├── demo.py              # Demo script
├── knowledge_graph.db   # SQLite database (auto-created)
├── uploads/             # Document storage (auto-created)
└── venv/                # Virtual environment
```

## Common Commands

```bash
# Start server
python main.py

# Start with auto-reload (development)
uvicorn main:app --reload

# Run demo
python demo.py

# Check database
sqlite3 knowledge_graph.db "SELECT * FROM documents;"
```

## Success Indicators

✅ Server starts without errors  
✅ Can access http://localhost:8000  
✅ Can upload a file via `/docs`  
✅ Knowledge graph is extracted  
✅ Can retrieve graph via API  


---

