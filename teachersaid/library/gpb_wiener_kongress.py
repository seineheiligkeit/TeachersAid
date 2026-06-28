"""Hand-authored GPB 'Der Wiener Kongress' (3. Kl.) — the History asset-class flagship.

The worked example for **expression provenance** (the History/GPB asset class; see
`Documents/history-facts-provenance-design.md`). It demonstrates BOTH paths on real content:

* **Path #1 — facts → original.** The learn text (i1/i2) is authored *fresh from facts* read off
  Wikipedia; `expression_origin="original"` + a `role="facts"` Wikipedia record (a real permalink
  to the exact revision, fetched once by `tools/fetch_wikipedia.py`). No CC-BY-SA obligation; the
  student sheet renders clean; the facts record is teacher/review-only — the mandatory-internal
  trust rule, so the fact is fact-checked at the gate, not asserted unchecked.
* **Path #2 — a real primary source, quoted.** "Quelle 1" embeds a SHORT verbatim excerpt of the
  **Deutsche Bundesakte, Artikel I (8. Juni 1815)** — an actual, verifiable public-domain primary
  source (Wikisource), `expression_origin="quoted"`, riding the Austrian Zitatrecht (§42f öUrhG).
  The quotation is *selected*, never authored (we do not fabricate historical wording).

The through-line is the core GPB competence the asset class is built around: **Quellen und
Darstellungen unterscheiden** — a Wikipedia article is a *Darstellung* (a later account), the
Bundesakte is a *Quelle* (a source from 1815); they tell you different things, and the difference
is the lesson. The tasks exercise HME (Methoden-/Quellenarbeit), HSA (Sachkompetenz), HFR
(Fragekompetenz) and HOR/PUR (Orientierung/Urteil), serving real GPB.US.3.* competences.

Note on orthography: the Quelle keeps its period spelling ("Teutschlands", "Vortheilen",
"Europa's") verbatim — authentic source text is itself a Quellenkritik cue.
"""

from __future__ import annotations

from ..grounding import lehrplan_store as store
from ..schema.blocks import InfoBlock, TaskBlock
from ..schema.provenance import BlockProvenance, ProvenanceSource
from ..schema.worksheet import (
    Baustein,
    BundleRequest,
    WorksheetContent,
    WorksheetMeta,
)

SUBJECT = "Geschichte und politische Bildung"

# --- provenance records (selected, never authored) ---------------------------
# Path #1: the Wikipedia FACTS record — a snapshot fetched once via tools/fetch_wikipedia.py
# (permalink to the exact revision, so the citation is stable as the live article changes).
_WP_FACTS = ProvenanceSource(
    title="Wiener Kongress",
    url="https://de.wikipedia.org/w/index.php?title=Wiener_Kongress&oldid=267935028",
    publisher="Wikipedia (de)",
    licence="CC-BY-SA-4.0",
    licence_url="https://creativecommons.org/licenses/by-sa/4.0/",
    retrieved="2026-06-28",
    role="facts",
)

# Path #2: a SHORT verbatim excerpt of a real PD primary source (Wikisource), riding Zitatrecht.
_BUNDESAKTE_QUOTE = (
    "… und von den Vortheilen überzeugt, welche aus ihrer festen und dauerhaften Verbindung "
    "für die Sicherheit und Unabhängigkeit Teutschlands, und die Ruhe und das Gleichgewicht "
    "Europa's hervorgehen würden, sind übereingekommen, sich zu einem beständigen Bunde zu "
    "vereinigen …"
)
_BUNDESAKTE = ProvenanceSource(
    title="Deutsche Bundesakte, Artikel I (8. Juni 1815)",
    url="https://de.wikisource.org/wiki/Die_teutsche_Bundesacte_vom_8._Juny_1815",
    publisher="Wikisource — Die Constitutionen der europäischen Staaten seit den letzten "
              "25 Jahren, Bd. 2 (1817)",
    licence="public-domain",
    role="expression",
    redistributable=True,            # PD by age (1815) — a 200-Jahre-altes Staatsdokument
    author_death_year=1859,          # a principal architect/signatory (Metternich); well >70 p.m.a.
    quote_span=_BUNDESAKTE_QUOTE,
)


def build_request() -> BundleRequest:
    # GPB's Kompetenzbereiche are competence strands, not content themes, so resolution
    # anchors to the GRADE (resolve_grade), not the topic — see the test.
    return BundleRequest(subject=SUBJECT, klasse=3, topic_raw="Der Wiener Kongress",
                         envelope="doppelstunde")


def _intro() -> list:
    return [
        InfoBlock(
            id="wk.i1", kind="prose",
            content=(
                "Nach der endgültigen Niederlage Napoleons ordneten die europäischen "
                "Großmächte 1814/15 auf einem Kongress in Wien den Kontinent neu. Leitend war "
                "der Gedanke eines Gleichgewichts der Mächte: Kein Staat sollte wieder so "
                "übermächtig werden, dass er ganz Europa beherrschen könnte. Zugleich kehrten "
                "viele Fürsten an die Macht zurück, die in der Zeit Napoleons verdrängt worden "
                "waren — diese Rückkehr zur alten Ordnung nennt man Restauration."
            ),
            provenance=BlockProvenance(expression_origin="original", sources=[_WP_FACTS]),
        ),
        InfoBlock(
            id="wk.i2", kind="key_fact",
            content=(
                "An die Stelle des 1806 untergegangenen Heiligen Römischen Reichs trat kein "
                "neuer Gesamtstaat, sondern ein lockerer Staatenbund: der Deutsche Bund. Die in "
                "Wien geschaffene Ordnung prägte Europa über Jahrzehnte und gilt als Beginn einer "
                "Epoche der Restauration."
            ),
            provenance=BlockProvenance(expression_origin="original", sources=[_WP_FACTS]),
        ),
        InfoBlock(
            id="wk.q1", kind="source_text",
            content=_BUNDESAKTE_QUOTE,
            teacher_note=(
                "Quelle 1 ist ein Auszug aus dem Originaltext von 1815 (historische "
                "Rechtschreibung beibehalten). Sie ist eine QUELLE — im Unterschied zum "
                "Wikipedia-Artikel, der eine DARSTELLUNG ist."
            ),
            provenance=BlockProvenance(expression_origin="quoted", sources=[_BUNDESAKTE]),
        ),
    ]


def _tasks() -> list[TaskBlock]:
    t1 = TaskBlock(  # HSA · remember — orient in time (a low band, builds the prerequisite)
        id="wk.t1", kind="ordering",
        prompt="Bringe die drei Ereignisse in die richtige zeitliche Reihenfolge.",
        payload={"kind": "ordering", "items": [
            "Gründung des Deutschen Bundes (Bundesakte)",
            "endgültige Niederlage Napoleons",
            "Beginn des Wiener Kongresses"]},
        response={"mode": "lines", "n": 3},
        cognitive_level="remember", dimensions=["HSA"],
        serves=[{"competence_id": "GPB.US.3.ALL.05", "relation": "builds_prerequisite"}],
        est_minutes=5,
        answer_key=("1. Niederlage Napoleons → 2. Beginn des Wiener Kongresses (1814/15) → "
                    "3. Gründung des Deutschen Bundes (Bundesakte, 8. Juni 1815)."),
    )
    t2 = TaskBlock(  # HME · analyze — the Wikipedia article AS a Darstellung
        id="wk.t2", kind="source_analysis",
        prompt=(
            "Der verlinkte Wikipedia-Artikel „Wiener Kongress“ ist eine Darstellung — ein "
            "späterer, zusammenfassender Bericht, keine Quelle aus der Zeit. Untersuche ihn: "
            "(a) Nach welchem Leitprinzip wird Europa neu geordnet? (b) Woran erkennst du, dass "
            "es sich um eine Darstellung und nicht um eine Quelle handelt? Nenne zwei Merkmale."
        ),
        response={"mode": "lines", "n": 6},
        cognitive_level="analyze", dimensions=["HME"],
        serves=[{"competence_id": "GPB.US.3.ALL.01", "relation": "exercises"}],
        est_minutes=12,
        answer_key=(
            "(a) Gleichgewicht der Mächte. (b) Merkmale einer Darstellung: rückblickende "
            "Einordnung und Wertung (z. B. „Restauration“, „Epoche“), Zusammenfassung über "
            "lange Zeiträume, keine zeitgenössische Stimme, belegende Verweise/Literatur."
        ),
        acceptable_reasoning=(
            "Akzeptiere jedes Merkmalspaar, das eine spätere Deutung von einer zeitgenössischen "
            "Quelle unterscheidet (Rückblick, Wertung, Zusammenfassung, Belegapparat)."
        ),
        watch_outs=[
            "Kern der Aufgabe ist die Unterscheidung Quelle/Darstellung — nicht das Nacherzählen "
            "des Inhalts. Würdige jede saubere Begründung dieser Unterscheidung.",
        ],
    )
    t3 = TaskBlock(  # HME · analyze — Quelle 1 (the Bundesakte primary source)
        id="wk.t3", kind="source_analysis",
        prompt=(
            "Lies Quelle 1 (Auszug aus der Deutschen Bundesakte von 1815). (a) Welches Ziel der "
            "Fürsten wird darin ausdrücklich genannt? Belege mit einer Wendung aus dem Text. "
            "(b) Welches Wort im Text passt zum Leitprinzip des Kongresses aus dem Lerntext?"
        ),
        response={"mode": "lines", "n": 5},
        cognitive_level="analyze", dimensions=["HME"],
        serves=[{"competence_id": "GPB.US.3.ALL.02", "relation": "exercises"}],
        est_minutes=12,
        answer_key=(
            "(a) Sich „zu einem beständigen Bunde zu vereinigen“ — zur Sicherheit und "
            "Unabhängigkeit sowie zur „Ruhe“. (b) „Gleichgewicht“ (Europa's) — dasselbe "
            "Leitprinzip, das der Lerntext nennt."
        ),
        watch_outs=[
            "HME/Quellenarbeit: Der Beleg muss eine WÖRTLICHE Wendung aus Quelle 1 sein, keine "
            "Paraphrase aus dem Lerntext.",
        ],
    )
    t4 = TaskBlock(  # HSA · analyze — compare Quelle vs. Darstellung (the asset-class point)
        id="wk.t4", kind="open_response",
        prompt=(
            "Vergleiche Quelle 1 (Bundesakte, 1815) mit dem Wikipedia-Artikel (Darstellung): "
            "Was kann dir die Quelle sagen, was die Darstellung NICHT kann — und umgekehrt? "
            "Gib je ein Beispiel."
        ),
        response={"mode": "box", "min_height_mm": 55},
        cognitive_level="analyze", dimensions=["HSA", "HME"],
        serves=[{"competence_id": "GPB.US.3.ALL.04", "relation": "exercises"}],
        est_minutes=12,
        acceptable_reasoning=(
            "Quelle: zeigt die zeitgenössische Sprache, Selbstdarstellung und erklärten Ziele "
            "der Beteiligten (authentisch, aber parteiisch und ohne Überblick). Darstellung: "
            "ordnet ein, fasst zusammen, bewertet die Folgen aus späterer Sicht (Überblick, aber "
            "keine zeitgenössische Stimme). Je ein passendes Beispiel genügt."
        ),
        watch_outs=[
            "Das ist die Kernidee der Stunde: Quelle ≠ Darstellung. Auf ein Beispiel je Richtung "
            "achten, nicht auf eine Wertung welche „besser“ sei.",
        ],
    )
    t5 = TaskBlock(  # HOR/PUR · evaluate — a judgment (the high band)
        id="wk.t5", kind="position_argument",
        prompt=(
            "„Der Wiener Kongress brachte vor allem Stabilität.“ Nimm zu dieser Aussage Stellung: "
            "Was spricht dafür, was dagegen (denke an die zurückgekehrten Fürsten und an die "
            "Menschen, die sich mehr Mitbestimmung wünschten)? Begründe am Ende dein eigenes Urteil."
        ),
        response={"mode": "box", "min_height_mm": 60},
        cognitive_level="evaluate", dimensions=["HOR"],
        serves=[{"competence_id": "GPB.US.3.ALL.06", "relation": "exercises"}],
        est_minutes=14,
        acceptable_reasoning=(
            "Dafür: langer Frieden zwischen den Großmächten, Gleichgewicht, klare Ordnung. "
            "Dagegen: Restauration unterdrückte liberale und nationale Wünsche; Stabilität "
            "auch um den Preis fehlender Mitbestimmung. Ein begründetes Urteil in beide "
            "Richtungen ist gültig — bewertet wird die Begründung, nicht die Position."
        ),
        watch_outs=[
            "Urteilskompetenz: ein einseitiges „gut/schlecht“ verfehlt die Aufgabe. Auf das "
            "Abwägen UND ein begründetes eigenes Urteil achten.",
        ],
    )
    return [t1, t2, t3, t4, t5]


def build_content() -> WorksheetContent:
    model = store.get_subject_model(SUBJECT)
    fassung = store.get_fassung()
    meta = WorksheetMeta(
        title="Der Wiener Kongress",
        subtitle="Quelle und Darstellung — wie wir über 1815 Bescheid wissen",
        subject=SUBJECT,
        stufe="Unterstufe",
        klasse=3,
        kernfrage="Wie ordnet der Wiener Kongress Europa neu — und woher wissen wir das?",
        fassung=fassung,
        lehrplan_label="Geschichte und politische Bildung · 3. Klasse · Der Wiener Kongress",
    )
    section = Baustein(
        id="wk.kern",
        title="Quelle ≠ Darstellung",
        teacher_overview={
            "throughline": (
                "Über die Vergangenheit wissen wir aus Quellen (von damals) UND aus "
                "Darstellungen (von heute) — beide sagen Verschiedenes, und das ist der Punkt."
            ),
            "talking_points": [
                "Quelle vs. Darstellung am konkreten Paar festmachen: Bundesakte (1815) vs. "
                "Wikipedia-Artikel (heute). Nicht definieren lassen, sondern unterscheiden lassen.",
                "„Gleichgewicht der Mächte“ taucht im Lerntext UND in Quelle 1 auf — die Brücke "
                "zwischen Darstellung und Quelle (Aufgabe t3).",
                "Restauration hat zwei Seiten: Stabilität für die Mächte, Rückschritt für "
                "Mitbestimmung — der Stoff für das Urteil in t5.",
            ],
            "extensions": [
                "Eine zweite Quelle (z. B. eine Karikatur der Zeit) hinzunehmen und mit der "
                "Bundesakte vergleichen — verschiedene Quellengattungen.",
                "Vergleich der Friedensordnung von 1815 mit jener nach 1918/1945.",
            ],
            "timing_notes": (
                "Doppelstunde. Die Provenienz-Logik ist im Hintergrund: Der Lerntext ist aus "
                "Fakten frei formuliert (Wikipedia nur als Faktenquelle, schülerseitig nicht "
                "zitiert), Quelle 1 ist ein kurzes wörtliches Zitat (mit Quellenangabe)."
            ),
            "differentiation": (
                "Basis: t1–t3 sichern Orientierung und Quellenarbeit. Vertiefung: t4 (Vergleich) "
                "und t5 (Urteil) für leistungsstärkere Schüler:innen."
            ),
        },
        blocks=_tasks(),
    )
    return WorksheetContent(
        meta=meta, subject_model=model, intro=_intro(), sections=[section],
    )
