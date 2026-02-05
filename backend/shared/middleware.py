"""Common Pydantic schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = 1
    limit: int = 20

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "limit": 20
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    status_code: int


class SuccessResponse(BaseModel):
    """Standard success response"""
    message: str
    data: Optional[dict] = None
