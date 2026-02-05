"""Accounting module - Financial tracking and reporting"""
from app.accounting.router import router
from app.accounting.service import AccountingService

__all__ = ["router", "AccountingService"]
