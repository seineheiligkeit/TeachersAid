#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_oberstufe_meta.py — write lehrplan/oberstufe/_meta.json + subject_models.json.

The Oberstufe catalog (parse_lehrplan_oberstufe.py) supplies verbatim competences; this adds
the curated **judgment layer** the parser can't auto-detect: per-subject Handlungs-/Kompetenz-
dimensionen with stable codes + per-dimension modality, content axes, and task-kind extensions.
Mirrors lehrplan/subject_models.json (Unterstufe). Decision (SME, 28 Jun 2026): mirror the
Lehrplan's own dimensions, not the Reifeprüfung Grundkompetenzen-Katalog.

Re-runnable: reads the parsed catalog for the registry (klassen, kind counts, variants) and
**cross-checks** each curated dimension set against the catalog's descriptor groups (warns on a
mismatch — the SME fact-check hook). Edit CURATED below; re-run.

    python tools/build_oberstufe_meta.py
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "lehrplan" / "oberstufe"

FASSUNG = {
    "kurztitel": "Lehrplan der allgemeinbildenden höheren Schule (AHS)",
    "bgbl": "BGBl. II Nr. 204/2024", "stammfassung": "BGBl. Nr. 88/1985",
    "doknr": "NOR40264237", "valid_from": "2024-09-01", "valid_to": "2026-08-31",
}
UT_LEGEND = [
    "Bildungs-, Berufs- und Lebensorientierung", "Entrepreneurship Education",
    "Gesundheitsförderung", "Informatische Bildung", "Interkulturelle Bildung",
    "Medienbildung", "Politische Bildung",
    "Reflexive Geschlechterpädagogik und Gleichstellung", "Sexualpädagogik",
    "Sprachliche Bildung und Lesen", "Umweltbildung für nachhaltige Entwicklung",
    "Verkehrs- und Mobilitätsbildung", "Wirtschafts-, Finanz- und Verbraucher/innenbildung",
]

# Per-subject curated model. dims = [(code, label, modality)]; modality ∈ printable|oral|enactive|audio.
CURATED = {
    "PHY": {"dims": [("W", "Fachwissen anwenden", "printable"),
                     ("E", "Experimentieren und Erkenntnisgewinnung", "printable"),
                     ("S", "Standpunkte begründen und aus naturwissenschaftlicher Sicht bewerten", "printable")],
            "content_areas": None, "task_kinds": ["experiment_protocol", "source_critique"],
            "notes": "Naturwissenschaften W/E/S — same model as Unterstufe; Anforderungsniveaus 2 Stufen "
                     "(Reproduktion/Transfer · Reflexion/Problemlösung). Inhaltsbereiche per Semester; two "
                     "Lehrstoff variants (>7 / ≤7 Wochenstunden) tagged on each lehrstoff competence."},
    "CHE": {"dims": [("WO", "Wissen organisieren: Recherchieren, Darstellen, Kommunizieren", "printable"),
                     ("EG", "Erkenntnisse gewinnen: Fragen, Untersuchen, Interpretieren", "printable"),
                     ("KZ", "Konsequenzen ziehen: Bewerten, Entscheiden, Handeln", "printable")],
            "content_areas": ["Stoff-Teilchen", "Struktur-Eigenschafts", "Donator-Akzeptor",
                              "Energie", "Größen", "Gleichgewicht"],
            "task_kinds": ["experiment_protocol", "source_critique", "calculation"],
            "notes": "Chemie does NOT use W/E/S — dreidimensionales Modell: Handlungsdimension "
                     "(Wissen organisieren / Erkenntnisse gewinnen / Konsequenzen ziehen) + "
                     "Anforderungsdimension Niveau 1/2 + 6 Basiskonzepte (content_areas)."},
    "BIO": {"dims": [("W", "Fachwissen aneignen und kommunizieren", "printable"),
                     ("E", "Erkenntnisse gewinnen", "printable"),
                     ("S", "Standpunkte begründen und reflektiert handeln", "printable")],
            "content_areas": ["Struktur und Funktion", "Reproduktion", "Kompartimentierung",
                              "Steuerung und Regelung", "Stoff- und Energieumwandlung",
                              "Information und Kommunikation",
                              "Variabilität, Verwandtschaft, Geschichte und Evolution"],
            "task_kinds": ["experiment_protocol", "source_critique", "genetics_cross"],
            "notes": "Naturwissenschaften W/E/S; descriptors pre-numbered W1–W5/E1–E5/S1–S5 (dimension "
                     "letter recovered). 7 Basiskonzepte (content_areas). Evolution is a cross-cutting axis (W5/S4)."},
    "MAT": {"dims": [("DM", "Darstellend-modellierendes Arbeiten", "printable"),
                     ("FO", "Formal-operatives Arbeiten", "printable"),
                     ("ID", "Interpretierend-dokumentierendes Arbeiten", "printable"),
                     ("KA", "Kritisch-argumentatives Arbeiten", "printable")],
            "content_areas": ["Algebra und Geometrie", "Funktionale Abhängigkeiten",
                              "Analysis", "Wahrscheinlichkeit und Statistik"],
            "task_kinds": ["calculation", "proof", "construction", "modelling"],
            "notes": "3-dim Lehrplan model: Inhaltsdimension (content_areas) × Handlungsdimension (dims) × "
                     "Komplexitätsdimension (Grundwissen/Verbindungen/Problemlösen). Mirrors the Lehrplan, "
                     "NOT the Reifeprüfung Grundkompetenzen-Katalog (SME decision)."},
    "DEU": {"dims": [("MK", "Mündliche Kompetenz", "oral"),
                     ("SK", "Schriftliche Kompetenz", "printable"),
                     ("TK", "Textkompetenz", "printable"),
                     ("LB", "Literarische Bildung", "printable"),
                     ("MB", "Mediale Bildung", "printable")],
            "content_areas": None,
            "task_kinds": ["interpretation", "eroerterung", "textanalyse", "zusammenfassung", "kommentar"],
            "notes": "6 Kompetenzbereiche; Sprachreflexion (SR) is integrated into the others (marked (SR)), "
                     "not a standalone dimension. Semesterised by literary epoch."},
    "FSP": {"dims": [("HOR", "Hören", "audio"),
                     ("LES", "Lesen", "printable"),
                     ("AGT", "An Gesprächen teilnehmen", "oral"),
                     ("ZSP", "Zusammenhängendes Sprechen", "oral"),
                     ("SCH", "Schreiben", "printable")],
            "content_areas": None,
            "task_kinds": ["listening_task", "reading_task", "writing_task", "mediation"],
            "notes": "5 GER-Fertigkeiten, gleich gewichtet. CEFR ceiling B2 (FS1) / B1 (FS2). Sprachmittlung "
                     "is a technique. Target-language material + German teacher layer."},
    "LAT": {"dims": [("UEB", "Übersetzungskompetenz", "printable"),
                     ("INT", "Interpretationskompetenz", "printable")],
            "content_areas": None, "task_kinds": ["translation", "text_analysis", "open_response"],
            "notes": "Reuses the existing Latein annotated-text engine (translation/grammar/culture). "
                     "Modularised; vier-/sechsjährig variants tagged on lehrstoff."},
    "GRI": {"dims": [("UEB", "Übersetzungskompetenz", "printable"),
                     ("INT", "Interpretationskompetenz", "printable")],
            "content_areas": None, "task_kinds": ["translation", "text_analysis", "open_response"],
            "notes": "Oberstufe-only; same model as Latein (+ 'Belegen und Nachweisen'). All-PD originals; "
                     "needs a polytonic-Greek rendering font."},
    "GPB": {"dims": [("HFK", "Historische Fragekompetenz", "printable"),
                     ("HMK", "Historische Methodenkompetenz (Re-/De-Konstruktion)", "printable"),
                     ("HOK", "Historische Orientierungskompetenz", "printable"),
                     ("HSK", "Historische Sachkompetenz", "printable"),
                     ("PUK", "Politische Urteilskompetenz", "printable"),
                     ("PHK", "Politische Handlungskompetenz", "oral"),
                     ("PMK", "Politische Methodenkompetenz", "printable"),
                     ("PSK", "Politische Sachkompetenz", "printable")],
            "content_areas": ["Belegbarkeit", "Konstruktivität", "Kausalität",
                              "Perspektive und Auswahl"],
            "task_kinds": ["source_analysis", "dekonstruktion", "argumentation"],
            "notes": "Zusammenfassung Geschichte (5./6.) + GPB (7./8.). Historische + politische Kompetenzfamilien; "
                     "the Sachkompetenz Basiskonzepte are content_areas. Fits history/expression-provenance."},
    "GWB": {"dims": [("SYN", "Synthesekompetenz", "printable"),
                     ("KOM", "Kommunikationskompetenz", "printable"),
                     ("HAN", "Handlungskompetenz", "enactive"),
                     ("REF", "Reflexionskompetenz", "printable")],
            "content_areas": ["Raumkonstruktion", "Diversität und Disparität", "Maßstäblichkeit",
                              "Märkte, Regulierung und Deregulierung", "Wachstum und Krise",
                              "Mensch-Umwelt-Beziehungen", "Geoökosysteme", "Kontingenz"],
            "task_kinds": ["data_analysis", "source_critique"],
            "notes": "16 handlungsorientierte Basiskonzepte (content_areas lists the load-bearing subset). "
                     "Richer quantitative competences than Unterstufe → grounded data layer. AB II/III throughout."},
    "ETH": {"dims": [("WP", "Wahrnehmen und Perspektiven einnehmen", "printable"),
                     ("AR", "Analysieren und Reflektieren", "printable"),
                     ("AU", "Argumentieren und Urteilen", "printable"),
                     ("IS", "Interagieren und Sich-Mitteilen", "oral"),
                     ("HO", "Handlungsoptionen entwickeln", "printable")],
            "content_areas": None, "task_kinds": ["argumentation", "dilemma", "text_analysis"],
            "notes": "Oberstufe-only Pflichtgegenstand. 5 Kompetenzbereiche, all grades; each theme worked "
                     "through 3 perspectives (personal/gesellschaftlich/ideengeschichtlich). Diversitätsgebot "
                     "(neutrality is curriculum) → the dilemma asset class."},
    "PUP": {"dims": [("WIS", "Wissen reproduzieren", "printable"),
                     ("TRA", "Wissen verknüpfen und transferieren", "printable"),
                     ("REF", "Reflektieren", "printable")],
            "content_areas": ["Psychologie", "Philosophie"],
            "task_kinds": ["text_analysis", "argumentation", "dilemma"],
            "notes": "Oberstufe-only. Dimensions = the 3 Verarbeitungstiefen (depth axis, mirrors cognitive "
                     "ladder); content split Psychologie (5./6. Sem) / Philosophie (7./8. Sem). Approximate — "
                     "SME to confirm. Therapy boundary: descriptive only."},
    "DGE": {"dims": [("H1", "Analysieren, Modellbilden, Planen", "printable"),
                     ("H2", "Operieren (inkl. 3D-CAD)", "enactive"),
                     ("H3", "Interpretieren (Risse lesen)", "printable"),
                     ("H4", "Argumentieren, Begründen", "printable")],
            "content_areas": ["Objekte und Eigenschaften", "Relationen (Schnitte, Boolesche Ops)",
                              "Transformationen", "Abbildungen und Risse (Projektion und Riss)"],
            "task_kinds": ["construction", "projection_reading"],
            "notes": "(Handlung, Inhalt, Komplexität)-Tupel. H2-Operieren is CAD-bound (do not target as "
                     "worksheet); H3-Interpretieren / Risse-lesen is the printable sweet spot (new 3D-projection "
                     "figure backend)."},
    "INF": {"dims": [("WV", "Wissen und Verstehen", "printable"),
                     ("AG", "Anwenden und Gestalten", "enactive"),
                     ("RB", "Reflektieren und Bewerten", "printable")],
            "content_areas": ["Informatik-Mensch-Gesellschaft", "Informatiksysteme",
                              "Angewandte Informatik", "Praktische Informatik"],
            "task_kinds": ["algorithm_trace", "query", "argumentation"],
            "notes": "Oberstufe-new (Pflicht 5. Kl). Handlungsbereiche map to Reproduktion/Transfer/Reflexion. "
                     "Printable correct-by-construction core: Praktische Informatik (algorithm-trace, SQL, "
                     "truth tables — execution-verified). KI/intelligence strand hosts the dilemma class."},
    "HOE": {"dims": [("KQ", "Konsumverhalten und Qualität bewerten", "printable"),
                     ("RM", "Ressourcen managen", "printable"),
                     ("CC", "Consumer Citizenship", "printable"),
                     ("EV", "Essverhalten reflektieren", "printable"),
                     ("NE", "Sich vollwertig und nachhaltig ernähren", "enactive")],
            "content_areas": None, "task_kinds": ["calculation", "data_analysis", "source_critique"],
            "notes": "Oberstufe-new (5./6. Kl). Printable theory (Energie-/Nährstoffbedarf berechnen → parametric; "
                     "Ernährungsdaten → data layer). The Praktikum is enactive (out)."},
    "MUS": {"dims": [("MP", "Musikpraxis", "enactive"),
                     ("MR", "Musikrezeption", "printable")],
            "content_areas": None, "task_kinds": ["score_analysis"],
            "notes": "Marginal. Praxis performed; Rezeption has a printable score-analysis sliver (Notentext), "
                     "but the core competence is aural and audio is not machine-generatable. Theory is integrated, "
                     "not a standalone drill block."},
    "KUG": {"dims": [("BP", "Bildnerische Praxis", "enactive"),
                     ("DP", "Dokumentation und Präsentation", "enactive"),
                     ("RE", "Reflexion (Bildanalyse)", "printable")],
            "content_areas": None, "task_kinds": ["image_analysis"],
            "notes": "Marginal. Praxis/Doku are made/performed; only Reflexion (Bildanalyse) is printable, and it "
                     "needs an annotated-image engine blocked on the deferred sourced-image rights lane."},
}
CURATED["PUP2"] = dict(CURATED["PUP"], notes=CURATED["PUP"]["notes"] + " (WkRG variant, incl. Praktika.)")


def main():
    files = sorted(p for p in CAT.glob("*.json") if p.name not in ("_meta.json", "subject_models.json"))
    registry, models, warnings = [], {"_about":
        "Curated SubjectCompetenceModel overlay for the AHS Oberstufe (hand-authored from the Lehrplan "
        "models; SME decision: mirror the Lehrplan dimensions, not the Reifeprüfung Grundkompetenzen-"
        "Katalog). dims carry per-dimension modality ∈ printable|oral|enactive|audio. Built by "
        "tools/build_oberstufe_meta.py; cross-checked against the parsed descriptor groups."}, []

    for p in files:
        d = json.loads(p.read_text(encoding="utf-8"))
        code = d["code"]
        registry.append({
            "code": code, "name": d["name"], "type": d.get("type", "pflichtgegenstand"),
            "variant": d.get("variant"), "klassen": d.get("klassen", []),
            "n_descriptor": d.get("n_descriptor", 0), "n_lehrstoff": d.get("n_lehrstoff", 0),
            "n_competences": d.get("n_competences", 0), "file": p.name,
        })
        spec = CURATED.get(code)
        if not spec:
            warnings.append(f"{code}: no curated model — skipped"); continue
        desc_groups = sorted({c["kompetenzbereich"] for c in d["competences"]
                              if c.get("kind") == "descriptor"})
        n_desc_groups = len([g for g in desc_groups if g != "Kompetenzmodell"])
        if n_desc_groups and n_desc_groups != len(spec["dims"]):
            warnings.append(f"{code}: {len(spec['dims'])} curated dims vs {n_desc_groups} descriptor "
                            f"groups {desc_groups} — verify")
        models[code] = {
            "dimensions": [{"code": c, "label": l, "modality": m} for c, l, m in spec["dims"]],
            "content_areas": spec["content_areas"],
            "task_kind_extensions": spec["task_kinds"],
            "notes": spec["notes"],
        }
        if d.get("variant"):
            models[code]["variant"] = d["variant"]

    meta = {
        "fassung": FASSUNG, "stufe": "Oberstufe",
        "scope": "Achter Teil — A. Pflichtgegenstände — 2. Oberstufe",
        "uebergreifende_themen": [{"nr": i + 1, "label": lab} for i, lab in enumerate(UT_LEGEND)],
        "id_scheme": "<SUBJ>.OS.<KLASSE|x>.<KB>.<nn>  (KLASSE=5..8; x=grade-independent descriptor; "
                     "kind ∈ descriptor|lehrstoff)",
        "subjects": registry,
    }
    (CAT / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (CAT / "subject_models.json").write_text(json.dumps(models, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote _meta.json ({len(registry)} subjects) + subject_models.json ({len(models)} models).")
    if warnings:
        print("\nCross-check warnings (SME fact-check hooks):")
        for w in warnings:
            print(f"  ! {w}")
    else:
        print("All curated dimension sets match the descriptor groups.")


if __name__ == "__main__":
    main()
