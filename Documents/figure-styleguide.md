# Figure styleguide + the scene engine

How a TeachersAid figure *looks* and how a rich figure is *built*. Two layers, one goal:
figures that are **consistent** (a house visual language, colour that means something) and
**composable** (a small algebra of primitives, so a new figure is composed, not hand-coded).

Code: `pipeline/figstyle.py` (the styleguide) · `pipeline/scene.py` (the scene engine) ·
`pipeline/constructions.py` + `pipeline/calculus.py` (the first didactic recipes). Visual
reference: the `tools/*_specimen.py` scripts (re-runnable; render to `runs/`, git-ignored).

## Why

Two distinct problems hid under "our figures all look the same":

1. **Visual sameness.** Every one of the ~25 recipes in `pipeline/assets.py` hard-codes its
   own palette as inline hex literals (`#33506e`, `#4f6f8f`, `#b03a2e`, …), copy-pasted
   everywhere. There was no style module and so no lever to change anything — but the colours
   were already used *semantically consistently* (red = the thing of interest, blue =
   structure). The fix is to **name** that and centralise it, not to randomise.
2. **Compositional rigidity.** Each recipe draws one fixed thing. `function_graph` cannot host
   a curve *and* a shaded region *and* a tangent *and* an annotation on one canvas. Every rich
   figure meant a new bespoke recipe — the "ad-hoc build a lot" we want to kill.

## The styleguide — `pipeline/figstyle.py`

The single source of truth for the visual language.

### Semantic colour roles

Colour **means** something, and the same thing in every figure:

| role | use |
|---|---|
| `ink` | structure: axes, frames, the default curve, primary text |
| `muted` | secondary: leaders, citations, captions |
| `grid` | gridlines (quiet) |
| `primary` | the main data (one series of bars / one line) |
| `focus` | the element/region of **interest** — the unknown, the result, "look here" |
| `positive` / `negative` | honest-vs-misleading, correct-vs-wrong, +/− |
| `surface` / `surface_warm` | soft box fills |

The didactic payoff: a student learns that **red is always what we're solving for** — the
`c = ?` unknown, the shaded integral, the tangent are the same role in three figures.

### The two ramps

- **`CATEGORICAL`** — a qualitative hue ramp for several series at once. (Before this, a
  multi-series line silently fell back to matplotlib's defaults — you effectively had one data
  colour.) Slot 0 = `primary`, so single-series and first-of-many agree.
- **`DASHES` / `line_kind(i)`** — a **dash ramp**, the linestyle twin of the colour ramp. Its
  load-bearing reason: a worksheet gets **photocopied in black and white**, so colour alone
  can't carry a distinction. `line_kind(i)` pairs a hue **and** a dash per family — *redundant
  encoding* that survives greyscale. (Proven on the triangle: `tools/triangle_centers_specimen.py`
  renders in colour and greyscale side by side.)

### Typography, weights, theming

- **Document font.** `figstyle` registers Carlito/Calibri with matplotlib using the *same*
  discovery as `rendering/reportlab_base`, so figure text matches the worksheet body instead of
  matplotlib's DejaVu Sans (figures stop reading as "pasted in"). Falls back to DejaVu on a bare
  machine.
- **`TYPE`** (a type scale) and **`STROKE`** (axis/curve/grid/leader weights + marker sizes).
- **`subject_accent(subject)`** — the theming hook: a restrained per-subject hue layered on the
  *constant* semantic roles, so identity is a dial, not a rewrite. (Currently unused by default;
  turn it on when we decide on theming.)

### Applying it

- **`house_rc()`** returns the rcParams dict; **`scene_to_png` scopes it via `plt.rc_context`**,
  so building a scene does *not* restyle the not-yet-ported legacy recipes.
- **`use_house_style()`** applies it globally — for the eventual **port** of the ~25 legacy
  recipes (still on the backlog; they hard-code hexes for now).

## The scene engine — `pipeline/scene.py`

A figure as data: a **`Scene`** = a **`Canvas`** + an ordered list of typed **layers**. One
`render_scene` walks the scene and draws each layer in the house style.

| primitive | what |
|---|---|
| `Polyline` | a path — an object outline, a function curve, any multi-point line |
| `Line` | a styled segment; `family` → a hue+dash pair from the ramps |
| `PointMark` | a labelled point, optional leader |
| `CircleShape` | a circle (fill optional) |
| `Arc` | a circular arc (e.g. an angle mark), optional mid-angle label |
| `Region` | a filled area — a shaded integral, a Riemann rectangle, area between curves |
| `Label` | text, with an optional white halo so it reads over a busy figure |

**Why it matters:** a new rich figure becomes "compose a few primitives", not "write a 40-line
matplotlib function". And because a scene is *data*, the **same scene renders at different
densities** — which is what makes a step-by-step construction worksheet fall out of one computed
object. The model is **renderer-agnostic in shape** (a future SVG/Typst backend could walk the
same `Scene`).

### Two tiers (the correct-by-construction seam)

Mirrors the existing `GenDataFigure → choose_representation` split. **The LLM never authors a
Scene** — that would let it draw a wrong tangent or leak an answer. A **didactic recipe COMPUTES
the scene** from a small, correct-by-construction spec. The substrate (this module) is only the
primitives + the renderer.

## Didactic recipes so far

### Geometry — `pipeline/constructions.py`

`matplotlib:triangle_construction` — the *merkwürdige Punkte des Dreiecks*: Umkreis (U), Inkreis
(I), Schwerpunkt (S), Höhenschnittpunkt (H), the Eulergerade and the Feuerbachkreis, **all
computed from the three vertices** (`triangle_geometry`). `stage` 1–6 renders the construction
cumulatively — helping lines bright in their step, then receded to just the result — so *one
computed object → the whole step-by-step construction worksheet*. Move a vertex and everything
re-solves.

### Analysis — `pipeline/calculus.py`

The analysis family, correct-by-construction via **sympy**. The LLM declares the function as an
expression string (a *parameter*, not a drawing); code samples, differentiates, and integrates
it. `tangent_slope` and `definite_integral` are the tested computational core.

| recipe | what is COMPUTED |
|---|---|
| `matplotlib:function_plot` | an arbitrary `f(x)` (which `function_graph` can't draw) |
| `matplotlib:integral_area` | the shaded ∫; the area value |
| `matplotlib:tangent` | the tangent at x₀; slope k = f'(x₀) + Steigungsdreieck |
| `matplotlib:riemann_sum` | n rectangles; the sum AND the exact value (error visible) |
| `matplotlib:extrema` | Hoch-/Tiefpunkt from f'(x)=0, classified by f''(x) |
| `matplotlib:area_between` | area between two curves = ∫\|f−g\|; auto-finds intersections |
| `matplotlib:distribution` | normal density with a probability region; area = P (WS strand) |

**Value masking (the task/solution split):** `show_value=False` → "A = ?" / "k = ?", so the
*same scene* is the student's task figure and the teacher's worked solution.

## The data-figure system (intent → representation)

The data-recipe half of the figure engine (the scene engine above is the structural half). Same
two-tier split: **the generator declares WHAT the data is, never the chart type** —
`GenDataFigure(intent, data)` in the generation views — and the **deterministic**
`schema/chart_choose.py::choose_representation` maps intent → recipe. The LLM declares intent; code
guarantees a legible representation.

| intent | recipe |
|---|---|
| `trend` | `line` |
| `relationship` | `scatter` (+ optional fit) |
| `distribution` | `histogram` |
| `spread` (five-number summary / compare distributions) | `boxplot` |
| `scale` (orders of magnitude) | `number_line` |
| `comparison` / `composition` | `bar_chart` |
| `demographic` (age × sex) | `population_pyramid` |
| `timeline` (dated events) | `timeline` (lane-packed labels via `figtext`) |
| `climate` (Klimadiagramm) | `climate_diagram` (Walter-Lieth: temp line on the left °C axis + precip bars on the right mm axis, via `twinx`) |

(`boxplot` + `tree_diagram` came out of the accessible-Matura figure scan, WS strand —
`matura-math-coverage.md`.)

### The recipe vocabulary (`GENERATION_RECIPES`)

- **data:** `number_line · bar_chart · line · scatter · histogram · boxplot · population_pyramid ·
  timeline · climate_diagram · choropleth_map`
- **math / structural:** `function_graph · math_formula` (mathtext) · the **geometry family (KB3)**
  `right_triangle · rectangle · polygon · circle · coordinate_plane` · the probability tree
  `tree_diagram` (Baumdiagramm, spec-provided branch probabilities, via `body.assets`)
- **scene recipes:** `triangle_construction` · the analysis family (above) · `cause_effect` ·
  `process_flow` (the Sachverhalt-derived figures) · `labeled_parts` ("Beschrifte die Teile",
  numbered-student/named-teacher projections) · `homology_schema` (the Biology vertebrate-Bauplan
  comparison — see below)
- **curated schematic comparison:** `homology_schema` (`pipeline/homology.py`) — schematic side-view
  silhouettes of vertebrates (Fisch · Frosch · Vogel · Hund) with the **forelimb pair in one role
  (`focus`) and the hindlimb pair in another (`primary`) — the SAME two colours on every animal**, so
  "gleicher Bauplan, verschiedene Werkzeuge" (homologe Gliedmaßen → gemeinsame Abstammung) reads at a
  glance while the *shape* varies (a red fin, a red wing, a red leg — homolog, verschieden geformt). A
  solid outline (fore) vs. dashed (hind) keeps the pairs apart in a B/W photocopy; a legend maps colour
  → Gliedmaßenpaar. **Correct by CURATION**, not invented numbers: the limb homologies are curated facts
  (`ANIMALS`), each animal declares exactly two fore + two hind limbs, and the unpaired fish fins stay
  neutral grey. This is the honest replacement for a "count the limb pairs" bar chart — a chart invites
  "find the differences", the opposite of the homology message.
- **physics scenes:** `optics_ray` (thin-lens Bildkonstruktion) · `circuit` (Schaltbild) ·
  `vector_addition`/`force_diagram` · `pinhole_camera` (Lochkamera — the two rays CROSS in the
  single hole, so the image is kopfstehend by construction; B = G·b/a) · `shadow_cone` (Schattenraum
  — closed-form tangents from a point source to a Kugel; the shaded Kernschatten has exactly one
  sharp edge per side — no Halbschatten). All computed, `show_value`-maskable, no coordinate axes.

`body.data_figures` (intent-declared) is the preferred seam for data; `body.assets` (explicit
generator) is for structural/geometry figures. Labels are **spec-provided** so a figure never leaks
the answer (e.g. "c = ?").

### Layout self-correction + the chart lint

Recipes self-correct their layout: `bar_chart` goes auto-horizontal for long/many labels, puts a value
label on **every** bar (so none is "invisible"), and offers `log` for orders-of-magnitude ranges;
titles wrap; `constrained_layout` throughout. `pipeline/chart_lint.py` (run in `verify`) flags
misrepresentations: a 0/1 "classification" plotted as bars; an extreme range that begs a log/table
decision; numeric/temporal x-values forced into bars (that data is a trend/relationship → line/scatter).

### Number & axis formatting (house rules)

Figures **never use scientific notation**: unit-scaled axis/value labels (`figstyle.unit_scale` →
"(in Mio.)"), German number formatting (`figstyle.fmt_de` — dot/space thousands, comma decimals), and
years on a **numeric** x-axis, not a categorical one. The **(c)-label discipline**: every data figure
(`bar_chart · line · scatter · histogram · population_pyramid · choropleth_map`) is exactly one of
`data_source` (sourced + cited; values derived from the dataset slice at assemble by
`data_ground.ground_data`) or `illustrative=True` (schematic); `pipeline/figure_lint.py` warns
otherwise. Pure-math figures are exempt.

## Guarantees the engine keeps

- **Correct by construction.** Every number/geometry is computed (sympy for analysis, closed-form
  for the triangle centres), never authored. `tests/test_scene.py` + `tests/test_calculus.py` lock
  the geometry's defining properties (circumcentre equidistant, incircle tangent, U·S·H collinear)
  and the computed values against ground truth (f'(x²)=2x, ∫₀¹x²=⅓, P(X≤μ)=½, …).
- **No answer leak.** Labels are spec-provided and maskable; a task figure shows "c = ?" / "A = ?".
- **Legibility.** Inherits the measure→fit→de-collide discipline of `pipeline/figtext.py`; the dash
  ramp for density; halos on labels over busy figures.

## What's next

- **Port the ~25 legacy recipes** — ✅ **DONE (9 Jul 2026).** Every recipe in
  `pipeline/assets.py` consumes the roles/ramps/type scale; `build_asset` scopes `house_rc()`
  over every build, so multi-series lines pick up the categorical ramp via `axes.prop_cycle`.
  Semantic wins along the way: the misleading/honest axis pair renders in `negative`/`positive`,
  the EM spectrum's ionising boundary likewise, the Klimadiagramm's two axes are colour-keyed to
  their series (temp = `focus`, precip = `primary`), and `math_formula` pins black so display
  formulas keep matching the inline-math runs. Only the decorative banner hue stays literal
  (curated, content-free). **Found + fixed in the port — the Windows-Calibri embedded-bitmap
  bug:** Calibri carries EBDT/EBLC bitmap strikes; FreeType selects them at exactly their ppem
  sizes and Agg then draws EMPTY outlines — text at e.g. 9 pt/150 dpi silently vanished while
  still *measuring* (so the overlap lint couldn't see it). `figstyle._register_font` now strips
  the strike tables (fontTools — already a matplotlib dep) into a cached outline-only copy and
  purges the strike-carrying originals from the font manager; locked by
  `tests/test_layout.py::test_house_font_renders_glyphs_at_every_size` (every TYPE size × asset
  and scene dpi must produce visible glyphs).
- **More scene recipes** — ✅ **DONE (10 Jul 2026):** physics `vector_addition`/`force_diagram`
  (`pipeline/physics_scenes.py`, an `Arrow` primitive with filled head/`family` hue/midpoint label/
  `curve`/`shrink`), `labeled_parts` (`pipeline/labeled_diagram.py`, leader-callouts, numbered-student /
  named-teacher projections), and the node-link consolidation — `tree_diagram`/`cause_effect`/
  `process_flow` are thin wrappers over `pipeline/nodelink.py` (a `Node` rounded-box primitive; frozen
  generator ids + specs).
- **A first-class density/stage selector** — ✅ **DONE (10 Jul 2026):** every layer takes a `group` tag;
  `Scene.select(*groups)` keeps untagged layers + the named groups (order preserved, shared Canvas);
  `constructions.py`'s stage 1–6 selects from one full grouped scene with identical per-stage output.
- **3D analytic geometry** — ✅ **BUILT (Wave A7 + prototype, `scene3d-geometry-design.md`):** the scene
  model extends to ℝ³ by projecting a 3D situation (sympy-computed planes/normals/Schnittgerade,
  Kegelschnitte) through a fixed **Schrägriss** map into these same 2D primitives — `render_scene` +
  `figstyle` reused wholesale, hidden-line occlusion per GZ convention (front arcs solid, occluded
  DASHED). Recipes: `matplotlib:axonometric_solid` + `matplotlib:riss_pair` (`pipeline/scene3d.py`).

*Reconciliation note (10 Jul 2026):* the port was independently implemented on both development
machines; the unified version keeps the workhorse line's SME-reviewed recipe bodies + representation
rules (`fmt_de`/`unit_scale`, `secondary`/`no_data` roles) and this line's font fix — strikes are
STRIPPED at registration (root cause) with the `_renders_small` probe kept as the measured safety net.
