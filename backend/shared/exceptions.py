"""Custom exceptions for the application"""
from fastapi import HTTPException, status


class CustomException(HTTPException):
    """Base custom exception"""

    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)


class UnauthorizedException(CustomException):
    """Raised when authentication fails"""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(CustomException):
    """Raised when user lacks permissions"""

    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundException(CustomException):
    """Raised when resource not found"""

    def __init__(self, detail: str = "Not found"):
        super().__init__(detail, status_code=status.HTTP_404_NOT_FOUND)


class ValidationException(CustomException):
    """Raised on validation errors"""

    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class ConflictException(CustomException):
    """Raised on resource conflicts (e.g., duplicate SKU)"""

    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_409_CONFLICT)
