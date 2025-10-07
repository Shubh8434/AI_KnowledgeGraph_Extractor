"""
Input validation module for AI-Powered Knowledge Graph Builder
Provides comprehensive validation for file uploads, data integrity, and API inputs.
"""

import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from fastapi import HTTPException
from config import settings


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class FileValidator:
    """Validates file uploads and file-related operations"""
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.csv'}
    
    # Maximum filename length
    MAX_FILENAME_LENGTH = 255
    
    # Dangerous filename patterns (path traversal, etc.)
    DANGEROUS_PATTERNS = [
        r'\.\./',  # Path traversal
        r'\.\.\\',  # Windows path traversal
        r'/',  # Directory separators
        r'\\',  # Windows directory separators
        r'<',  # HTML/XML injection
        r'>',  # HTML/XML injection
        r'|',  # Command injection
        r'&',  # Command injection
        r';',  # Command injection
        r'`',  # Command injection
        r'$',  # Variable substitution
        r'*',  # Wildcard
        r'?',  # Wildcard
        r'[',  # Character class
        r']',  # Character class
        r'{',  # Brace expansion
        r'}',  # Brace expansion
    ]
    
    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """
        Validate and sanitize filename
        
        Args:
            filename: The filename to validate
            
        Returns:
            Sanitized filename
            
        Raises:
            ValidationError: If filename is invalid
        """
        if not filename:
            raise ValidationError("Filename cannot be empty")
        
        if len(filename) > cls.MAX_FILENAME_LENGTH:
            raise ValidationError(f"Filename too long. Maximum length: {cls.MAX_FILENAME_LENGTH}")
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, filename):
                raise ValidationError(f"Filename contains dangerous characters: {filename}")
        
        # Remove any remaining dangerous characters
        safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        if not safe_filename:
            raise ValidationError("Filename contains no valid characters")
        
        return safe_filename
    
    @classmethod
    def validate_file_extension(cls, filename: str) -> str:
        """
        Validate file extension
        
        Args:
            filename: The filename to check
            
        Returns:
            Validated file extension (with dot)
            
        Raises:
            ValidationError: If extension is not allowed
        """
        if not filename:
            raise ValidationError("Filename cannot be empty")
        
        # Extract extension
        file_ext = Path(filename).suffix.lower()
        
        if not file_ext:
            raise ValidationError("File must have an extension")
        
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            raise ValidationError(
                f"File type not supported. Allowed types: {', '.join(cls.ALLOWED_EXTENSIONS)}"
            )
        
        return file_ext
    
    @classmethod
    def validate_file_size(cls, file_size: int) -> None:
        """
        Validate file size
        
        Args:
            file_size: Size of the file in bytes
            
        Raises:
            ValidationError: If file is too large
        """
        if file_size <= 0:
            raise ValidationError("File size must be greater than 0")
        
        if file_size > settings.MAX_FILE_SIZE:
            raise ValidationError(
                f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes "
                f"({settings.MAX_FILE_SIZE / (1024*1024):.1f} MB)"
            )
    
    @classmethod
    def validate_file_path(cls, file_path: str) -> str:
        """
        Validate and sanitize file path
        
        Args:
            file_path: The file path to validate
            
        Returns:
            Sanitized file path
            
        Raises:
            ValidationError: If path is invalid
        """
        if not file_path:
            raise ValidationError("File path cannot be empty")
        
        # Resolve the path to prevent directory traversal
        try:
            resolved_path = Path(file_path).resolve()
            upload_dir = Path(settings.UPLOAD_DIR).resolve()
            
            # Ensure the file is within the upload directory
            if not str(resolved_path).startswith(str(upload_dir)):
                raise ValidationError("File path is outside allowed directory")
            
        except Exception as e:
            raise ValidationError(f"Invalid file path: {e}")
        
        return str(resolved_path)


class DataValidator:
    """Validates data structures and content"""
    
    @classmethod
    def validate_knowledge_graph(cls, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate knowledge graph structure
        
        Args:
            graph_data: The graph data to validate
            
        Returns:
            Validated graph data
            
        Raises:
            ValidationError: If graph data is invalid
        """
        if not isinstance(graph_data, dict):
            raise ValidationError("Graph data must be a dictionary")
        
        # Validate nodes
        nodes = graph_data.get('nodes', [])
        if not isinstance(nodes, list):
            raise ValidationError("Nodes must be a list")
        
        validated_nodes = []
        node_ids = set()
        
        for i, node in enumerate(nodes):
            validated_node = cls._validate_node(node, i)
            if validated_node['id'] in node_ids:
                raise ValidationError(f"Duplicate node ID: {validated_node['id']}")
            node_ids.add(validated_node['id'])
            validated_nodes.append(validated_node)
        
        # Validate edges
        edges = graph_data.get('edges', [])
        if not isinstance(edges, list):
            raise ValidationError("Edges must be a list")
        
        validated_edges = []
        edge_pairs = set()
        
        for i, edge in enumerate(edges):
            validated_edge = cls._validate_edge(edge, i, node_ids)
            edge_key = (validated_edge['source'], validated_edge['target'], validated_edge['relationship'])
            if edge_key in edge_pairs:
                raise ValidationError(f"Duplicate edge: {edge_key}")
            edge_pairs.add(edge_key)
            validated_edges.append(validated_edge)
        
        return {
            'nodes': validated_nodes,
            'edges': validated_edges
        }
    
    @classmethod
    def _validate_node(cls, node: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Validate a single node"""
        if not isinstance(node, dict):
            raise ValidationError(f"Node {index} must be a dictionary")
        
        # Required fields
        required_fields = ['id', 'label', 'type']
        for field in required_fields:
            if field not in node:
                raise ValidationError(f"Node {index} missing required field: {field}")
        
        # Validate node ID
        node_id = str(node['id']).strip()
        if not node_id:
            raise ValidationError(f"Node {index} ID cannot be empty")
        if len(node_id) > 50:
            raise ValidationError(f"Node {index} ID too long (max 50 characters)")
        
        # Validate label
        label = str(node['label']).strip()
        if not label:
            raise ValidationError(f"Node {index} label cannot be empty")
        if len(label) > 255:
            raise ValidationError(f"Node {index} label too long (max 255 characters)")
        
        # Validate type
        node_type = str(node['type']).strip()
        if not node_type:
            raise ValidationError(f"Node {index} type cannot be empty")
        if len(node_type) > 100:
            raise ValidationError(f"Node {index} type too long (max 100 characters)")
        
        return {
            'id': node_id,
            'label': label,
            'type': node_type
        }
    
    @classmethod
    def _validate_edge(cls, edge: Dict[str, Any], index: int, valid_node_ids: set) -> Dict[str, Any]:
        """Validate a single edge"""
        if not isinstance(edge, dict):
            raise ValidationError(f"Edge {index} must be a dictionary")
        
        # Required fields
        required_fields = ['source', 'target', 'relationship']
        for field in required_fields:
            if field not in edge:
                raise ValidationError(f"Edge {index} missing required field: {field}")
        
        # Validate source and target
        source = str(edge['source']).strip()
        target = str(edge['target']).strip()
        
        if not source:
            raise ValidationError(f"Edge {index} source cannot be empty")
        if not target:
            raise ValidationError(f"Edge {index} target cannot be empty")
        
        if source not in valid_node_ids:
            raise ValidationError(f"Edge {index} source node ID not found: {source}")
        if target not in valid_node_ids:
            raise ValidationError(f"Edge {index} target node ID not found: {target}")
        
        if source == target:
            raise ValidationError(f"Edge {index} cannot connect a node to itself")
        
        # Validate relationship
        relationship = str(edge['relationship']).strip()
        if not relationship:
            raise ValidationError(f"Edge {index} relationship cannot be empty")
        if len(relationship) > 100:
            raise ValidationError(f"Edge {index} relationship too long (max 100 characters)")
        
        return {
            'source': source,
            'target': target,
            'relationship': relationship
        }
    
    @classmethod
    def validate_json_response(cls, response_text: str) -> Dict[str, Any]:
        """
        Validate and parse JSON response from LLM
        
        Args:
            response_text: Raw response text from LLM
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValidationError: If JSON is invalid
        """
        if not response_text or not response_text.strip():
            raise ValidationError("Empty response from LLM")
        
        # Try to parse as JSON directly
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from text using regex
        json_patterns = [
            r'\{.*\}',  # Simple object
            r'\{[\s\S]*\}',  # Object with newlines
            r'```json\s*(\{[\s\S]*?\})\s*```',  # JSON in code block
            r'```\s*(\{[\s\S]*?\})\s*```',  # JSON in generic code block
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        raise ValidationError("Could not extract valid JSON from LLM response")


class APIValidator:
    """Validates API inputs and parameters"""
    
    @classmethod
    def validate_document_id(cls, document_id: Any) -> int:
        """
        Validate document ID parameter
        
        Args:
            document_id: The document ID to validate
            
        Returns:
            Validated document ID as integer
            
        Raises:
            ValidationError: If document ID is invalid
        """
        try:
            doc_id = int(document_id)
            if doc_id <= 0:
                raise ValidationError("Document ID must be a positive integer")
            return doc_id
        except (ValueError, TypeError):
            raise ValidationError("Document ID must be a valid integer")
    
    @classmethod
    def validate_version_number(cls, version_number: Any) -> int:
        """
        Validate version number parameter
        
        Args:
            version_number: The version number to validate
            
        Returns:
            Validated version number as integer
            
        Raises:
            ValidationError: If version number is invalid
        """
        try:
            version = int(version_number)
            if version <= 0:
                raise ValidationError("Version number must be a positive integer")
            return version
        except (ValueError, TypeError):
            raise ValidationError("Version number must be a valid integer")
    
    @classmethod
    def validate_text_content(cls, text: str) -> str:
        """
        Validate text content
        
        Args:
            text: The text content to validate
            
        Returns:
            Validated text content
            
        Raises:
            ValidationError: If text content is invalid
        """
        if not text or not text.strip():
            raise ValidationError("Text content cannot be empty")
        
        # Check for reasonable length
        if len(text) > 1000000:  # 1MB of text
            raise ValidationError("Text content too long (maximum 1MB)")
        
        return text.strip()


def validate_file_upload(file, filename: str) -> Tuple[str, str]:
    """
    Comprehensive file upload validation
    
    Args:
        file: The uploaded file object
        filename: The filename
        
    Returns:
        Tuple of (validated_filename, validated_extension)
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Validate filename
        safe_filename = FileValidator.validate_filename(filename)
        
        # Validate file extension
        file_ext = FileValidator.validate_file_extension(safe_filename)
        
        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        FileValidator.validate_file_size(file_size)
        
        return safe_filename, file_ext
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File validation error: {str(e)}")


def validate_knowledge_graph_response(response_text: str) -> Dict[str, Any]:
    """
    Validate knowledge graph response from LLM
    
    Args:
        response_text: Raw response from LLM
        
    Returns:
        Validated knowledge graph data
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Parse JSON
        graph_data = DataValidator.validate_json_response(response_text)
        
        # Validate structure
        validated_graph = DataValidator.validate_knowledge_graph(graph_data)
        
        return validated_graph
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Graph validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Graph parsing error: {str(e)}")