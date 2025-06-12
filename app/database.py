from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import redis
import asyncio
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy setup
engine = None
SessionLocal = None
Base = declarative_base()

# Redis connection
redis_client: Optional[redis.Redis] = None

def create_database_engine():
    """Create database engine based on configuration"""
    global engine, SessionLocal
    
    if settings.database_url.startswith("sqlite"):
        # SQLite configuration for development
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.debug
        )
    else:
        # PostgreSQL configuration for production
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=300,    # Recycle connections every 5 minutes
            echo=settings.debug
        )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info(f"Database engine created for: {settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url}")

def create_redis_connection():
    """Create Redis connection"""
    global redis_client
    
    try:
        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # Test connection
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        redis_client = None

def get_database_session():
    """Get database session"""
    if SessionLocal is None:
        create_database_engine()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def check_database_health() -> tuple[bool, str]:
    """Check database connectivity for health checks"""
    try:
        if engine is None:
            create_database_engine()
        
        with engine.connect() as connection:
            # Simple query to test connection
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            return True, "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False, f"error: {str(e)[:50]}"

async def check_redis_health() -> tuple[bool, str]:
    """Check Redis connectivity for health checks"""
    try:
        if redis_client is None:
            create_redis_connection()
        
        if redis_client:
            redis_client.ping()
            return True, "connected"
        else:
            return False, "not configured"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False, f"error: {str(e)[:50]}"

def initialize_database():
    """Initialize database connections"""
    logger.info("Initializing database connections...")
    create_database_engine()
    create_redis_connection()
    logger.info("Database initialization complete")

# Initialize on import
initialize_database() 