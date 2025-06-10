from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
from datetime import datetime, timezone

from app.schemas import PaymentEvent, FraudDetectionResult, HealthCheck
from app.logger import logger
from app.config import settings

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Add middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*"]  # Configure for production
)

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version=settings.app_version,
        database_status="connected",  # TODO: Add actual DB check
        redis_status="connected"      # TODO: Add actual Redis check
    )

@app.post("/ingest-event", response_model=dict)
@limiter.limit(f"{settings.rate_limit_requests}/minute")
async def ingest_event(request: Request, event: PaymentEvent):
    """
    Ingest payment events for fraud detection analysis
    """
    start_time = time.time()
    
    try:
        logger.info(f"Received payment event: {event.transaction_id}")
        
        # TODO: Add event to database/queue for processing
        # TODO: Trigger fraud detection analysis
        # TODO: Return fraud detection results
        
        processing_time = (time.time() - start_time) * 1000
        
        # Placeholder response - replace with actual fraud detection
        return {
            "status": "received",
            "transaction_id": event.transaction_id,
            "processing_time_ms": processing_time,
            "message": "Event queued for fraud analysis"
        }
        
    except Exception as e:
        logger.error(f"Error processing event {event.transaction_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
