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
        from .library import (
            seed_arrangements,
            seed_assets,
            seed_astronomy,
            seed_blocks,
            seed_datasets,
            seed_history,
            seed_library,
            seed_sachverhalte,
            seed_texts,
            seed_textsorten,
        )

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
        arrs = seed_arrangements()
        print(f"\nStaged {len(arrs)} Lernarrangement(s) into the arrangement store "
              f"({', '.join(a.id for a in arrs)} — review them in the Arrangements tab).")
        data = seed_datasets()
        print(f"\nStaged {len(data)} grounded-facts dataset(s) into the dataset store "
              f"({', '.join(d.id for d in data)} — review them in the Datensätze tab).")
        texts = seed_texts()
        print(f"\nStaged {len(texts)} annotated text(s) into the text store "
              f"({', '.join(t.id for t in texts)} — review them in the Texte tab).")
        hist = seed_history()
        print(f"\nStaged {len(hist)} History-Flagship (GPB Wiener Kongress) als Inhalt "
              f"({', '.join(h.id for h in hist)} — Provenienz im Blöcke-Panel prüfen).")
        svs = seed_sachverhalte()
        print(f"\nStaged {len(svs)} Sachverhalt(e) in den Sachverhalt-Store "
              f"({', '.join(s.id for s in svs)} — Fakten/Quellen im Sachverhalte-Tab prüfen).")
        txs = seed_textsorten()
        print(f"\nStaged {len(txs)} Textsorten-Scaffold(s) als Inhalt "
              f"({', '.join(t.title for t in txs)} — im Inhalte-Tab prüfen).")
        astro = seed_astronomy()
        print(f"\nStaged {len(astro)} Astronomie-Blätter (Sternkarten-Engine) als Inhalt "
              f"({', '.join(a.id for a in astro)} — Mondphasen [Kompetenz] + Sternenhimmel "
              "[Horizont], im Inhalte-Tab prüfen).")
        print("\nRun 'python -m teachersaid' and open the dashboard to review them.")
        sys.exit(0)

    host = os.environ.get("TEACHERSAID_HOST", "127.0.0.1")
    port = int(os.environ.get("TEACHERSAID_PORT", "8000"))
    uvicorn.run("teachersaid.api.app:app", host=host, port=port, reload=False)
