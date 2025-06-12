import json
import redis
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.database import redis_client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class FraudRedisService:
    """Redis service for fraud detection operations"""
    
    def __init__(self):
        self.redis = redis_client
        self.default_expiry = 3600  # 1 hour default TTL
    
    # ================================
    # User Behavior Tracking
    # ================================
    
    def track_user_transaction(self, user_id: str, transaction_data: Dict[str, Any]):
        """Track recent user transactions for pattern analysis"""
        key = f"user:transactions:{user_id}"
        
        # Add transaction to list (keep last 50)
        transaction_json = json.dumps({
            **transaction_data,
            "timestamp": datetime.now().isoformat()
        })
        
        pipe = self.redis.pipeline()
        pipe.lpush(key, transaction_json)
        pipe.ltrim(key, 0, 49)  # Keep only last 50 transactions
        pipe.expire(key, 86400 * 7)  # Expire after 7 days
        pipe.execute()
    
    def get_user_recent_transactions(self, user_id: str, count: int = 10) -> List[Dict]:
        """Get user's recent transactions"""
        key = f"user:transactions:{user_id}"
        transactions = self.redis.lrange(key, 0, count - 1)
        return [json.loads(tx) for tx in transactions]
    
    def track_failed_attempt(self, user_id: str):
        """Track failed payment attempts"""
        key = f"user:failed_attempts:{user_id}"
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 3600)  # Reset every hour
        pipe.execute()
    
    def get_failed_attempts(self, user_id: str) -> int:
        """Get failed attempts count"""
        key = f"user:failed_attempts:{user_id}"
        count = self.redis.get(key)
        return int(count) if count else 0
    
    # ================================
    # Rate Limiting
    # ================================
    
    def is_rate_limited(self, identifier: str, limit: int, window_seconds: int) -> bool:
        """Check if identifier is rate limited"""
        key = f"rate_limit:{identifier}"
        current = self.redis.get(key)
        
        if current is None:
            # First request
            pipe = self.redis.pipeline()
            pipe.set(key, 1)
            pipe.expire(key, window_seconds)
            pipe.execute()
            return False
        
        if int(current) >= limit:
            return True
        
        # Increment counter
        self.redis.incr(key)
        return False
    
    # ================================
    # Risk Scoring Cache
    # ================================
    
    def cache_user_risk_score(self, user_id: str, risk_score: float, ttl: int = 1800):
        """Cache user risk score (30 min default)"""
        key = f"risk_score:{user_id}"
        self.redis.setex(key, ttl, risk_score)
    
    def get_cached_risk_score(self, user_id: str) -> Optional[float]:
        """Get cached risk score"""
        key = f"risk_score:{user_id}"
        score = self.redis.get(key)
        return float(score) if score else None
    
    # ================================
    # Suspicious Activity Flags
    # ================================
    
    def flag_suspicious_user(self, user_id: str, reason: str, duration_hours: int = 24):
        """Flag user as suspicious"""
        key = f"suspicious:{user_id}"
        data = {
            "reason": reason,
            "flagged_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        }
        self.redis.setex(key, duration_hours * 3600, json.dumps(data))
        logger.warning(f"User {user_id} flagged as suspicious: {reason}")
    
    def is_user_suspicious(self, user_id: str) -> tuple[bool, Optional[str]]:
        """Check if user is flagged as suspicious"""
        key = f"suspicious:{user_id}"
        data = self.redis.get(key)
        if data:
            flag_info = json.loads(data)
            return True, flag_info["reason"]
        return False, None
    
    def unflag_user(self, user_id: str):
        """Remove suspicious flag"""
        key = f"suspicious:{user_id}"
        self.redis.delete(key)
    
    # ================================
    # Pattern Detection Cache
    # ================================
    
    def cache_pattern_analysis(self, pattern_key: str, analysis_result: Dict, ttl: int = 3600):
        """Cache pattern analysis results"""
        key = f"pattern:{pattern_key}"
        self.redis.setex(key, ttl, json.dumps(analysis_result))
    
    def get_cached_pattern(self, pattern_key: str) -> Optional[Dict]:
        """Get cached pattern analysis"""
        key = f"pattern:{pattern_key}"
        result = self.redis.get(key)
        return json.loads(result) if result else None
    
    # ================================
    # Event Queue Management
    # ================================
    
    def queue_for_ml_analysis(self, transaction_data: Dict):
        """Queue transaction for ML analysis"""
        queue_key = "ml_analysis_queue"
        self.redis.lpush(queue_key, json.dumps(transaction_data))
    
    def get_queued_transactions(self, batch_size: int = 10) -> List[Dict]:
        """Get transactions from ML analysis queue"""
        queue_key = "ml_analysis_queue"
        transactions = []
        for _ in range(batch_size):
            item = self.redis.rpop(queue_key)
            if not item:
                break
            transactions.append(json.loads(item))
        return transactions
    
    # ================================
    # Session Management
    # ================================
    
    def store_session_risk(self, session_id: str, risk_data: Dict, ttl: int = 3600):
        """Store session-based risk data"""
        key = f"session:risk:{session_id}"
        self.redis.setex(key, ttl, json.dumps(risk_data))
    
    def get_session_risk(self, session_id: str) -> Optional[Dict]:
        """Get session risk data"""
        key = f"session:risk:{session_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

# Initialize service
fraud_redis = FraudRedisService() 