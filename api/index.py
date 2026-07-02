import sys
import os

# Add the project root to python path so backend.api and others can be imported
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import the FastAPI application instance
from backend.api import app
