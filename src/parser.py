"""
Backward-compatibility shim.
GoFunction and GoParser are now in src/models.py and src/parsers/go_parser.py.
"""

from .models import CodeFunction as GoFunction  # noqa: F401
from .parsers.go_parser import GoParser  # noqa: F401
