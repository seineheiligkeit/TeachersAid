"""Run the dashboard:  python -m teachersaid   (then open http://127.0.0.1:8000)."""

from __future__ import annotations

import os

import uvicorn

if __name__ == "__main__":
    host = os.environ.get("TEACHERSAID_HOST", "127.0.0.1")
    port = int(os.environ.get("TEACHERSAID_PORT", "8000"))
    uvicorn.run("teachersaid.api.app:app", host=host, port=port, reload=False)
