"""
Advanced error handlers and response models for MechaniAI API.
Provides comprehensive error handling with security and user experience in mind.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


# Error Response Models
class ValidationError(BaseModel):
    """Model for individual validation errors."""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: bool = Field(True, description="Always true for error responses")
    message: str = Field(..., description="Human-readable error message")
    error_code: str = Field(..., description="Machine-readable error code")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")


class ValidationErrorResponse(ErrorResponse):
    """Detailed validation error response."""
    validation_errors: List[ValidationError] = Field(..., description="List of validation errors")


class RateLimitErrorResponse(ErrorResponse):
    """Rate limit error response with retry information."""
    retry_after: int = Field(..., description="Seconds to wait before retrying")
    limit: int = Field(..., description="Request limit per time window")
    window: int = Field(..., description="Time window in seconds")


# Error Handler Functions
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors with detailed information.
    
    Args:
        request: FastAPI request object
        exc: Pydantic validation exception
        
    Returns:
        JSONResponse with detailed validation error information
    """
    validation_errors = []
    
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        validation_errors.append(ValidationError(
            field=field_path,
            message=error["msg"],
            code=error["type"]
        ))
    
    error_response = ValidationErrorResponse(
        message="Request validation failed",
        error_code="VALIDATION_ERROR",
        validation_errors=validation_errors,
        request_id=getattr(request.state, 'request_id', None)
    )
    
    logger.warning(f"Validation error: {validation_errors}")
    
    return JSONResponse(
        status_code=422,
        content=error_response.model_dump()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with consistent error format.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSONResponse with standardized error format
    """
    # Map HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED", 
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        408: "REQUEST_TIMEOUT",
        409: "CONFLICT",
        413: "PAYLOAD_TOO_LARGE",
        415: "UNSUPPORTED_MEDIA_TYPE",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = error_code_map.get(exc.status_code, "UNKNOWN_ERROR")
    
    # Special handling for rate limiting
    if exc.status_code == 429:
        error_response = RateLimitErrorResponse(
            message="Too many requests",
            error_code=error_code,
            retry_after=60,  # Default retry after 60 seconds
            limit=100,  # Default limit
            window=3600,  # Default window of 1 hour
            request_id=getattr(request.state, 'request_id', None)
        )
    else:
        error_response = ErrorResponse(
            message=exc.detail if isinstance(exc.detail, str) else "An error occurred",
            error_code=error_code,
            request_id=getattr(request.state, 'request_id', None)
        )
    
    logger.warning(f"HTTP {exc.status_code} error: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions with secure error responses.
    
    Args:
        request: FastAPI request object
        exc: General exception
        
    Returns:
        JSONResponse with secure error information
    """
    # Log the full exception for debugging
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Return generic error message (don't expose internal details)
    error_response = ErrorResponse(
        message="An internal server error occurred",
        error_code="INTERNAL_SERVER_ERROR",
        request_id=getattr(request.state, 'request_id', None)
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


# Security Headers Middleware
class SecurityHeadersMiddleware:
    """Middleware to add security headers to all responses."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # Add security headers
                security_headers = {
                    b"x-content-type-options": b"nosniff",
                    b"x-frame-options": b"DENY",
                    b"x-xss-protection": b"1; mode=block",
                    b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                    b"content-security-policy": b"default-src 'self'",
                    b"referrer-policy": b"strict-origin-when-cross-origin"
                }
                
                for header_name, header_value in security_headers.items():
                    if header_name not in headers:
                        headers[header_name] = header_value
                
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


# Request ID Middleware
class RequestIDMiddleware:
    """Middleware to add unique request IDs for tracking."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        import uuid
        request_id = str(uuid.uuid4())
        
        # Add request ID to scope for access in handlers
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["request_id"] = request_id
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[b"x-request-id"] = request_id.encode()
                message["headers"] = list(headers.items())
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


# Rate Limiting (Basic Implementation)
class SimpleRateLimiter:
    """Simple in-memory rate limiter for basic protection."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # {client_ip: [(timestamp, count), ...]}
        self.window_size = 60  # 1 minute
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed for the client IP."""
        current_time = time.time()
        
        # Clean old entries
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (timestamp, count) for timestamp, count in self.requests[client_ip]
                if current_time - timestamp < self.window_size
            ]
        
        # Count requests in current window
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        request_count = sum(count for _, count in self.requests[client_ip])
        
        if request_count >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[client_ip].append((current_time, 1))
        return True


# Rate Limiting Middleware
class RateLimitMiddleware:
    """Middleware for basic rate limiting."""
    
    def __init__(self, app, rate_limiter: SimpleRateLimiter):
        self.app = app
        self.rate_limiter = rate_limiter
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Get client IP
        client_ip = scope.get("client", ["unknown", None])[0]
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(client_ip):
            # Send rate limit error
            response = JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "message": "Too many requests",
                    "error_code": "RATE_LIMITED",
                    "retry_after": 60
                }
            )
            await response(scope, receive, send)
            return
        
        await self.app(scope, receive, send) 