"""
Error handling module for AI-Powered Knowledge Graph Builder
Provides centralized error handling, logging, and user-friendly error responses.
"""

import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors"""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(APIError):
    """Validation error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, details)


class NotFoundError(APIError):
    """Resource not found error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 404, details)


class ConflictError(APIError):
    """Resource conflict error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 409, details)


class ProcessingError(APIError):
    """Document processing error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 422, details)


class SecurityError(APIError):
    """Security-related error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 403, details)


class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def handle_validation_error(exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors"""
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.warning(f"Validation error: {errors}")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Invalid input data",
                "details": errors
            }
        )
    
    @staticmethod
    def handle_database_error(exc: SQLAlchemyError) -> JSONResponse:
        """Handle database errors"""
        error_type = type(exc).__name__
        
        if isinstance(exc, IntegrityError):
            # Handle constraint violations
            if "UNIQUE constraint failed" in str(exc):
                logger.warning(f"Unique constraint violation: {exc}")
                return JSONResponse(
                    status_code=409,
                    content={
                        "error": "Conflict",
                        "message": "Resource already exists",
                        "details": {"constraint": "unique"}
                    }
                )
            elif "FOREIGN KEY constraint failed" in str(exc):
                logger.warning(f"Foreign key constraint violation: {exc}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Invalid Reference",
                        "message": "Referenced resource does not exist",
                        "details": {"constraint": "foreign_key"}
                    }
                )
            else:
                logger.error(f"Integrity error: {exc}")
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Database Constraint Error",
                        "message": "Data violates database constraints",
                        "details": {"constraint": "integrity"}
                    }
                )
        else:
            logger.error(f"Database error ({error_type}): {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Database Error",
                    "message": "An error occurred while accessing the database",
                    "details": {"type": error_type}
                }
            )
    
    @staticmethod
    def handle_api_error(exc: APIError) -> JSONResponse:
        """Handle custom API errors"""
        logger.warning(f"API error: {exc.message}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @staticmethod
    def handle_generic_error(exc: Exception) -> JSONResponse:
        """Handle unexpected errors"""
        error_id = id(exc)  # Simple error ID for tracking
        
        logger.error(f"Unexpected error (ID: {error_id}): {exc}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "details": {
                    "error_id": str(error_id),
                    "type": type(exc).__name__
                }
            }
        )
    
    @staticmethod
    def handle_http_exception(exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions"""
        logger.warning(f"HTTP exception: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )


def create_error_response(
    message: str,
    status_code: int = 500,
    error_type: str = "Error",
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a standardized error response
    
    Args:
        message: Error message
        status_code: HTTP status code
        error_type: Type of error
        details: Additional error details
        
    Returns:
        JSONResponse with error information
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_type,
            "message": message,
            "details": details or {}
        }
    )


def log_error_context(request: Request, error: Exception, context: Dict[str, Any] = None):
    """
    Log error with request context
    
    Args:
        request: FastAPI request object
        error: The exception that occurred
        context: Additional context information
    """
    context = context or {}
    
    error_context = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "client": request.client.host if request.client else "unknown",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context
    }
    
    logger.error(f"Request error context: {error_context}")


class ErrorMiddleware:
    """Middleware for global error handling"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            # Log the error with context
            log_error_context(request, exc)
            
            # Handle different types of errors
            if isinstance(exc, APIError):
                response = ErrorHandler.handle_api_error(exc)
            elif isinstance(exc, SQLAlchemyError):
                response = ErrorHandler.handle_database_error(exc)
            elif isinstance(exc, HTTPException):
                response = ErrorHandler.handle_http_exception(exc)
            else:
                response = ErrorHandler.handle_generic_error(exc)
            
            await response(scope, receive, send)


# Common error messages
ERROR_MESSAGES = {
    "document_not_found": "Document not found",
    "version_not_found": "Version not found",
    "invalid_file_type": "Invalid file type",
    "file_too_large": "File too large",
    "processing_failed": "Document processing failed",
    "extraction_failed": "Knowledge graph extraction failed",
    "validation_failed": "Input validation failed",
    "security_violation": "Security policy violation",
    "database_error": "Database operation failed",
    "llm_error": "AI processing failed",
    "file_not_found": "File not found",
    "permission_denied": "Permission denied",
    "rate_limited": "Rate limit exceeded",
    "maintenance_mode": "Service temporarily unavailable"
}


def get_error_message(key: str, **kwargs) -> str:
    """
    Get formatted error message
    
    Args:
        key: Error message key
        **kwargs: Format parameters
        
    Returns:
        Formatted error message
    """
    message = ERROR_MESSAGES.get(key, "Unknown error")
    return message.format(**kwargs) if kwargs else message