"""
Security module for AI-Powered Knowledge Graph Builder
Handles file upload security, path validation, and access control.
"""

import os
import hashlib
import magic
from pathlib import Path
from typing import Optional, Tuple
import logging

from config import settings

logger = logging.getLogger(__name__)


class SecurityManager:
    """Handles security-related operations"""
    
    # Allowed MIME types for each file extension
    ALLOWED_MIME_TYPES = {
        '.pdf': ['application/pdf'],
        '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        '.txt': ['text/plain', 'text/plain; charset=utf-8'],
        '.csv': ['text/csv', 'text/plain']
    }
    
    # Maximum file size (in bytes)
    MAX_FILE_SIZE = settings.MAX_FILE_SIZE
    
    # Dangerous file extensions that should never be allowed
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.php', '.asp', '.jsp', '.py', '.rb', '.pl', '.sh', '.ps1', '.psm1',
        '.dll', '.so', '.dylib', '.bin', '.app', '.deb', '.rpm', '.msi'
    }
    
    @classmethod
    def ensure_upload_directory(cls) -> str:
        """
        Ensure upload directory exists and is properly configured
        
        Returns:
            Path to the upload directory
            
        Raises:
            OSError: If directory cannot be created or configured
        """
        upload_dir = Path(settings.UPLOAD_DIR)
        
        try:
            # Create directory if it doesn't exist
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Set proper permissions (read/write for owner, read for group/others)
            os.chmod(upload_dir, 0o755)
            
            # Verify directory is writable
            test_file = upload_dir / '.test_write'
            try:
                test_file.write_text('test')
                test_file.unlink()
            except Exception as e:
                raise OSError(f"Upload directory is not writable: {e}")
            
            logger.info(f"Upload directory ensured: {upload_dir.absolute()}")
            return str(upload_dir.absolute())
            
        except Exception as e:
            logger.error(f"Failed to ensure upload directory: {e}")
            raise OSError(f"Cannot create or configure upload directory: {e}")
    
    @classmethod
    def validate_file_security(cls, file_path: str, file_content: bytes) -> Tuple[bool, str]:
        """
        Comprehensive file security validation
        
        Args:
            file_path: Path to the file
            file_content: File content as bytes
            
        Returns:
            Tuple of (is_safe, reason)
        """
        try:
            # Check file size
            if len(file_content) > cls.MAX_FILE_SIZE:
                return False, f"File too large: {len(file_content)} bytes (max: {cls.MAX_FILE_SIZE})"
            
            if len(file_content) == 0:
                return False, "Empty file"
            
            # Get file extension
            file_ext = Path(file_path).suffix.lower()
            
            # Check for dangerous extensions
            if file_ext in cls.DANGEROUS_EXTENSIONS:
                return False, f"Dangerous file extension: {file_ext}"
            
            # Validate MIME type
            try:
                mime_type = magic.from_buffer(file_content, mime=True)
                allowed_types = cls.ALLOWED_MIME_TYPES.get(file_ext, [])
                
                if allowed_types and mime_type not in allowed_types:
                    return False, f"Invalid MIME type: {mime_type} for extension {file_ext}"
                    
            except Exception as e:
                logger.warning(f"Could not determine MIME type: {e}")
                # Continue without MIME validation if magic is not available
            
            # Check for suspicious content patterns
            if cls._contains_suspicious_content(file_content):
                return False, "File contains suspicious content patterns"
            
            # Check for embedded scripts or executables
            if cls._contains_embedded_executables(file_content):
                return False, "File contains embedded executables or scripts"
            
            return True, "File is safe"
            
        except Exception as e:
            logger.error(f"File security validation error: {e}")
            return False, f"Security validation error: {e}"
    
    @classmethod
    def _contains_suspicious_content(cls, content: bytes) -> bool:
        """
        Check for suspicious content patterns
        
        Args:
            content: File content as bytes
            
        Returns:
            True if suspicious content is found
        """
        # Convert to string for pattern matching
        try:
            text = content.decode('utf-8', errors='ignore').lower()
        except:
            text = str(content).lower()
        
        # Suspicious patterns
        suspicious_patterns = [
            r'<script[^>]*>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'vbscript:',  # VBScript URLs
            r'data:text/html',  # Data URLs with HTML
            r'<iframe[^>]*>',  # Iframe tags
            r'<object[^>]*>',  # Object tags
            r'<embed[^>]*>',  # Embed tags
            r'<form[^>]*>',  # Form tags
            r'<input[^>]*>',  # Input tags
            r'<link[^>]*>',  # Link tags
            r'<meta[^>]*>',  # Meta tags
            r'<style[^>]*>',  # Style tags
            r'<link[^>]*stylesheet',  # Stylesheet links
            r'@import',  # CSS imports
            r'expression\s*\(',  # CSS expressions
            r'url\s*\(',  # CSS URLs
            r'<[^>]*on\w+\s*=',  # Event handlers
            r'<[^>]*href\s*=',  # Href attributes
            r'<[^>]*src\s*=',  # Src attributes
        ]
        
        import re
        for pattern in suspicious_patterns:
            if re.search(pattern, text):
                logger.warning(f"Suspicious content pattern found: {pattern}")
                return True
        
        return False
    
    @classmethod
    def _contains_embedded_executables(cls, content: bytes) -> bool:
        """
        Check for embedded executables or scripts
        
        Args:
            content: File content as bytes
            
        Returns:
            True if embedded executables are found
        """
        # Check for common executable signatures
        executable_signatures = [
            b'MZ',  # PE executable
            b'\x7fELF',  # ELF executable
            b'\xfe\xed\xfa',  # Mach-O executable
            b'#!/bin/',  # Shell script
            b'#!/usr/bin/',  # Shell script
            b'#!/usr/local/bin/',  # Shell script
            b'<?php',  # PHP script
            b'<script',  # JavaScript
            b'<%@',  # ASP script
            b'<%',  # ASP script
        ]
        
        for signature in executable_signatures:
            if signature in content:
                logger.warning(f"Embedded executable signature found: {signature}")
                return True
        
        return False
    
    @classmethod
    def generate_safe_filename(cls, original_filename: str) -> str:
        """
        Generate a safe filename with collision avoidance
        
        Args:
            original_filename: Original filename
            
        Returns:
            Safe filename
        """
        # Get file extension
        path = Path(original_filename)
        name = path.stem
        ext = path.suffix.lower()
        
        # Sanitize name
        import re
        safe_name = re.sub(r'[^\w\-_\.]', '_', name)
        safe_name = re.sub(r'_+', '_', safe_name)  # Replace multiple underscores
        safe_name = safe_name.strip('_')
        
        if not safe_name:
            safe_name = 'file'
        
        # Limit length
        if len(safe_name) > 100:
            safe_name = safe_name[:100]
        
        # Generate unique filename
        base_filename = f"{safe_name}{ext}"
        counter = 1
        
        while True:
            if counter == 1:
                filename = base_filename
            else:
                name_part = safe_name
                if len(name_part) > 90:  # Leave room for counter
                    name_part = name_part[:90]
                filename = f"{name_part}_{counter}{ext}"
            
            # Check if file exists
            file_path = Path(settings.UPLOAD_DIR) / filename
            if not file_path.exists():
                return filename
            
            counter += 1
            if counter > 1000:  # Prevent infinite loop
                # Use hash-based naming as fallback
                import hashlib
                hash_suffix = hashlib.md5(original_filename.encode()).hexdigest()[:8]
                return f"{safe_name}_{hash_suffix}{ext}"
    
    @classmethod
    def validate_file_path(cls, file_path: str) -> bool:
        """
        Validate that file path is within allowed directory
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if path is safe
        """
        try:
            upload_dir = Path(settings.UPLOAD_DIR).resolve()
            file_path = Path(file_path).resolve()
            
            # Check if file is within upload directory
            return str(file_path).startswith(str(upload_dir))
            
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return False
    
    @classmethod
    def get_file_hash(cls, file_content: bytes) -> str:
        """
        Generate SHA-256 hash of file content
        
        Args:
            file_content: File content as bytes
            
        Returns:
            SHA-256 hash as hex string
        """
        return hashlib.sha256(file_content).hexdigest()
    
    @classmethod
    def scan_upload_directory(cls) -> dict:
        """
        Scan upload directory for security issues
        
        Returns:
            Dictionary with scan results
        """
        upload_dir = Path(settings.UPLOAD_DIR)
        
        if not upload_dir.exists():
            return {"error": "Upload directory does not exist"}
        
        results = {
            "total_files": 0,
            "suspicious_files": [],
            "large_files": [],
            "unknown_types": [],
            "errors": []
        }
        
        try:
            for file_path in upload_dir.rglob('*'):
                if file_path.is_file():
                    results["total_files"] += 1
                    
                    try:
                        # Check file size
                        file_size = file_path.stat().st_size
                        if file_size > cls.MAX_FILE_SIZE:
                            results["large_files"].append({
                                "path": str(file_path),
                                "size": file_size
                            })
                        
                        # Check file content
                        with open(file_path, 'rb') as f:
                            content = f.read(1024)  # Read first 1KB
                            
                        is_safe, reason = cls.validate_file_security(str(file_path), content)
                        if not is_safe:
                            results["suspicious_files"].append({
                                "path": str(file_path),
                                "reason": reason
                            })
                        
                        # Check file type
                        try:
                            mime_type = magic.from_file(str(file_path), mime=True)
                            ext = file_path.suffix.lower()
                            allowed_types = cls.ALLOWED_MIME_TYPES.get(ext, [])
                            
                            if allowed_types and mime_type not in allowed_types:
                                results["unknown_types"].append({
                                    "path": str(file_path),
                                    "mime_type": mime_type,
                                    "extension": ext
                                })
                        except:
                            pass  # Skip MIME type check if magic is not available
                            
                    except Exception as e:
                        results["errors"].append({
                            "path": str(file_path),
                            "error": str(e)
                        })
        
        except Exception as e:
            results["error"] = f"Directory scan failed: {e}"
        
        return results