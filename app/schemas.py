from pydantic import BaseModel, validator, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

class PaymentStatus(str, Enum):
    INITIATED = "initiated"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTOCURRENCY = "cryptocurrency"
    BUY_NOW_PAY_LATER = "bnpl"

class DeviceInfo(BaseModel):
    device_id: Optional[str] = None
    device_type: Optional[str] = None  # mobile, desktop, tablet
    os: Optional[str] = None
    browser: Optional[str] = None
    user_agent: Optional[str] = None
    screen_resolution: Optional[str] = None

class LocationInfo(BaseModel):
    ip_address: str
    country: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None

class PaymentEvent(BaseModel):
    # Core payment info
    user_id: str = Field(..., min_length=1, max_length=50)
    transaction_id: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0, le=1000000)  # Max $1M
    currency: str = Field(default="USD", min_length=3, max_length=3)
    timestamp: datetime
    payment_method: PaymentMethod
    status: PaymentStatus
    
    # Merchant/Product info
    merchant_id: Optional[str] = Field(None, max_length=50)
    product_category: Optional[str] = Field(None, max_length=100)
    product_ids: Optional[List[str]] = Field(default_factory=list)
    
    # User behavior context
    session_id: Optional[str] = Field(None, max_length=100)
    device_info: Optional[DeviceInfo] = None
    location_info: Optional[LocationInfo] = None
    
    # Risk indicators
    is_first_time_user: Optional[bool] = False
    account_age_days: Optional[int] = Field(None, ge=0)
    previous_failed_attempts: Optional[int] = Field(default=0, ge=0)
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('currency')
    def validate_currency(cls, v):
        return v.upper()
    
    @validator('amount')
    def validate_amount(cls, v):
        return round(v, 2)  # Ensure 2 decimal places

class FraudDetectionResult(BaseModel):
    transaction_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    triggered_rules: List[str] = Field(default_factory=list)
    recommended_action: str  # APPROVE, REVIEW, BLOCK
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float
    timestamp: datetime

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database_status: str
    redis_status: str
