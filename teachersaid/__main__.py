"""TeachersAid CLI.

  python -m teachersaid          # run the dashboard (http://127.0.0.1:8000)
  python -m teachersaid seed     # seed the master-library examples into the review queue
"""

from __future__ import annotations

import os
import sys

import uvicorn

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "seed":
        from .library import seed_assets, seed_blocks, seed_library

        items = seed_library()
        print(f"Seeded {len(items)} master-library worksheet(s) into the review store:")
        for it in items:
            status = "ERROR: " + it.error if it.error else f"{it.status} (review)"
            print(f"  - {it.id}  {it.title}  — {status}")
        blocks = seed_blocks()
        print(f"\nHarvested {len(blocks)} blocks into the block library "
              f"({sum(1 for b in blocks if b.role=='task')} tasks, "
              f"{sum(1 for b in blocks if b.role=='info')} info) — status 'approved' "
              "(curated seed; composable into worksheets).")
        kit = seed_assets()
        print(f"\nSeeded {len(kit)} decorative kit asset(s) into the asset library "
              "(status 'in_review' — review them in the Abbildungen tab).")
        print("\nRun 'python -m teachersaid' and open the dashboard to review them.")
        sys.exit(0)

    host = os.environ.get("TEACHERSAID_HOST", "127.0.0.1")
    port = int(os.environ.get("TEACHERSAID_PORT", "8000"))
    uvicorn.run("teachersaid.api.app:app", host=host, port=port, reload=False)
