"""Propose authored difficulty labels for SME vetting (roadmap C4 follow-up).

Deterministic, offline, no LLM. The C4 difficulty model found the block corpus carries
ZERO authored `difficulty` labels (every task block falls back to the cognitive-level
band), so the model is *not learnable* (`Documents/difficulty-model.md`). The fix is
upstream: authored labels. Authored difficulty is SME judgment — an agent must NOT
silently write labels into the corpus. This tool instead emits **proposals** (the house
authored-then-SME-vetted pattern): a review surface the SME edits/accepts, after which
`tools/apply_difficulty.py` writes only the accepted labels and `tools/fit_difficulty.py`
becomes genuinely evaluable.

It builds two proposal groups over the task-block corpus:

  * **cues** — every block whose COMPUTED band (`pipeline/difficulty_model`) disagrees
    with the operative (authored-or-cognitive-fallback) band by >=1 (the C4 review cues).
    Each carries an *individually authored* German rationale (read from the task prompt);
    for a handful the proposal deliberately CONFIRMS the cognitive anchor against the
    model's flag (a false-alarm call — honest two-way review).
  * **sample** — a stratified sample of non-cue blocks where an authored label is most
    informative: ranked by intrinsic nudge (the non-anchor surface signal), then spread
    across subjects, kinds, and bands. For every non-cue block the computed band already
    EQUALS the cognitive band (integer bands, 1-band threshold), so these proposals are
    genuine two-signal confirmations — an explicit confirmation is also information.

Each proposal defaults `accepted: null` so the SME can mark true/false or edit the band.

    python tools/propose_difficulty.py            # write runs/difficulty/{json,md}
    python tools/propose_difficulty.py --dry-run  # report the plan; write nothing
    python tools/propose_difficulty.py --force    # overwrite an existing proposals file
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))  # import the worktree's teachersaid, not a site egg-link

from teachersaid.pipeline import difficulty_model as dm  # noqa: E402
from teachersaid.pipeline.difficulty import effective_difficulty  # noqa: E402
from teachersaid.store.blockstore import BlockStore  # noqa: E402

PROPOSALS_VERSION = 1
OUT_DIR = REPO_ROOT / "runs" / "difficulty"
JSON_PATH = OUT_DIR / "difficulty_proposals.json"
MD_PATH = OUT_DIR / "difficulty_proposals.md"

# target size of the whole proposals set (cues + sample), within the 120-150 review budget
TARGET_TOTAL = 138
SAMPLE_SUBJECT_CAP = 8   # max sample proposals per subject (spread, not GWB/MAT domination)
SAMPLE_KIND_CAP = 10     # max sample proposals per task kind

# --- German surface vocabulary (for the templated sample rationales) ---------------------
_BAND_WORD = {1: "leicht (Reproduktion)", 2: "mittel (Transfer)", 3: "anspruchsvoll (Reflexion)"}
_LEVEL_DE = {
    "remember": "Erinnern", "understand": "Verstehen", "apply": "Anwenden",
    "analyze": "Analysieren", "evaluate": "Bewerten", "create": "Erschaffen",
}

# --- the 48 individually authored cue proposals (band, rationale) -------------------------
# Read from each task prompt. Where `band == cognitive fallback`, the proposal CONFIRMS the
# anchor against the model's flag (a deliberate false-alarm call). These are authored SME-
# style judgments over the frozen task surface — the SME vets every one via `accepted`.
CUE_PROPOSALS: dict[str, tuple[int, str]] = {
    # --- LEICHTER: the anchor reads higher than the scaffolded/closed surface ---
    "c0005.t5": (2, "Fairness-Reihung mit kurzer Begründung: das Werturteil ist in ein "
                    "geschlossenes Reihungsformat gefasst und eng geführt — eher Transfer "
                    "(Band 2) als offene Reflexion (Band 3). Grenzfall."),
    "c0009.t4": (2, "Bewegungstagebuch über fünf Tage: überwiegend Protokollieren mit knapper "
                    "Schlussreflexion; der reale Anspruch liegt bei Transfer (Band 2), nicht "
                    "bei offener Reflexion (Band 3)."),
    "c0170.t2": (1, "Ursache-Folge-Paare im Teich zuordnen: geschlossene Zuordnung vorgegebener "
                    "Elemente in der 1. Klasse — reproduktionsnah (Band 1) statt Transfer (Band 2)."),
    "c0172.t4": (1, "Körpermerkmal→Vorteil zuordnen: geschlossenes Wiedererkennen erlernter "
                    "Paare, geringe Textlast — Band 1 statt Band 2."),
    "c0196.t4": (1, "Bekannte Abfolge (Bienenbesuch→Frucht) reihen: Abruf einer gelernten "
                    "Reihenfolge — Reproduktion (Band 1)."),
    "c0011.t4": (2, "Aus vorgegebenen Aussagen das 'echte Argument' auswählen: geschlossenes "
                    "Erkennen eines Kriteriums — Transfer (Band 2), nicht offene Reflexion (Band 3)."),
    "c0050.t4": (1, "Gehörte Sätze Situationen zuordnen: rezeptives Wiedererkennen im "
                    "geschlossenen Format, sehr geringe Textlast — Band 1 statt Band 2."),
    "c0032.t1": (2, "CONFIRM: Trotz geschlossenem MC-Format verlangt das 'und warum' echtes "
                    "Anwenden des Angebot-Nachfrage-Mechanismus — Transfer (Band 2) ist "
                    "berechtigt; der Modell-Hinweis auf Band 1 greift zu kurz."),
    "c0034.t3": (2, "CONFIRM: Alltagsbeispiele den EU-Grundfreiheiten zuordnen heißt, abstrakte "
                    "Kategorien auf neue Fälle anzuwenden — echter Transfer (Band 2); das "
                    "geschlossene Format senkt den Anspruch nicht auf Band 1."),
    "c0081.t4": (2, "R/F zu Bevölkerungsdynamik entscheiden und je in einem Satz begründen: "
                    "eng geführte Beurteilung — Transfer (Band 2) statt offener Reflexion (Band 3)."),
    "c0082.t4": (2, "R/F zu Energie und Klimawandel mit Ein-Satz-Begründung: scaffolded, die "
                    "Beurteilung ist vorstrukturiert — Band 2 statt Band 3."),
    "c0109.t4": (2, "Maßnahmen aus einer Liste auswählen und kurz begründen: geschlossene "
                    "Auswahl mit knapper Begründung — Transfer (Band 2), nicht Reflexion (Band 3)."),
    "c0111.t4": (2, "R/F entscheiden und je kurz begründen: eng geführtes Beurteilungsformat "
                    "— Band 2 statt Band 3."),
    "c0112.t5": (2, "R/F entscheiden und kurz begründen: scaffolded — Transfer (Band 2) statt "
                    "offener Reflexion (Band 3)."),
    "c0145.t3": (2, "R/F mit Ein-Satz-Begründung: die Beurteilung ist eng geführt — Band 2 "
                    "statt Band 3."),
    "c0146.t2": (2, "Zutreffende Aussagen zur Globalisierung auswählen und begründen: "
                    "geschlossene Auswahl mit knapper Begründung — Transfer (Band 2), nicht "
                    "Reflexion (Band 3)."),
    "c0141.t5": (2, "R/F zu NS-System und Holocaust mit kurzer Begründung: inhaltlich schwer, "
                    "aber die Aufgabenoperation (entscheiden + knapp begründen) bleibt Transfer "
                    "(Band 2). Grenzfall wegen der inhaltlichen Tiefe."),
    "c0142.t5": (2, "Diskutierte Erklärungen zum Zerfall der UdSSR ankreuzen und begründen: "
                    "geschlossene Auswahl mit kurzer Begründung — Band 2 statt Band 3."),
    "c0144.t5": (2, "R/F entscheiden und in einem Satz begründen: eng geführtes Format — "
                    "Transfer (Band 2) statt Reflexion (Band 3)."),
    "c0060.t5": (2, "CONFIRM: Lateinische Wörter zu korrekter Satzstellung ordnen und übersetzen "
                    "wendet Syntaxregeln an — echter Transfer (Band 2); trotz Reihungsformat "
                    "nicht auf Band 1 zu senken."),
    "c0062.t4": (1, "Lateinvokabel↔deutsche Bedeutung verbinden: im Kern Vokabelabruf (das "
                    "Erbwort-Suchen ist ein kleiner Zusatz) — reproduktionsnah (Band 1) statt "
                    "Transfer (Band 2)."),
    "c0063.t4": (2, "R/F zum Fortleben des Lateinischen mit kurzer Begründung: scaffolded — "
                    "Transfer (Band 2) statt Reflexion (Band 3)."),
    "c0086.t5": (2, "R/F zum Elektronengasmodell ankreuzen und kurz begründen: eng geführte "
                    "Beurteilung — Band 2 statt Band 3."),
    "phy-strahlung.str.t4": (2, "R/F entscheiden und begründen/korrigieren: vorstrukturiertes "
                    "Beurteilungsformat — Transfer (Band 2) statt offener Reflexion (Band 3)."),
    "c0055.t4": (1, "Fragen↔Antworten zuordnen (Hörtext): rezeptives Wiedererkennen, minimale "
                    "Textlast — Band 1 statt Band 2."),
    "c0056.t4": (1, "Unterstrichene Wörter ihrer deutschen Bedeutung zuordnen: Vokabelabruf im "
                    "geschlossenen Format — Reproduktion (Band 1)."),
    "c0057.t2": (1, "Possessivbegleiter (mon/ma/mes) einsetzen: weitgehend mechanische "
                    "Ein-Regel-Anwendung — reproduktionsnah (Band 1) statt Transfer (Band 2)."),
    "c0057.t4": (1, "Hobby↔französischer Satz verbinden: geschlossenes Wiedererkennen, minimale "
                    "Textlast — Band 1."),
    "c0059.t2": (2, "CONFIRM: Passé composé bilden verlangt Hilfsverbwahl (avoir/être) UND "
                    "Partizipangleichung — mehrschrittige Regelanwendung, echter Transfer "
                    "(Band 2); nicht auf Band 1 zu senken."),
    # --- SCHWERER: the open, prose-heavy surface reads higher than the anchor ---
    "c0195.t3": (3, "Drei Reinigungsverfahren anhand quantitativer Angaben vergleichen und "
                    "begründet auswählen: offene Datenauswertung mit hoher Textlast — "
                    "anspruchsvoll (Band 3), über der Einstufung als Transfer (Band 2)."),
    "c0010.t1": (2, "Sachtext lesen und analysieren in freier Schriftform: die offene "
                    "Textanalyse mit hoher Textlast liegt über bloßem Verstehen — Transfer (Band 2)."),
    "c0138.t2": (2, "Zeitleiste auswerten: Teile a/b sind Ablesen (reproduktiv), Teil c offene "
                    "Reflexion; der offene Schreibanteil hebt die Aufgabe knapp auf Transfer "
                    "(Band 2). Grenzfall — überwiegend Abruf."),
    "c0090.t4": (3, "Fallstudie Sahelzone eigenständig analysieren, sehr hohe Textlast, offene "
                    "Schriftform — anspruchsvoll (Band 3), über dem Transfer-Anchor (Band 2)."),
    "c0093.t3": (3, "Fallstudie Bankfiliale mehrteilig analysieren (betroffene Gruppen, Folgen): "
                    "offene Analyse — Band 3. Grenzfall wegen moderater Textlänge."),
    "c0094.t2": (2, "Bevölkerungspyramide lesen und Folgen für die Sozialversicherung frei "
                    "erklären: offene Deutung über bloßem Verstehen — Transfer (Band 2)."),
    "c0107.t2": (2, "Die drei stärksten Jahrgänge nennen und ihre Ursachen erklären: offene "
                    "Erklärung — Transfer (Band 2), nicht bloße Reproduktion."),
    "c0108.t2": (2, "Anteil der ≥75-Jährigen aus der Gesamtzahl berechnen und Rechenweg zeigen: "
                    "eine offene Rechenaufgabe — Transfer (Band 2), trotz Einstufung als Verstehen."),
    "c0112.t4": (3, "Erklären, warum Nigerias geringe Pro-Kopf-Emission bei hoher Betroffenheit "
                    "ein Gerechtigkeitsproblem ist: offene argumentative Analyse — "
                    "anspruchsvoll (Band 3)."),
    "c0118.t5": (3, "Fallstudie Hallstatt analysieren, sehr hohe Textlast, offene Schriftform — "
                    "Band 3, über dem Transfer-Anchor (Band 2)."),
    "c0147.t3": (3, "Zwei Grafiken (Empfehlung vs. Konsum) vergleichen und Abweichungen deuten: "
                    "offene Datenanalyse, hohe Textlast — anspruchsvoll (Band 3)."),
    "c0148.t4": (3, "Konsumhäufigkeiten vergleichen und soziale/sensorische Faktoren deuten: "
                    "offene Analyse, höchste Textlast — Band 3."),
    "c0151.t3": (2, "Authentische Seneca-Passage idiomatisch übersetzen: die Übersetzung eines "
                    "Originaltexts mit hoher Textlast ist Transfer (Band 2), nicht bloßes "
                    "Verstehen (Band 1)."),
    "c0140.t1": (2, "Einen zusammenhängenden Absatz über einen Beruf und KI schreiben: freie "
                    "Textproduktion in der L2 — Transfer (Band 2), über der Einstufung als Verstehen."),
    "c0181.t2": (1, "CONFIRM: 12,25 als gemischte Zahl schreiben und den Stellenwert in einem "
                    "Satz erklären: elementare Umwandlung der 1. Klasse; die kurze Erklärung "
                    "hebt sie nicht auf Transfer — Band 1 bestätigt, der Modell-Hinweis auf "
                    "Band 2 überschätzt das offene Format."),
    "c0189.t5": (3, "√9+√16 vs. √25 rechnerisch prüfen und daraus eine allgemeine Vorsicht bei "
                    "Wurzeln/Näherungen ableiten: offene Argumentation im irrationalen "
                    "Zahlenbereich — anspruchsvoll (Band 3)."),
    "c0197.t4": (2, "Beschreiben, wie Zylinder/Kegel durch Rotation entstehen, und die für die "
                    "Oberfläche nötigen Größen benennen: offene konzeptuelle Erklärung — "
                    "Transfer (Band 2)."),
    "c0123.t3": (3, "Bei ähnlicher Temperatur die Ursache des großen Niederschlagsunterschieds "
                    "begründet vermuten: offene, hypothesenbildende Analyse — anspruchsvoll (Band 3)."),
    "c0049.t2": (2, "Die Kraftübertragung am Fahrrad mit allen Fachbegriffen strukturiert "
                    "beschreiben: offene Erklärung mit sehr hoher Textlast — Transfer (Band 2), "
                    "über bloßem Verstehen."),
}


# --- corpus load -------------------------------------------------------------------------

def _prompt_excerpt(block, n: int = 90) -> str:
    raw = getattr(block, "prompt", None) or ""
    if isinstance(raw, list):
        raw = "".join(getattr(r, "text", "") for r in raw)
    text = " ".join(str(raw).split())  # collapse whitespace/newlines
    return text[: n - 1] + "…" if len(text) > n else text


def _load_rows() -> list[dict]:
    """Every task block → its estimate, effective band, features, intrinsic nudge."""
    bs = BlockStore()
    rows = []
    for lb in bs.list():
        est = dm.estimate(lb.block)
        if est is None:                       # info block → no difficulty
            continue
        eff = effective_difficulty(lb.block)
        authored = getattr(lb.block, "difficulty", None)
        intrinsic = round(sum(c for n, c in est.contributions.items() if n != "cog"), 4)
        rows.append({
            "lb": lb, "est": est, "eff": eff, "authored": authored,
            "intrinsic": intrinsic, "delta": est.band - eff,
        })
    return rows


# --- rationale for the (agreement) sample ------------------------------------------------

def _sample_rationale(row: dict) -> str:
    lb, est, eff = row["lb"], row["est"], row["eff"]
    level_de = _LEVEL_DE.get(lb.cognitive_level or "", lb.cognitive_level or "?")
    drivers = dm.top_drivers(est, k=2)
    band_word = _BAND_WORD[eff]
    if drivers:
        return (f"Oberflächenmerkmale ({', '.join(drivers)}) stützen die kognitive Einstufung "
                f"({level_de}) — {band_word} (Band {eff}) bestätigt.")
    return (f"Aufgabentyp und Antwortformat entsprechen der kognitiven Einstufung ({level_de}) "
            f"— {band_word} (Band {eff}) bestätigt.")


# --- sample selection: intrinsic-ranked, spread across subject/kind/band ------------------

def _select_sample(noncue: list[dict], want: int) -> list[dict]:
    """Stratified pick maximising informativeness (intrinsic nudge) while spreading across
    subjects, kinds, and bands. Phase A guarantees a subject×band floor; Phase B tops up by
    intrinsic under per-subject/per-kind caps. Deterministic (ties broken by block id)."""
    ordered = sorted(noncue, key=lambda r: (-r["intrinsic"], r["lb"].id))

    picked: list[dict] = []
    picked_ids: set[str] = set()
    per_subject: dict[str, int] = {}
    per_kind: dict[str, int] = {}

    def take(r: dict) -> None:
        picked.append(r)
        picked_ids.add(r["lb"].id)
        per_subject[r["lb"].subject] = per_subject.get(r["lb"].subject, 0) + 1
        per_kind[r["lb"].kind] = per_kind.get(r["lb"].kind, 0) + 1

    # Phase A — one block per (subject, effective band): the diversity floor.
    seen_cells: set[tuple[str, int]] = set()
    for r in ordered:
        cell = (r["lb"].subject, r["eff"])
        if cell not in seen_cells:
            seen_cells.add(cell)
            take(r)

    # Phase B — top up by intrinsic nudge under caps, until `want` is reached.
    for r in ordered:
        if len(picked) >= want:
            break
        if r["lb"].id in picked_ids:
            continue
        if per_subject.get(r["lb"].subject, 0) >= SAMPLE_SUBJECT_CAP:
            continue
        if per_kind.get(r["lb"].kind, 0) >= SAMPLE_KIND_CAP:
            continue
        take(r)

    return picked


# --- proposal records --------------------------------------------------------------------

def _proposal(row: dict, group: str) -> dict:
    lb, est, eff = row["lb"], row["est"], row["eff"]
    if group == "cue":
        if lb.id in CUE_PROPOSALS:
            proposed, rationale = CUE_PROPOSALS[lb.id]
        else:                                 # graceful default for any new cue
            proposed = est.band
            rationale = (f"Berechnete Einstufung ({_BAND_WORD[est.band]}) weicht vom "
                         f"Anchor ({_BAND_WORD[eff]}) ab; Oberflächenmerkmale: "
                         f"{', '.join(dm.top_drivers(est, k=2)) or '—'}.")
    else:
        proposed, rationale = eff, _sample_rationale(row)
    return {
        "block_id": lb.id,
        "group": group,
        "subject": lb.subject,
        "klasse": lb.klasse,
        "kind": lb.kind,
        "cognitive_level": lb.cognitive_level,
        "status": lb.status,
        "effective_band": eff,
        "effective_source": "authored" if row["authored"] is not None else "cognitive_fallback",
        "computed_band": est.band,
        "computed_score": est.score,
        "computed_drivers": dm.top_drivers(est, k=3),
        "intrinsic_nudge": row["intrinsic"],
        "direction": ("leichter" if row["delta"] < 0 else "schwerer") if group == "cue" else "einig",
        "proposed_difficulty": proposed,
        "agrees_with_fallback": proposed == eff,
        "prompt_excerpt": _prompt_excerpt(lb.block),
        "rationale_de": rationale,
        "accepted": None,   # SME sets true/false (or edits proposed_difficulty then true)
    }


def build_proposals(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    cues = [r for r in rows if abs(r["delta"]) >= 1]
    cues.sort(key=lambda r: (r["delta"], r["lb"].subject, r["lb"].id))
    noncue = [r for r in rows if abs(r["delta"]) < 1]
    want_sample = max(TARGET_TOTAL - len(cues), 0)
    sample = _select_sample(noncue, want_sample)
    sample.sort(key=lambda r: (r["lb"].subject, -r["intrinsic"], r["lb"].id))
    return ([_proposal(r, "cue") for r in cues],
            [_proposal(r, "sample") for r in sample])


# --- rendering ---------------------------------------------------------------------------

def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _md_table(props: list[dict]) -> list[str]:
    by_subject: dict[str, list[dict]] = {}
    for p in props:
        by_subject.setdefault(p["subject"], []).append(p)
    lines: list[str] = []
    for subject in sorted(by_subject):
        group = by_subject[subject]
        lines.append(f"#### {subject} ({len(group)})\n")
        lines.append("| Block | Kl | kogn. Stufe | Aufgabentyp | Eff→Ber | Vorschlag | "
                     "Aufgabe (Auszug) | Begründung |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for p in sorted(group, key=lambda x: x["block_id"]):
            arrow = f"{p['effective_band']}→{p['computed_band']}"
            flag = " *(bestätigt Anchor)*" if p["group"] == "cue" and p["agrees_with_fallback"] else ""
            lines.append(
                f"| `{p['block_id']}` | {p['klasse']} | {p['cognitive_level']} | {p['kind']} | "
                f"{arrow} | **{p['proposed_difficulty']}**{flag} | "
                f"{_md_escape(p['prompt_excerpt'])} | {_md_escape(p['rationale_de'])} |")
        lines.append("")
    return lines


def render_markdown(cues: list[dict], sample: list[dict], generated: str,
                    corpus_n: int) -> str:
    thresholds = dm._load_model()["thresholds"]
    diverge = sum(1 for p in cues if not p["agrees_with_fallback"])
    lower = sum(1 for p in cues if p["proposed_difficulty"] < p["effective_band"])
    higher = sum(1 for p in cues if p["proposed_difficulty"] > p["effective_band"])
    lines = [
        "# Difficulty-Label-Vorschläge (C4 → lernbares Modell)",
        "",
        f"*Version {PROPOSALS_VERSION} · erzeugt {generated} · {corpus_n} Aufgabenblöcke im "
        f"Korpus · Modell-Schwellen {thresholds}*",
        "",
        "## Arbeitsablauf (SME)",
        "",
        "1. Diese Tabelle durchsehen; die maschinenlesbare Fassung ist "
        "`difficulty_proposals.json` (identische Reihenfolge).",
        "2. Pro Vorschlag in der JSON `accepted` setzen: `true` übernimmt `proposed_difficulty`, "
        "`false` verwirft; bei Bedarf `proposed_difficulty` vorher editieren.",
        "3. `python tools/apply_difficulty.py runs/difficulty/difficulty_proposals.json` schreibt "
        "NUR die akzeptierten Labels in den Blockstore (Review-Status bleibt erhalten).",
        "4. `python tools/fit_difficulty.py` neu ausführen — mit authored Labels, die vom "
        "kognitiven Fallback abweichen, wird das Modell erstmals echt evaluierbar.",
        "",
        "Bis dahin ist nichts geschrieben: `difficulty` bleibt im Korpus überall `null`. "
        "Ein Vorschlag darf mit dem Fallback ÜBEREINSTIMMEN — eine bewusste Bestätigung ist "
        "ebenfalls Information; Divergenz wird nicht künstlich erzeugt.",
        "",
        "## Überblick",
        "",
        f"- **Cues** ({len(cues)}): berechnete Einstufung weicht ≥1 Band vom operativen Band ab "
        f"(die C4-Review-Cues). Davon {diverge} mit Vorschlag ≠ Fallback "
        f"({lower} niedriger, {higher} höher), {len(cues) - diverge} bestätigen den Anchor "
        f"trotz Modell-Flag (bewusste Fehlalarm-Einschätzung).",
        f"- **Sample** ({len(sample)}): Nicht-Cue-Blöcke mit dem größten intrinsischen Nudge, "
        f"gestreut über Fächer/Aufgabentypen/Bänder. Hier ist die berechnete Einstufung stets "
        f"gleich dem Anchor — beide Signale bestätigen einander.",
        f"- **Gesamt**: {len(cues) + len(sample)} Vorschläge.",
        "",
        "Bandskala: 1 = leicht (Reproduktion) · 2 = mittel (Transfer) · 3 = anspruchsvoll "
        "(Reflexion). Spalte **Eff→Ber** = operatives Band (kognitiver Fallback) → berechnetes "
        "Band; **Vorschlag** = vorgeschlagenes authored Label.",
        "",
        "## Cues",
        "",
    ]
    lines += _md_table(cues)
    lines += ["## Sample (informative Bestätigungen)", ""]
    lines += _md_table(sample)
    return "\n".join(lines).rstrip() + "\n"


def build_document(cues: list[dict], sample: list[dict], generated: str,
                   corpus_n: int) -> dict:
    return {
        "version": PROPOSALS_VERSION,
        "generated": generated,
        "corpus_blocks": corpus_n,
        "model_thresholds": dm._load_model()["thresholds"],
        "band_scale": {"1": "leicht (Reproduktion)", "2": "mittel (Transfer)",
                       "3": "anspruchsvoll (Reflexion)"},
        "counts": {
            "cues": len(cues),
            "sample": len(sample),
            "total": len(cues) + len(sample),
            "cues_diverging": sum(1 for p in cues if not p["agrees_with_fallback"]),
            "cues_proposed_lower": sum(1 for p in cues
                                       if p["proposed_difficulty"] < p["effective_band"]),
            "cues_proposed_higher": sum(1 for p in cues
                                        if p["proposed_difficulty"] > p["effective_band"]),
        },
        "note": "Authored-then-SME-vetted difficulty proposals. Set `accepted: true` to apply "
                "`proposed_difficulty` (edit it first if needed); then run "
                "tools/apply_difficulty.py, then tools/fit_difficulty.py. Nothing is written to "
                "the corpus until the SME runs the apply tool.",
        "proposals": cues + sample,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report the plan; write nothing")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing proposals file (else refuse, to protect SME edits)")
    args = ap.parse_args()

    rows = _load_rows()
    if not rows:
        print("no task blocks found in the corpus — nothing to propose", file=sys.stderr)
        sys.exit(1)
    cues, sample = build_proposals(rows)
    generated = date.today().isoformat()
    doc = build_document(cues, sample, generated, len(rows))

    c = doc["counts"]
    print(f"corpus: {len(rows)} task blocks")
    print(f"cues: {c['cues']}  (diverging {c['cues_diverging']}: "
          f"{c['cues_proposed_lower']} lower, {c['cues_proposed_higher']} higher)")
    print(f"sample: {c['sample']}   total proposals: {c['total']}")

    if args.dry_run:
        print("\n[dry-run] not writing", JSON_PATH.relative_to(REPO_ROOT))
        return
    if JSON_PATH.exists() and not args.force:
        print(f"\n{JSON_PATH.relative_to(REPO_ROOT)} exists — refusing to overwrite "
              f"(protects SME `accepted` edits). Pass --force to regenerate.", file=sys.stderr)
        sys.exit(2)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_PATH.write_text(render_markdown(cues, sample, generated, len(rows)), encoding="utf-8")
    print("\nwrote", JSON_PATH.relative_to(REPO_ROOT))
    print("wrote", MD_PATH.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
