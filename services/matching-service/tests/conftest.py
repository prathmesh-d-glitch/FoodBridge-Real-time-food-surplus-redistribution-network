import os
import sys
from pathlib import Path

# Add matching-service root to sys.path so 'import app' works cleanly
service_dir = Path(__file__).resolve().parent.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))
