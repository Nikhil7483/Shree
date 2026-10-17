"""
Application Configuration Interface.
Re-exports application settings from app.core.config for unified access.
"""

from app.core.config import Settings, get_settings

__all__ = ["Settings", "get_settings"]
