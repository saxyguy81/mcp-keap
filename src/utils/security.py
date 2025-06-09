"""
Security utilities for Keap MCP service including rate limiting,
API key management, and security best practices.
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import os

from src.utils.logging_utils import get_security_logger


class SecurityLevel(Enum):
    """Security classification levels."""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_allowance: int = 10
    cooldown_period: int = 300  # 5 minutes


@dataclass
class SecurityEvent:
    """Security event for logging and monitoring."""
    event_type: str
    severity: SecurityLevel
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"


class RateLimiter:
    """Advanced rate limiter with multiple time windows and burst protection."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests: Dict[str, List[float]] = {}
        self.blocked_ips: Dict[str, float] = {}
        self.security_logger = get_security_logger()
        
    async def is_allowed(self, identifier: str, request_weight: int = 1) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limits.
        
        Args:
            identifier: Unique identifier (IP address, user ID, etc.)
            request_weight: Weight of the request (default 1)
            
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        current_time = time.time()
        
        # Check if IP is temporarily blocked
        if identifier in self.blocked_ips:
            if current_time < self.blocked_ips[identifier]:
                return False, {
                    "blocked": True,
                    "blocked_until": self.blocked_ips[identifier],
                    "reason": "Rate limit exceeded - temporary block"
                }
            else:
                # Unblock expired blocks
                del self.blocked_ips[identifier]
        
        # Initialize request history if not exists
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests outside all time windows
        self._cleanup_old_requests(identifier, current_time)
        
        # Check rate limits for different time windows
        minute_requests = self._count_requests_in_window(identifier, current_time, 60)
        hour_requests = self._count_requests_in_window(identifier, current_time, 3600)
        day_requests = self._count_requests_in_window(identifier, current_time, 86400)
        
        # Check limits
        rate_limit_info = {
            "requests_per_minute": {
                "current": minute_requests,
                "limit": self.config.requests_per_minute
            },
            "requests_per_hour": {
                "current": hour_requests,
                "limit": self.config.requests_per_hour
            },
            "requests_per_day": {
                "current": day_requests,
                "limit": self.config.requests_per_day
            }
        }
        
        # Check if any limit is exceeded
        if (minute_requests + request_weight > self.config.requests_per_minute or
            hour_requests + request_weight > self.config.requests_per_hour or
            day_requests + request_weight > self.config.requests_per_day):
            
            # Apply temporary block for repeated violations
            violation_count = self._get_recent_violations(identifier, current_time)
            if violation_count >= 3:  # 3 violations in recent period
                block_until = current_time + self.config.cooldown_period
                self.blocked_ips[identifier] = block_until
                
                self.security_logger.log_rate_limit_event(
                    user_id=identifier,
                    violation_count=violation_count,
                    blocked_until=block_until
                )
                
                rate_limit_info["blocked"] = True
                rate_limit_info["blocked_until"] = block_until
            
            return False, rate_limit_info
        
        # Allow request and record it
        for _ in range(request_weight):
            self.requests[identifier].append(current_time)
        
        return True, rate_limit_info
    
    def _cleanup_old_requests(self, identifier: str, current_time: float):
        """Remove requests older than 24 hours."""
        cutoff_time = current_time - 86400  # 24 hours
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]
    
    def _count_requests_in_window(self, identifier: str, current_time: float, window_seconds: int) -> int:
        """Count requests within a specific time window."""
        cutoff_time = current_time - window_seconds
        return len([
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ])
    
    def _get_recent_violations(self, identifier: str, current_time: float) -> int:
        """Count recent rate limit violations."""
        # This is a simplified implementation
        # In production, you'd want to track violations separately
        recent_requests = self._count_requests_in_window(identifier, current_time, 300)  # Last 5 minutes
        return max(0, recent_requests - self.config.requests_per_minute)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        current_time = time.time()
        
        return {
            "active_identifiers": len(self.requests),
            "blocked_identifiers": len(self.blocked_ips),
            "total_requests": sum(len(reqs) for reqs in self.requests.values()),
            "blocked_ips": {
                ip: {"blocked_until": block_time, "remaining_seconds": max(0, block_time - current_time)}
                for ip, block_time in self.blocked_ips.items()
            }
        }


class ApiKeyManager:
    """Secure API key management with rotation capabilities."""
    
    def __init__(self, key_file: Optional[str] = None):
        self.key_file = key_file or os.getenv("API_KEY_FILE", ".api_keys.json")
        self.keys: Dict[str, Dict[str, Any]] = {}
        self.security_logger = get_security_logger()
        self._load_keys()
    
    def _load_keys(self):
        """Load API keys from secure storage."""
        try:
            if os.path.exists(self.key_file):
                with open(self.key_file, 'r') as f:
                    self.keys = json.load(f)
        except Exception as e:
            self.security_logger.log_error_event(
                "api_key_load_error",
                f"Failed to load API keys: {str(e)}"
            )
    
    def _save_keys(self):
        """Save API keys to secure storage."""
        try:
            with open(self.key_file, 'w') as f:
                json.dump(self.keys, f, indent=2)
            
            # Set secure file permissions (read/write for owner only)
            os.chmod(self.key_file, 0o600)
            
        except Exception as e:
            self.security_logger.log_error_event(
                "api_key_save_error",
                f"Failed to save API keys: {str(e)}"
            )
    
    def generate_key(self, name: str, expires_days: int = 365) -> str:
        """Generate a new API key."""
        # Generate cryptographically secure random key
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        self.keys[key_hash] = {
            "name": name,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_used": None,
            "usage_count": 0,
            "active": True
        }
        
        self._save_keys()
        
        self.security_logger.log_authentication_event(
            "api_key_generated",
            True,
            user_id=name,
            key_expires=expires_at.isoformat()
        )
        
        return key
    
    def validate_key(self, key: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate an API key."""
        if not key:
            return False, None
        
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash not in self.keys:
            self.security_logger.log_authentication_event(
                "api_key_validation",
                False,
                error_details="Key not found"
            )
            return False, None
        
        key_info = self.keys[key_hash]
        
        # Check if key is active
        if not key_info.get("active", True):
            self.security_logger.log_authentication_event(
                "api_key_validation",
                False,
                user_id=key_info.get("name"),
                error_details="Key is inactive"
            )
            return False, None
        
        # Check expiration
        expires_at = datetime.fromisoformat(key_info["expires_at"])
        if datetime.utcnow() > expires_at:
            self.security_logger.log_authentication_event(
                "api_key_validation",
                False,
                user_id=key_info.get("name"),
                error_details="Key expired"
            )
            return False, None
        
        # Update usage tracking
        key_info["last_used"] = datetime.utcnow().isoformat()
        key_info["usage_count"] = key_info.get("usage_count", 0) + 1
        self._save_keys()
        
        self.security_logger.log_authentication_event(
            "api_key_validation",
            True,
            user_id=key_info.get("name")
        )
        
        return True, key_info
    
    def rotate_key(self, old_key: str, expires_days: int = 365) -> Optional[str]:
        """Rotate an existing API key."""
        old_key_hash = hashlib.sha256(old_key.encode()).hexdigest()
        
        if old_key_hash not in self.keys:
            return None
        
        old_key_info = self.keys[old_key_hash]
        name = old_key_info["name"]
        
        # Generate new key
        new_key = self.generate_key(f"{name}_rotated", expires_days)
        
        # Deactivate old key
        old_key_info["active"] = False
        old_key_info["rotated_at"] = datetime.utcnow().isoformat()
        
        self._save_keys()
        
        self.security_logger.log_authentication_event(
            "api_key_rotated",
            True,
            user_id=name
        )
        
        return new_key
    
    def revoke_key(self, key: str) -> bool:
        """Revoke an API key."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash not in self.keys:
            return False
        
        key_info = self.keys[key_hash]
        key_info["active"] = False
        key_info["revoked_at"] = datetime.utcnow().isoformat()
        
        self._save_keys()
        
        self.security_logger.log_authentication_event(
            "api_key_revoked",
            True,
            user_id=key_info.get("name")
        )
        
        return True
    
    def list_keys(self) -> List[Dict[str, Any]]:
        """List all API keys (without exposing the actual keys)."""
        return [
            {
                "name": info["name"],
                "created_at": info["created_at"],
                "expires_at": info["expires_at"],
                "last_used": info.get("last_used"),
                "usage_count": info.get("usage_count", 0),
                "active": info.get("active", True)
            }
            for info in self.keys.values()
        ]
    
    def cleanup_expired_keys(self):
        """Remove expired keys from storage."""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key_hash, key_info in self.keys.items():
            expires_at = datetime.fromisoformat(key_info["expires_at"])
            if current_time > expires_at:
                expired_keys.append(key_hash)
        
        for key_hash in expired_keys:
            del self.keys[key_hash]
        
        if expired_keys:
            self._save_keys()
            self.security_logger.log_authentication_event(
                "api_keys_cleanup",
                True,
                cleanup_count=len(expired_keys)
            )


class SecurityValidator:
    """Security validation utilities."""
    
    @staticmethod
    def validate_input(value: str, max_length: int = 1000, allowed_chars: Optional[str] = None) -> bool:
        """Validate input for potential security issues."""
        if not value or len(value) > max_length:
            return False
        
        # Check for basic injection patterns
        dangerous_patterns = [
            '<script', 'javascript:', 'data:', 'vbscript:',
            'on', 'eval(', 'exec(', 'system(', 'os.', 'subprocess',
            'import ', '__import__', 'input(', 'raw_input('
        ]
        
        value_lower = value.lower()
        for pattern in dangerous_patterns:
            if pattern in value_lower:
                return False
        
        # Check allowed characters if specified
        if allowed_chars and not all(c in allowed_chars for c in value):
            return False
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for security."""
        import re
        
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')
        
        # Keep only alphanumeric, dots, dashes, and underscores
        filename = re.sub(r'[^a-zA-Z0-9.\-_]', '', filename)
        
        # Limit length
        return filename[:255]
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure token."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
        """Hash password securely using PBKDF2."""
        import hashlib
        
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # Use PBKDF2 with 100,000 iterations
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return key.hex(), salt
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: bytes) -> bool:
        """Verify password against hash."""
        import hashlib
        
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(key.hex(), hashed)


class SecurityMiddleware:
    """Security middleware for request processing."""
    
    def __init__(self, rate_limiter: RateLimiter, api_key_manager: ApiKeyManager):
        self.rate_limiter = rate_limiter
        self.api_key_manager = api_key_manager
        self.security_logger = get_security_logger()
    
    async def process_request(self, request_info: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Process incoming request for security validation.
        
        Args:
            request_info: Dictionary containing request details
            
        Returns:
            Tuple of (allowed, security_info)
        """
        source_ip = request_info.get("source_ip", "unknown")
        api_key = request_info.get("api_key")
        endpoint = request_info.get("endpoint", "unknown")
        
        security_info = {
            "source_ip": source_ip,
            "endpoint": endpoint,
            "checks_passed": [],
            "checks_failed": [],
            "rate_limit_info": {}
        }
        
        # 1. Rate limiting check
        allowed, rate_limit_info = await self.rate_limiter.is_allowed(source_ip)
        security_info["rate_limit_info"] = rate_limit_info
        
        if not allowed:
            security_info["checks_failed"].append("rate_limit")
            self.security_logger.log_rate_limit_event(
                user_id=source_ip,
                endpoint=endpoint
            )
            return False, security_info
        
        security_info["checks_passed"].append("rate_limit")
        
        # 2. API key validation (if provided)
        if api_key:
            key_valid, key_info = self.api_key_manager.validate_key(api_key)
            if not key_valid:
                security_info["checks_failed"].append("api_key")
                return False, security_info
            
            security_info["checks_passed"].append("api_key")
            security_info["api_key_info"] = key_info
        
        # 3. Input validation
        if "payload" in request_info:
            payload = request_info["payload"]
            if isinstance(payload, str) and not SecurityValidator.validate_input(payload):
                security_info["checks_failed"].append("input_validation")
                return False, security_info
            
            security_info["checks_passed"].append("input_validation")
        
        # Log successful security validation
        self.security_logger.log_api_access(
            endpoint=endpoint,
            method=request_info.get("method", "UNKNOWN"),
            user_id=security_info.get("api_key_info", {}).get("name", source_ip)
        )
        
        return True, security_info


# Global security components
_rate_limiter: Optional[RateLimiter] = None
_api_key_manager: Optional[ApiKeyManager] = None
_security_middleware: Optional[SecurityMiddleware] = None


def get_rate_limiter(config: Optional[RateLimitConfig] = None) -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        if config is None:
            config = RateLimitConfig(
                requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
                requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
                requests_per_day=int(os.getenv("RATE_LIMIT_PER_DAY", "10000"))
            )
        _rate_limiter = RateLimiter(config)
    return _rate_limiter


def get_api_key_manager() -> ApiKeyManager:
    """Get global API key manager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = ApiKeyManager()
    return _api_key_manager


def get_security_middleware() -> SecurityMiddleware:
    """Get global security middleware instance."""
    global _security_middleware
    if _security_middleware is None:
        _security_middleware = SecurityMiddleware(
            get_rate_limiter(),
            get_api_key_manager()
        )
    return _security_middleware


async def cleanup_security_data():
    """Cleanup expired security data."""
    api_key_manager = get_api_key_manager()
    api_key_manager.cleanup_expired_keys()
    
    # Additional cleanup can be added here
    security_logger = get_security_logger()
    security_logger.log_authentication_event(
        "security_cleanup",
        True,
        cleanup_completed=True
    )