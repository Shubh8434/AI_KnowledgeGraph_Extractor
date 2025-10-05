from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, csv
    file_path = Column(String(500), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    text_content = Column(Text, nullable=True)
    
    # Relationships
    nodes = relationship("Node", back_populates="document", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="document", cascade="all, delete-orphan")
    versions = relationship("Version", back_populates="document", cascade="all, delete-orphan")


class Version(Base):
    __tablename__ = "versions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="versions")
    nodes = relationship("Node", back_populates="version", cascade="all, delete-orphan")
    edges = relationship("Edge", back_populates="version", cascade="all, delete-orphan")


class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    version_id = Column(Integer, ForeignKey("versions.id", ondelete="CASCADE"), nullable=False)
    node_id = Column(String(50), nullable=False)  # e.g., "n1", "n2"
    label = Column(String(255), nullable=False)
    node_type = Column(String(100), nullable=False)  # Person, Organization, Location, etc.
    
    # Relationships
    document = relationship("Document", back_populates="nodes")
    version = relationship("Version", back_populates="nodes")


class Edge(Base):
    __tablename__ = "edges"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    version_id = Column(Integer, ForeignKey("versions.id", ondelete="CASCADE"), nullable=False)
    source_node_id = Column(String(50), nullable=False)
    target_node_id = Column(String(50), nullable=False)
    relationship_type = Column(String(100), nullable=False)  # Changed from 'relationship' to avoid conflicts
    
    # Relationships
    document = relationship("Document", back_populates="edges")
    version = relationship("Version", back_populates="edges")