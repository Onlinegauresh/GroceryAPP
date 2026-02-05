"""Authentication models - import User from shared models"""
# User model is defined in shared.models.User to avoid duplication
# This module is kept for organization purposes
from shared.models import User, RoleEnum

__all__ = ["User", "RoleEnum"]
