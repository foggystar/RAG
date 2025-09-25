"""
Enhanced middleware for the RAG system.
Provides rate limiting, security, logging, and monitoring capabilities.
"""

import time
import json
import os
from functools import wraps
from typing import Optional, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import structlog
from config import server_settings, security_settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Rate limiting setup
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{server_settings.rate_limit_requests}/{server_settings.rate_limit_window}seconds"]
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'rag_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'rag_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'rag_active_connections',
    'Number of active connections'
)

PDF_UPLOADS = Counter(
    'rag_pdf_uploads_total',
    'Total PDF uploads',
    ['status']
)

QUERIES_PROCESSED = Counter(
    'rag_queries_processed_total',
    'Total queries processed',
    ['status']
)

ERROR_COUNT = Counter(
    'rag_errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)


class SecurityMiddleware:
    """Security middleware for file upload and path validation"""
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """Validate and sanitize filename"""
        if not filename:
            raise ValueError("Filename cannot be empty")
        
        if len(filename) > security_settings.max_filename_length:
            raise ValueError(f"Filename too long (max {security_settings.max_filename_length} characters)")
        
        # Check file extension
        if not any(filename.lower().endswith(ext) for ext in security_settings.allowed_extensions):
            raise ValueError(f"File type not allowed. Allowed types: {security_settings.allowed_extensions}")
        
        # Sanitize filename
        sanitized = []
        for char in filename:
            if char in security_settings.allowed_filename_chars:
                sanitized.append(char)
            else:
                sanitized.append('_')
        
        sanitized_filename = ''.join(sanitized)
        
        # Ensure filename is not empty after sanitization
        if not sanitized_filename or sanitized_filename.startswith('.'):
            import uuid
            sanitized_filename = f"{uuid.uuid4().hex}.pdf"
        
        return sanitized_filename
    
    @staticmethod
    def validate_file_path(file_path: str, base_dir: str) -> str:
        """Validate that file path is within allowed directory"""
        abs_file_path = os.path.abspath(file_path)
        abs_base_dir = os.path.abspath(base_dir)
        
        if not abs_file_path.startswith(abs_base_dir):
            raise ValueError(f"Invalid file path: {file_path}")
        
        return abs_file_path
    
    @staticmethod
    def validate_query_length(query: str) -> str:
        """Validate query length"""
        if len(query) > security_settings.max_query_length:
            raise ValueError(f"Query too long (max {security_settings.max_query_length} characters)")
        return query.strip()


class LoggingMiddleware:
    """Enhanced logging middleware"""
    
    @staticmethod
    async def log_request(request: Request, call_next):
        """Log HTTP requests with structured logging"""
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request start
        logger.info(
            "HTTP request started",
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log request completion
            logger.info(
                "HTTP request completed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=process_time,
                client_ip=client_ip
            )
            
            # Update metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                "HTTP request failed",
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time=process_time,
                client_ip=client_ip,
                exc_info=True
            )
            
            # Update error metrics
            ERROR_COUNT.labels(
                error_type=type(e).__name__,
                endpoint=request.url.path
            ).inc()
            
            raise


class MetricsMiddleware:
    """Prometheus metrics middleware"""
    
    @staticmethod
    async def metrics_request(request: Request, call_next):
        """Collect metrics for HTTP requests"""
        ACTIVE_CONNECTIONS.inc()
        try:
            response = await call_next(request)
            return response
        finally:
            ACTIVE_CONNECTIONS.dec()


def setup_middleware(app):
    """Setup all middleware for the FastAPI application"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=server_settings.cors_origins,
        allow_credentials=server_settings.cors_allow_credentials,
        allow_methods=server_settings.cors_allow_methods,
        allow_headers=server_settings.cors_allow_headers,
    )
    
    # Rate limiting exception handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Custom middleware order matters
    app.middleware("http")(MetricsMiddleware.metrics_request)
    app.middleware("http")(LoggingMiddleware.log_request)


def rate_limit(limit: str):
    """Rate limiting decorator for specific endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await limiter.limit(limit)(func)(*args, **kwargs)
        return wrapper
    return decorator


def log_function_call(func_name: str):
    """Decorator to log function calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.info("Function call started", function=func_name)
            try:
                result = await func(*args, **kwargs)
                logger.info("Function call completed", function=func_name)
                return result
            except Exception as e:
                logger.error("Function call failed", function=func_name, error=str(e), exc_info=True)
                raise
        return wrapper
    return decorator


def get_metrics() -> str:
    """Get Prometheus metrics"""
    return generate_latest().decode('utf-8')