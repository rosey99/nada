"""Global pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path

# Ensure the project root is on the path so imports work
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
