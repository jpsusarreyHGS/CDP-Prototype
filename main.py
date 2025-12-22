"""FastAPI entry point for the data inventory aggregation service."""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from routers.inventory_aggregator import router as inventory_router

app = FastAPI(title="Customer Data Platform Inventory API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory_router, prefix="/inventory")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Provide clearer error messages for JSON parsing errors."""
    import logging
    logger = logging.getLogger(__name__)
    
    errors = exc.errors()
    
    # Try to log the raw request body for debugging
    try:
        body = await request.body()
        body_str = body.decode('utf-8', errors='replace')
        logger.error(f"JSON parsing error. Request body (first 500 chars): {body_str[:500]}")
        logger.error(f"Request body length: {len(body_str)}")
        # Log around the error location if available
        for error in errors:
            if error.get("type") == "json_invalid":
                ctx = error.get("ctx", {})
                error_msg = ctx.get("error", "")
                loc = error.get("loc", [])
                if "body" in loc and len(loc) > 1:
                    pos = loc[1] if isinstance(loc[1], int) else None
                    if pos:
                        start = max(0, pos - 50)
                        end = min(len(body_str), pos + 50)
                        logger.error(f"Error at position {pos}: ...{body_str[start:end]}...")
    except Exception as e:
        logger.error(f"Could not read request body for debugging: {e}")
    
    for error in errors:
        if error.get("type") == "json_invalid":
            # Provide helpful message for JSON parsing errors
            ctx = error.get("ctx", {})
            error_msg = ctx.get("error", "")
            loc = error.get("loc", [])
            
            if "control character" in error_msg.lower():
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "detail": "Invalid JSON format: Control characters (like newlines) must be escaped. "
                                 "In your private_key field, ensure all newlines are escaped as \\n (backslash + n), "
                                 "not actual line breaks. The private key should be a single line string with \\n for newlines.",
                        "error_type": "json_parse_error",
                        "location": list(loc),
                        "suggestion": "Format your private_key like: \"-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\""
                    }
                )
            elif "Expecting value" in error_msg:
                return JSONResponse(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    content={
                        "detail": f"Invalid JSON format: {error_msg}. The request body contains malformed JSON. "
                                 "This could be caused by: 1) Missing quotes around string values, 2) Trailing commas, "
                                 "3) Special characters that aren't escaped, or 4) Empty values where a value is expected.",
                        "error_type": "json_parse_error",
                        "location": list(loc),
                        "error_message": error_msg
                    }
                )
    
    # Return default validation error
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors}
    )


@app.get("/")
async def root():
    return {"message": "Platform Inventory API"}

