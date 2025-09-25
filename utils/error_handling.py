"""
Enhanced error handling utilities for the RAG system.
Provides centralized error handling, custom exceptions, and error responses.
"""

import traceback
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog
from utils.middleware import logger

class ErrorCode:
    """Error code constants"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    DATABASE_ERROR = "DATABASE_ERROR"
    API_ERROR = "API_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class RAGException(Exception):
    """Base exception for RAG system"""
    
    def __init__(
        self,
        message: str,
        error_code: str = ErrorCode.INTERNAL_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(RAGException):
    """Validation error"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class FileTooLargeError(RAGException):
    """File too large error"""
    
    def __init__(self, max_size: int, actual_size: int):
        super().__init__(
            message=f"File too large. Maximum size: {max_size} bytes, Actual size: {actual_size} bytes",
            error_code=ErrorCode.FILE_TOO_LARGE,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details={"max_size": max_size, "actual_size": actual_size}
        )


class InvalidFileTypeError(RAGException):
    """Invalid file type error"""
    
    def __init__(self, allowed_types: list, actual_type: str):
        super().__init__(
            message=f"Invalid file type. Allowed types: {allowed_types}, Actual type: {actual_type}",
            error_code=ErrorCode.INVALID_FILE_TYPE,
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            details={"allowed_types": allowed_types, "actual_type": actual_type}
        )


class FileNotFoundError(RAGException):
    """File not found error"""
    
    def __init__(self, filename: str):
        super().__init__(
            message=f"File not found: {filename}",
            error_code=ErrorCode.FILE_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details={"filename": filename}
        )


class DatabaseError(RAGException):
    """Database operation error"""
    
    def __init__(self, message: str, operation: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"operation": operation, **(details or {})}
        )


class APIError(RAGException):
    """External API error"""
    
    def __init__(self, message: str, api_service: str, status_code: int = status.HTTP_502_BAD_GATEWAY):
        super().__init__(
            message=message,
            error_code=ErrorCode.API_ERROR,
            status_code=status_code,
            details={"api_service": api_service}
        )


class ProcessingError(RAGException):
    """Document processing error"""
    
    def __init__(self, message: str, processing_step: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.PROCESSING_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"processing_step": processing_step, **(details or {})}
        )


class TimeoutError(RAGException):
    """Timeout error"""
    
    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            message=f"Operation timed out: {operation}",
            error_code=ErrorCode.TIMEOUT_ERROR,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            details={"operation": operation, "timeout_seconds": timeout_seconds}
        )


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


def create_error_response(
    error: RAGException,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create standardized error response"""
    logger.error(
        "Error occurred",
        error_code=error.error_code,
        message=error.message,
        status_code=error.status_code,
        details=error.details,
        request_id=request_id,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=error.status_code,
        content=ErrorResponse(
            error_code=error.error_code,
            message=error.message,
            details=error.details,
            request_id=request_id
        ).dict()
    )


def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation errors"""
    return create_error_response(
        ValidationError(str(exc)),
        getattr(request.state, 'request_id', None)
    )


def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    return create_error_response(
        RAGException(
            message=exc.detail,
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=exc.status_code
        ),
        getattr(request.state, 'request_id', None)
    )


def handle_rag_exception(request: Request, exc: RAGException) -> JSONResponse:
    """Handle RAG exceptions"""
    return create_error_response(
        exc,
        getattr(request.state, 'request_id', None)
    )


def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions"""
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        exc_info=True,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    return create_error_response(
        RAGException(
            message="An unexpected error occurred",
            error_code=ErrorCode.INTERNAL_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error_type": type(exc).__name__}
        ),
        getattr(request.state, 'request_id', None)
    )


def setup_exception_handlers(app):
    """Setup exception handlers for the FastAPI application"""
    from fastapi.exceptions import RequestValidationError
    
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(RAGException, handle_rag_exception)
    app.add_exception_handler(Exception, handle_generic_exception)


def log_and_raise_error(
    error_class: type,
    message: str,
    **kwargs
) -> None:
    """Log error and raise exception"""
    logger.error(
        "Raising error",
        error_class=error_class.__name__,
        message=message,
        **kwargs
    )
    raise error_class(message, **kwargs)


def safe_execute(func, *args, **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except RAGException:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error in safe_execute",
            function=func.__name__,
            error=str(e),
            exc_info=True
        )
        raise RAGException(
            message=f"Error in {func.__name__}: {str(e)}",
            error_code=ErrorCode.INTERNAL_ERROR
        )