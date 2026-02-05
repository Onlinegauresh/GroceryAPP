"""Shop models"""
from shared.models import Shop

# Re-export Shop model from shared.models
# This keeps the shop management logic in the shops module
__all__ = ["Shop"]
