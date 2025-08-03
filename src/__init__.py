"""
Turbo Air Equipment Viewer - Core Package
Minimal imports to prevent circular dependency errors
"""

# Only import core configuration and exceptions that don't have dependencies
try:
    from .config import Config, init_session_state, AppError, DatabaseError, AuthError, SyncError
except ImportError:
    # Fallback if config module has issues
    pass

# Don't import UI, pages, or other modules that might have circular dependencies
# Let individual modules import what they need directly

__version__ = "1.0.0"
__author__ = "Turbo Air Team"

# Minimal exports - only core config items
__all__ = [
    'Config', 
    'init_session_state', 
    'AppError', 
    'DatabaseError', 
    'AuthError', 
    'SyncError'
]