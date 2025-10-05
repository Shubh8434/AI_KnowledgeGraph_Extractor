from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
from datetime import datetime
import os

from database import get_db, engine, Base
from models import Document, Node, Edge, Version
from schemas import DocumentResponse, GraphResponse, VersionListResponse
from services import DocumentProcessor, KnowledgeGraphExtractor
from config import settings
from fastapi import Form
# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Powered Knowledge Graph Builder",
    description="Extract entities and relationships from documents using AI",
    version="1.0.0"
)

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Initialize services
doc_processor = DocumentProcessor()
kg_extractor = KnowledgeGraphExtractor()


@app.get("/")
async def root():
    return {
        "message": "AI-Powered Knowledge Graph Builder API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/documents/upload",
            "list_documents": "/documents",
            "get_graph": "/documents/{document_id}/graph",
            "get_version": "/documents/{document_id}/versions/{version_number}",
            "list_versions": "/documents/{document_id}/versions"
        }
    }


@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document (PDF, DOCX, TXT, CSV) and extract knowledge graph
    """
    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.txt', '.csv']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Save file
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract text content
        text_content = doc_processor.extract_text(file_path, file_ext)
        
        # Create document record
        document = Document(
            filename=file.filename,
            file_type=file_ext[1:],  # Remove the dot
            file_path=file_path,
            upload_date=datetime.utcnow(),
            text_content=text_content
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Extract knowledge graph
        graph_data = kg_extractor.extract_graph(text_content)
        
        # Create version
        version = Version(
            document_id=document.id,
            version_number=1,
            created_at=datetime.utcnow()
        )
        db.add(version)
        db.commit()
        db.refresh(version)
        
        # Store nodes
        node_map = {}
        for node_data in graph_data['nodes']:
            node = Node(
                document_id=document.id,
                version_id=version.id,
                node_id=node_data['id'],
                label=node_data['label'],
                node_type=node_data['type']
            )
            db.add(node)
            db.commit()
            db.refresh(node)
            node_map[node_data['id']] = node.id
        
        # Store edges
        for edge_data in graph_data['edges']:
            edge = Edge(
                document_id=document.id,
                version_id=version.id,
                source_node_id=edge_data['source'],
                target_node_id=edge_data['target'],
                relationship_type=edge_data['relationship']
            )
            db.add(edge)
        
        db.commit()
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            upload_date=document.upload_date,
            status="success",
            message="Document processed and knowledge graph extracted"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents(db: Session = Depends(get_db)):
    """
    List all uploaded documents
    """
    documents = db.query(Document).all()
    return [
        DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            file_type=doc.file_type,
            upload_date=doc.upload_date,
            status="success"
        )
        for doc in documents
    ]


@app.get("/documents/{document_id}/graph", response_model=GraphResponse)
async def get_graph(document_id: int, db: Session = Depends(get_db)):
    """
    Get the latest knowledge graph for a document
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get latest version
    latest_version = db.query(Version).filter(
        Version.document_id == document_id
    ).order_by(Version.version_number.desc()).first()
    
    if not latest_version:
        raise HTTPException(status_code=404, detail="No graph version found")
    
    # Get nodes and edges
    nodes = db.query(Node).filter(
        Node.document_id == document_id,
        Node.version_id == latest_version.id
    ).all()
    
    edges = db.query(Edge).filter(
        Edge.document_id == document_id,
        Edge.version_id == latest_version.id
    ).all()
    
    return GraphResponse(
        document_id=str(document_id),
        version=latest_version.version_number,
        nodes=[
            {
                "id": node.node_id,
                "label": node.label,
                "type": node.node_type
            }
            for node in nodes
        ],
        edges=[
            {
                "source": edge.source_node_id,
                "target": edge.target_node_id,
                "relationship": edge.relationship_type
            }
            for edge in edges
        ]
    )


@app.get("/documents/{document_id}/versions", response_model=VersionListResponse)
async def list_versions(document_id: int, db: Session = Depends(get_db)):
    """
    List all versions for a document
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    versions = db.query(Version).filter(
        Version.document_id == document_id
    ).order_by(Version.version_number.desc()).all()
    
    return VersionListResponse(
        document_id=document_id,
        versions=[
            {
                "version_number": v.version_number,
                "created_at": v.created_at
            }
            for v in versions
        ]
    )

@app.post("/documents/{document_id}/update", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    new_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Update an existing document by adding new text or uploading a new version.
    Creates a new version of the knowledge graph.
    """
    # Fetch existing document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get latest version number
    latest_version = db.query(Version).filter(
        Version.document_id == document_id
    ).order_by(Version.version_number.desc()).first()
    next_version_number = (latest_version.version_number + 1) if latest_version else 1

    print(f"new_text: {new_text}")
    # Case 1: Update via new text
    if new_text:
        updated_text = document.text_content + "\n" + new_text
    # Case 2: Update via new file
    elif file:
        file_ext = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = ['.pdf', '.docx', '.txt', '.csv']
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}")

        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        new_text_content = doc_processor.extract_text(file_path, file_ext)
        updated_text = document.text_content + "\n" + new_text_content
    else:
        raise HTTPException(status_code=400, detail="Provide either new_text or a file for update")

    # Update text content in document
    document.text_content = updated_text
    db.commit()
    db.refresh(document)

    # Extract new graph
    graph_data = kg_extractor.extract_graph(updated_text)

    # Create new version
    new_version = Version(
        document_id=document.id,
        version_number=next_version_number,
        created_at=datetime.utcnow()
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    # Store new nodes
    node_map = {}
    for node_data in graph_data['nodes']:
        node = Node(
            document_id=document.id,
            version_id=new_version.id,
            node_id=node_data['id'],
            label=node_data['label'],
            node_type=node_data['type']
        )
        db.add(node)
        db.commit()
        db.refresh(node)
        node_map[node_data['id']] = node.id

    # Store new edges
    for edge_data in graph_data['edges']:
        edge = Edge(
            document_id=document.id,
            version_id=new_version.id,
            source_node_id=edge_data['source'],
            target_node_id=edge_data['target'],
            relationship_type=edge_data['relationship']
        )
        db.add(edge)
    db.commit()

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        file_type=document.file_type,
        upload_date=document.upload_date,
        status="success",
        message=f"Document updated and new version {next_version_number} created"
    )


@app.get("/documents/{document_id}/versions/{version_number}", response_model=GraphResponse)
async def get_version(
    document_id: int,
    version_number: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific version of the knowledge graph
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    version = db.query(Version).filter(
        Version.document_id == document_id,
        Version.version_number == version_number
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    nodes = db.query(Node).filter(
        Node.document_id == document_id,
        Node.version_id == version.id
    ).all()
    
    edges = db.query(Edge).filter(
        Edge.document_id == document_id,
        Edge.version_id == version.id
    ).all()
    
    return GraphResponse(
        document_id=str(document_id),
        version=version.version_number,
        nodes=[
            {
                "id": node.node_id,
                "label": node.label,
                "type": node.node_type
            }
            for node in nodes
        ],
        edges=[
            {
                "source": edge.source_node_id,
                "target": edge.target_node_id,
                "relationship": edge.relationship_type
            }
            for edge in edges
        ]
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)