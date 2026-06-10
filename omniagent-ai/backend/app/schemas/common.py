from pydantic import BaseModel, field_validator, ConfigDict
from typing import List, Any, Optional
from datetime import datetime
import re


class OkResponse(BaseModel):
    ok: bool = True
    message: str = "ok"


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    limit: int
    offset: int


class SafeString(str):
    """String that validates for common injection attacks"""
    
    @staticmethod
    def validate(value: str, allow_special: bool = False) -> bool:
        """Validate string for safety"""
        if not isinstance(value, str):
            return False
        
        # Check length
        if len(value) > 10000:
            return False
        
        if not allow_special:
            # Block common SQL injection patterns
            dangerous_patterns = [
                r"(\bUNION\b|\bSELECT\b|\bDROP\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b)",
                r"(--|;|/\*|\*/|xp_|sp_)",
            ]
            for pattern in dangerous_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    return False
        
        return True


class PaginationParams(BaseModel):
    """Pagination parameters"""
    skip: int = 0
    limit: int = 50
    
    @field_validator('skip')
    @classmethod
    def validate_skip(cls, v):
        if v < 0:
            raise ValueError('skip must be >= 0')
        if v > 1000000:
            raise ValueError('skip must be <= 1000000')
        return v
    
    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v):
        if v < 1:
            raise ValueError('limit must be >= 1')
        if v > 1000:
            raise ValueError('limit must be <= 1000')
        return v


class SortParams(BaseModel):
    """Sort parameters"""
    sort_by: str = "created_at"
    sort_order: str = "desc"  # asc or desc
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v


class TimeRangeParams(BaseModel):
    """Time range parameters"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        if info.data.get('start_date') and v:
            if v < info.data['start_date']:
                raise ValueError('end_date must be after start_date')
        return v


class SearchParams(BaseModel):
    """Search parameters"""
    query: str
    limit: int = 20
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('query must be at least 2 characters')
        if len(v) > 500:
            raise ValueError('query must be less than 500 characters')
        if not SafeString.validate(v, allow_special=True):
            raise ValueError('query contains invalid characters')
        return v.strip()
    
    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v):
        if v < 1 or v > 500:
            raise ValueError('limit must be between 1 and 500')
        return v


class StatusResponse(BaseModel):
    """Generic status response"""
    status: str
    message: Optional[str] = None
    timestamp: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Error response format"""
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: Optional[datetime] = None