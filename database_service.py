"""
Database service module for optimized database operations
Handles batching, transactions, and performance optimizations.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import contextmanager
import logging

from models import Document, Version, Node, Edge
from validators import DataValidator

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service class for optimized database operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        try:
            yield self.db
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
    
    def create_document_with_graph(
        self, 
        filename: str, 
        file_type: str, 
        file_path: str, 
        text_content: str,
        graph_data: Dict[str, Any]
    ) -> Document:
        """
        Create a document with its knowledge graph in a single optimized transaction
        
        Args:
            filename: Document filename
            file_type: Document file type
            file_path: Path to the file
            text_content: Extracted text content
            graph_data: Validated knowledge graph data
            
        Returns:
            Created document object
        """
        with self.transaction():
            # Create document
            document = Document(
                filename=filename,
                file_type=file_type,
                file_path=file_path,
                text_content=text_content
            )
            self.db.add(document)
            self.db.flush()  # Get the ID without committing
            
            # Create version
            version = Version(
                document_id=document.id,
                version_number=1
            )
            self.db.add(version)
            self.db.flush()  # Get the ID without committing
            
            # Batch create nodes
            nodes = self._create_nodes_batch(document.id, version.id, graph_data['nodes'])
            
            # Batch create edges
            edges = self._create_edges_batch(document.id, version.id, graph_data['edges'])
            
            logger.info(f"Created document {document.id} with {len(nodes)} nodes and {len(edges)} edges")
            
            return document
    
    def update_document_with_graph(
        self,
        document_id: int,
        updated_text: str,
        graph_data: Dict[str, Any]
    ) -> Document:
        """
        Update a document with new knowledge graph in a single optimized transaction
        
        Args:
            document_id: ID of the document to update
            updated_text: Updated text content
            graph_data: Validated knowledge graph data
            
        Returns:
            Updated document object
        """
        with self.transaction():
            # Get document
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Update text content
            document.text_content = updated_text
            
            # Get next version number
            latest_version = self.db.query(Version).filter(
                Version.document_id == document_id
            ).order_by(Version.version_number.desc()).first()
            next_version_number = (latest_version.version_number + 1) if latest_version else 1
            
            # Create new version
            new_version = Version(
                document_id=document.id,
                version_number=next_version_number
            )
            self.db.add(new_version)
            self.db.flush()  # Get the ID without committing
            
            # Batch create nodes
            nodes = self._create_nodes_batch(document.id, new_version.id, graph_data['nodes'])
            
            # Batch create edges
            edges = self._create_edges_batch(document.id, new_version.id, graph_data['edges'])
            
            logger.info(f"Updated document {document.id} with version {next_version_number}: {len(nodes)} nodes and {len(edges)} edges")
            
            return document
    
    def _create_nodes_batch(self, document_id: int, version_id: int, nodes_data: List[Dict]) -> List[Node]:
        """Create multiple nodes in a single batch operation"""
        nodes = []
        
        for node_data in nodes_data:
            node = Node(
                document_id=document_id,
                version_id=version_id,
                node_id=node_data['id'],
                label=node_data['label'],
                node_type=node_data['type']
            )
            nodes.append(node)
        
        # Add all nodes at once
        self.db.add_all(nodes)
        self.db.flush()  # Flush to get IDs
        
        return nodes
    
    def _create_edges_batch(self, document_id: int, version_id: int, edges_data: List[Dict]) -> List[Edge]:
        """Create multiple edges in a single batch operation"""
        edges = []
        
        for edge_data in edges_data:
            edge = Edge(
                document_id=document_id,
                version_id=version_id,
                source_node_id=edge_data['source'],
                target_node_id=edge_data['target'],
                relationship_type=edge_data['relationship']
            )
            edges.append(edge)
        
        # Add all edges at once
        self.db.add_all(edges)
        self.db.flush()  # Flush to get IDs
        
        return edges
    
    def get_document_graph_optimized(self, document_id: int, version_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get document graph with optimized queries
        
        Args:
            document_id: Document ID
            version_id: Optional specific version ID
            
        Returns:
            Graph data with nodes and edges
        """
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Get version
        if version_id:
            version = self.db.query(Version).filter(
                Version.document_id == document_id,
                Version.id == version_id
            ).first()
        else:
            version = self.db.query(Version).filter(
                Version.document_id == document_id
            ).order_by(Version.version_number.desc()).first()
        
        if not version:
            raise ValueError(f"No version found for document {document_id}")
        
        # Get nodes and edges in single queries
        nodes = self.db.query(Node).filter(
            Node.document_id == document_id,
            Node.version_id == version.id
        ).all()
        
        edges = self.db.query(Edge).filter(
            Edge.document_id == document_id,
            Edge.version_id == version.id
        ).all()
        
        return {
            'document_id': str(document_id),
            'version': version.version_number,
            'nodes': [
                {
                    'id': node.node_id,
                    'label': node.label,
                    'type': node.node_type
                }
                for node in nodes
            ],
            'edges': [
                {
                    'source': edge.source_node_id,
                    'target': edge.target_node_id,
                    'relationship': edge.relationship_type
                }
                for edge in edges
            ]
        }
    
    def get_document_versions_optimized(self, document_id: int) -> List[Dict[str, Any]]:
        """
        Get document versions with optimized query
        
        Args:
            document_id: Document ID
            
        Returns:
            List of version information
        """
        # Single query to get all versions
        versions = self.db.query(Version).filter(
            Version.document_id == document_id
        ).order_by(Version.version_number.desc()).all()
        
        return [
            {
                'version_number': version.version_number,
                'created_at': version.created_at
            }
            for version in versions
        ]
    
    def get_documents_optimized(self) -> List[Dict[str, Any]]:
        """
        Get all documents with optimized query
        
        Returns:
            List of document information
        """
        documents = self.db.query(Document).all()
        
        return [
            {
                'id': doc.id,
                'filename': doc.filename,
                'file_type': doc.file_type,
                'upload_date': doc.upload_date,
                'status': 'success'
            }
            for doc in documents
        ]
    
    def cleanup_old_versions(self, document_id: int, keep_versions: int = 10) -> int:
        """
        Clean up old versions of a document, keeping only the most recent ones
        
        Args:
            document_id: Document ID
            keep_versions: Number of recent versions to keep
            
        Returns:
            Number of versions deleted
        """
        with self.transaction():
            # Get versions to delete (oldest first)
            versions_to_delete = self.db.query(Version).filter(
                Version.document_id == document_id
            ).order_by(Version.version_number.asc()).offset(keep_versions).all()
            
            if not versions_to_delete:
                return 0
            
            version_ids = [v.id for v in versions_to_delete]
            
            # Delete associated nodes and edges first (cascade should handle this, but being explicit)
            self.db.query(Node).filter(Node.version_id.in_(version_ids)).delete(synchronize_session=False)
            self.db.query(Edge).filter(Edge.version_id.in_(version_ids)).delete(synchronize_session=False)
            
            # Delete versions
            deleted_count = self.db.query(Version).filter(
                Version.id.in_(version_ids)
            ).delete(synchronize_session=False)
            
            logger.info(f"Cleaned up {deleted_count} old versions for document {document_id}")
            return deleted_count
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics for monitoring
        
        Returns:
            Dictionary with database statistics
        """
        stats = {}
        
        # Count documents
        stats['total_documents'] = self.db.query(Document).count()
        
        # Count versions
        stats['total_versions'] = self.db.query(Version).count()
        
        # Count nodes
        stats['total_nodes'] = self.db.query(Node).count()
        
        # Count edges
        stats['total_edges'] = self.db.query(Edge).count()
        
        # Average nodes per document
        if stats['total_documents'] > 0:
            stats['avg_nodes_per_document'] = stats['total_nodes'] / stats['total_documents']
        else:
            stats['avg_nodes_per_document'] = 0
        
        # Average edges per document
        if stats['total_documents'] > 0:
            stats['avg_edges_per_document'] = stats['total_edges'] / stats['total_documents']
        else:
            stats['avg_edges_per_document'] = 0
        
        return stats