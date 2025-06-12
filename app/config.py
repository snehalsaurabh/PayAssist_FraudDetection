import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # project root
env_path = BASE_DIR / ".env"
load_dotenv(env_path, override=True)  

class Settings(BaseSettings):
    # Application Settings
    app_name: str = "Amazon PayAssist Fraud Detection"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Database Settings - Now properly configured for env vars
    database_url: str = Field(
        default="sqlite:///./fraud_detection.db",  # Fallback for development
        description="Database connection URL"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # Security Settings - Better secret key handling
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT tokens"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Fraud Detection Settings
    suspicious_amount_threshold: float = 10000.0
    max_failed_attempts_per_hour: int = 5
    max_transactions_per_minute: int = 10
    pattern_analysis_window_hours: int = 24
    
    # Time Windows for Pattern Detection
    daily_window_hours: int = 24
    weekly_window_hours: int = 168  # 7 days
    monthly_window_hours: int = 720  # 30 days
    
    # Fraud Scoring Thresholds
    low_risk_threshold: float = 0.3
    medium_risk_threshold: float = 0.6
    high_risk_threshold: float = 0.8
    
    # Monitoring & Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/fraud_detection.log"
    enable_metrics: bool = True
    
    # External Services
    notification_webhook_url: Optional[str] = None
    ml_model_endpoint: Optional[str] = None
    
    # Kafka Settings (for high-volume event streaming)
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "payment-events"
    enable_kafka: bool = False
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'mysql://', 'sqlite://', 'mysql+pymysql://')):
            raise ValueError('Invalid database URL')
        return v
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters long')
        return v
    
    model_config = {
        "env_file": env_path,        # absolute path → always found
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

settings = Settings()
