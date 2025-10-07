from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
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
from validators import validate_file_upload, validate_knowledge_graph_response, APIValidator
from database_service import DatabaseService
from security import SecurityManager
from error_handlers import (
    ErrorHandler, APIError, ValidationError as CustomValidationError, 
    NotFoundError, ProcessingError, SecurityError, create_error_response
)
# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Powered Knowledge Graph Builder",
    description="Extract entities and relationships from documents using AI",
    version="1.0.0"
)

# Add error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return ErrorHandler.handle_validation_error(exc)

@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    return ErrorHandler.handle_database_error(exc)

@app.exception_handler(APIError)
async def api_exception_handler(request: Request, exc: APIError):
    return ErrorHandler.handle_api_error(exc)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return ErrorHandler.handle_http_exception(exc)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return ErrorHandler.handle_generic_error(exc)

# Ensure upload directory exists with proper security
try:
    SecurityManager.ensure_upload_directory()
except OSError as e:
    print(f"❌ Failed to create upload directory: {e}")
    exit(1)

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
    # Validate file upload
    safe_filename, file_ext = validate_file_upload(file, file.filename)
    
    try:
        # Save file with safe filename
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract text content
        text_content = doc_processor.extract_text(file_path, file_ext)
        
        # Validate text content
        text_content = APIValidator.validate_text_content(text_content)
        
        # Extract knowledge graph
        raw_graph_data = kg_extractor.extract_graph(text_content)
        
        # Validate knowledge graph response
        graph_data = validate_knowledge_graph_response(str(raw_graph_data))
        
        # Create document with graph using optimized service
        db_service = DatabaseService(db)
        document = db_service.create_document_with_graph(
            filename=safe_filename,
            file_type=file_ext[1:],  # Remove the dot
            file_path=file_path,
            text_content=text_content,
            graph_data=graph_data
        )
        
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
    db_service = DatabaseService(db)
    documents_data = db_service.get_documents_optimized()
    
    return [
        DocumentResponse(
            id=doc['id'],
            filename=doc['filename'],
            file_type=doc['file_type'],
            upload_date=doc['upload_date'],
            status=doc['status']
        )
        for doc in documents_data
    ]


@app.get("/documents/{document_id}/graph", response_model=GraphResponse)
async def get_graph(document_id: int, db: Session = Depends(get_db)):
    """
    Get the latest knowledge graph for a document
    """
    # Validate document ID
    try:
        document_id = APIValidator.validate_document_id(document_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        db_service = DatabaseService(db)
        graph_data = db_service.get_document_graph_optimized(document_id)
        
        return GraphResponse(
            document_id=graph_data['document_id'],
            version=graph_data['version'],
            nodes=graph_data['nodes'],
            edges=graph_data['edges']
        )
    except ValueError as e:
        raise NotFoundError(f"Document {document_id} not found")


@app.get("/documents/{document_id}/versions", response_model=VersionListResponse)
async def list_versions(document_id: int, db: Session = Depends(get_db)):
    """
    List all versions for a document
    """
    # Validate document ID
    try:
        document_id = APIValidator.validate_document_id(document_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        db_service = DatabaseService(db)
        versions_data = db_service.get_document_versions_optimized(document_id)
        
        return VersionListResponse(
            document_id=document_id,
            versions=versions_data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

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
    # Validate document ID
    try:
        document_id = APIValidator.validate_document_id(document_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Fetch existing document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get latest version number
    latest_version = db.query(Version).filter(
        Version.document_id == document_id
    ).order_by(Version.version_number.desc()).first()
    next_version_number = (latest_version.version_number + 1) if latest_version else 1

    # Case 1: Update via new text
    if new_text:
        # Validate text content
        try:
            validated_text = APIValidator.validate_text_content(new_text)
            updated_text = document.text_content + "\n" + validated_text
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # Case 2: Update via new file
    elif file:
        # Validate file upload
        try:
            safe_filename, file_ext = validate_file_upload(file, file.filename)
            
            file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            new_text_content = doc_processor.extract_text(file_path, file_ext)
            validated_text = APIValidator.validate_text_content(new_text_content)
            updated_text = document.text_content + "\n" + validated_text
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Provide either new_text or a file for update")

    # Extract new graph
    raw_graph_data = kg_extractor.extract_graph(updated_text)
    
    # Validate knowledge graph response
    try:
        graph_data = validate_knowledge_graph_response(str(raw_graph_data))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Update document with graph using optimized service
    try:
        db_service = DatabaseService(db)
        document = db_service.update_document_with_graph(
            document_id=document_id,
            updated_text=updated_text,
            graph_data=graph_data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

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
    # Validate parameters
    try:
        document_id = APIValidator.validate_document_id(document_id)
        version_number = APIValidator.validate_version_number(version_number)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        db_service = DatabaseService(db)
        graph_data = db_service.get_document_graph_optimized(document_id, version_id)
        
        return GraphResponse(
            document_id=graph_data['document_id'],
            version=graph_data['version'],
            nodes=graph_data['nodes'],
            edges=graph_data['edges']
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/stats")
async def get_database_stats(db: Session = Depends(get_db)):
    """
    Get database statistics for monitoring
    """
    try:
        db_service = DatabaseService(db)
        stats = db_service.get_database_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {str(e)}")


@app.post("/documents/{document_id}/cleanup")
async def cleanup_old_versions(
    document_id: int,
    keep_versions: int = 10,
    db: Session = Depends(get_db)
):
    """
    Clean up old versions of a document
    """
    # Validate document ID
    try:
        document_id = APIValidator.validate_document_id(document_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        db_service = DatabaseService(db)
        deleted_count = db_service.cleanup_old_versions(document_id, keep_versions)
        
        return {
            "message": f"Cleaned up {deleted_count} old versions",
            "document_id": document_id,
            "versions_deleted": deleted_count
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up versions: {str(e)}")


@app.get("/security/scan")
async def scan_upload_directory():
    """
    Scan upload directory for security issues
    """
    try:
        results = SecurityManager.scan_upload_directory()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Security scan failed: {str(e)}")


@app.post("/security/validate-file")
async def validate_file_security(
    file: UploadFile = File(...)
):
    """
    Validate file security without processing
    """
    try:
        # Read file content
        content = await file.read()
        
        # Generate safe filename
        safe_filename = SecurityManager.generate_safe_filename(file.filename)
        
        # Validate security
        is_safe, reason = SecurityManager.validate_file_security(safe_filename, content)
        
        # Generate file hash
        file_hash = SecurityManager.get_file_hash(content)
        
        return {
            "filename": file.filename,
            "safe_filename": safe_filename,
            "is_safe": is_safe,
            "reason": reason,
            "file_size": len(content),
            "file_hash": file_hash,
            "mime_type": "application/octet-stream"  # Would need python-magic for actual MIME type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File validation failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)