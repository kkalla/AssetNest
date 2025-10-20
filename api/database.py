"""
Database module for AssetNest API.

This module has been refactored to use a modular architecture with
focused services and repositories while maintaining backward compatibility.
"""

import logging

# Import the new facade implementation
from .database_facade import DatabaseManager

# Configure logging
logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = ["DatabaseManager"]

# Import DatabaseManager module-level for direct access
DatabaseManager = DatabaseManager
