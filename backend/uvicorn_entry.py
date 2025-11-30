#!/usr/bin/env python3
"""
Uvicorn entry point for Atlas API server
"""
import uvicorn
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    uvicorn.run(
        "atlas_api.main:app",
        host="127.0.0.1",
        port=4100,
        reload=True,
        log_level="info"
    )
