"""
Middleware package for Locrit Backend
"""

from backend.middleware.auth import login_required

__all__ = ['login_required']