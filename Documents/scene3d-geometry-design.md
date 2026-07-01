# 3D analytic geometry — projected scenes (Schrägbild)

How the figure engine reaches **ℝ³**: parametrized planes + normal vectors, the Schnittgerade of
two planes, the enclosed angle, and **Kegelschnitte** (a cone sliced by a plane → ellipse ·
parabola · hyperbola). Print-first, not interactive.

**Status: validated prototype.** The whole arc runs in the specimen `tools/plane3d_specimen.py`
(re-runnable; renders to `runs/`, git-ignored). It is *not yet* promoted into the package — the
promotion path is at the bottom. Sibling of the 2D scene engine (`Documents/figure-styleguide.md`).

## The curriculum it serves (Oberstufe MAT, verified against `lehrplan/oberstufe/MAT.json`)

- **Kl. 6 — "Vektoren und analytische Geometrie in ℝ³":** *"Normalvektoren ermitteln; Ebenen durch
  Parameterdarstellungen bzw. Gleichungen (Normalvektordarstellungen) beschreiben"* — planes,
  normals, plane∩plane, angle.
- **Kl. 7 — "Kreise, Kugeln, Kegelschnittlinien und andere Kurven":** conics through equations,
  *gegenseitige Lage Kegelschnitt–Gerade* + Schnittpunkte + **Tangente**.

This is the priority-3 **AG** gap flagged in `matura-math-coverage.md` ("analytic geometry of
lines/vectors — extends `vector_dot_angle`"), plus the whole Kl. 7 Kegelschnitte KB.

## The load-bearing idea: model in 3D, project to a 2D `Scene`, reuse everything

The figure engine is two layers — **computation** (sympy computes the correct object) and
**rendering** (the 2D `Scene` → matplotlib). 3D is near-free in the first and a bounded decision in
the second. The design keeps them apart:

1. **Compute in 3D.** sympy (already the `calculus.py` dependency) owns the geometry: a plane from a
   point+normal, `E.intersection(F)` → the Schnittgerade (a `Line3D`; empty when parallel — the
   honest gap falls out), `E.angle_between(F)`, `E.equation()`. The conic section is solved from
   cone∩plane. **The model never authors a computed coordinate** — it declares *parameters* (plane
   coefficients, the cone's `k`/`m`/`c`); code computes the rest. Same two-tier seam as everywhere
   (`GenDataFigure → choose_representation`, the calculus recipes): the LLM declares intent, code
   guarantees the object. A wrong Schnittgerade — exactly the error-prone hand-computation this
   whole engine exists to prevent — is structurally impossible.
2. **Project to a 2D `Scene`.** A single fixed **linear map ℝ³→ℝ²** (a parallel projection) turns the
   3D situation into ordinary 2D `scene` primitives, so the **entire existing renderer**
   (`scene.render_scene`), styleguide (`figstyle`: semantic colour roles, halos, the photocopy-safe
   dash ramp) and legibility machinery are reused unchanged. No `mplot3d`, nothing interactive — a
   print Schrägbild, the way an AHS Schulbuch draws it. This is exactly the direction `scene.py`
   already anticipates ("renderer-agnostic in shape… a future backend could walk the same `Scene`").

Value-masking (`show_value=False` → "n⃗ = ?" / "φ = ?") and the triangle's `stage 1–6` build-up carry
over unchanged: one computed object → the student task figure, the teacher solution, and a
step-by-step (plane 1 → plane 2 → crease → normals → angle).

### The projection (house default: Schrägriss)

`project(P) = x·AXO.x + y·AXO.y + z·AXO.z` — the columns are the screen images of the unit axes; one
map applied to every point ⇒ a consistent parallel projection. Two conventions, one-line swap:

- **`SCHRAEGRISS` (default)** — the strict Austrian Kabinettprojektion: ŷ horizontal, ẑ vertical, x̂
  (the receding depth axis) at 45° lower-left, foreshortened ½. Coordinate-reading is easy; it's what
  students see. Chosen as the default (SME preference).
- **`AXO_34`** — a general 3/4 view (nothing axis-aligned); reads more "spatial". Preferred for
  **cone** figures, where depth matters more than coordinate-reading (the triptych uses it).

### The `Scene3D` vocabulary (throwaway sketch of the eventual `pipeline/scene3d.py`)

Typed 3D primitives that project into the 2D `scene` primitives: `Seg3 · Path3 · Patch3` (a plane
patch = translucent fill + dash-coded boundary, so two planes stay distinct in B/W) · `Fill3`
(boundary-less body fill, e.g. the cone) · `Arrow3` (a vector — **composed** from primitives, an
arrowhead built in 2D, so `scene.py` stays untouched) · `Dot3 · Text3`. Draw order (z) is explicit,
as in the triangle recipe.

## Occlusion — hidden-line determination (the robust tier and its boundary)

The powerful part, and where the honest boundary lives. Under **parallel projection** the projection
rays are one fixed 3D direction — the **null vector of the `AXO` matrix** — so it comes free and is
correct for either projection. Visibility of a curve point is then a **closed-form ray test** against
an analytic surface, not a mesh raycast.

**Robust, genuinely general (not case-by-case):** a curve occluded by known analytic bodies. One
reusable machine: (1) the view direction from the matrix; (2) **one write-once predicate per surface
*type*** — a cone is a quadric → one quadratic (`cone_occluder`); a plane → linear; a sphere/cylinder
→ quadratics; (3) a generic `split_visibility(curve, occluders, d)` that dashes the hidden runs. A new
occludable body = one small function, touching zero figures. It's **exact** (closed-form), fits the
correct-by-construction seam (visibility computed at projection time), and covers essentially the whole
analytic-geometry/Kegelschnitte curriculum.

**The boundary (design rule — do NOT over-promise):** *many mutually-interpenetrating **opaque**
surfaces* is the classical hidden-surface problem (split surfaces along their intersection curves,
globally order the pieces) — GPU-z-buffer territory, and matplotlib is a painter, not a z-buffer. We
**bound it to a handful of objects** or **sidestep it with translucency** — drawing planes
semi-transparent means "you see both" is honest and needs no ordering. Per figure it's a clean choice:
**translucent** (no occlusion math) *or* **opaque with computed dashing**. The one thing we can't do is
crisp hidden-line dashing *through* a translucent surface.

## Kegelschnitte — one recipe, three conics; and the 2D working representation

**The cone-slice (motivation).** Substituting the plane `{z = c + m·y}` into the cone `x²+y²=(k·z)²`
gives `x² = A·y² + B·y + C`, and **`sign(A) = sign(k²m²−1)` decides the conic**: `|m|<1/k` → bounded →
**ellipse**; `m=1/k` → `A=0` → **parabola**; `|m|>1/k` → two disjoint y-intervals → **hyperbola** (two
branches, both nappes). The conic type *falls out of the arithmetic* — nothing is drawn to look right.
Occlusion dashes each hidden arc.

*Load-bearing subtlety (a real bug we fixed):* the two `x = ±√P` arms may be joined **only at genuine
vertices** (roots, where `x=0`), never across a cone-height clip — else a parabola/hyperbola gets a
spurious straight chord slamming its open end shut. `cone_section_curve` returns `(closed, points)`:
ellipse = both ends vertices → closed; parabola = one vertex → open; hyperbola = two open branches. An
*abstraction of an infinite cone* is fine; a parabola that doesn't look like a parabola is not.

**The 2D conic-plus-tangent (the actual task surface).** As *taught* in Kl. 7, Kegelschnitte is mostly
a **2D** problem: the conic in the coordinate plane, `gegenseitige Lage` with a line, the **Tangente**.
That drops straight into the **existing 2D scene engine** — no 3D machinery. `scene_ellipse_tangent`:
ellipse + point P + the tangent (computed, cleared to integers via sympy `Rational` → `t: 15x+32y=100`)
+ foci, maskable (`t: ?` for the student sheet). The cone-slice is the *why*; this is the workhorse.

## What's validated (the specimen figures)

`tools/plane3d_specimen.py` → `runs/`: plane-from-normal · two-planes-intersection (both projections) ·
the occluded cone-slice ellipse · the three-conic triptych (one cone, three planes) · the 2D
ellipse-tangent. All sympy-computed, print-first, greyscale-robust (the dash ramp + hidden-line
dashing survive a B/W photocopy).

## Promotion path (mechanical, once the look is banked)

1. **`pipeline/scene3d.py`** — lift `Scene3D` + `project()` (Schrägriss default) + the occlusion pass;
   promote `Fill3`/`Arrow3` to real primitives.
2. **`@_generator` recipes** — `matplotlib:plane_normal · plane_intersection · cone_section ·
   conic_tangent`, with `GENERATION_RECIPES` entries (declared parameters only), following the
   triangle/calculus pattern. Structural/geometry figures ride `body.assets`, not `data_figures`.
3. **Occluder predicates** — a small write-once set (`cone`, `plane`, `sphere`).
4. **Tests** (`tests/test_scene3d.py`, mirroring `test_scene`/`test_calculus`) — lock the computed
   facts: Schnittgerade direction, `angle_between`, the ellipse's semi-axes from cone∩plane, and a
   visibility split (front visible / back hidden).
5. Keep this doc as the design record; the **occlusion boundary** above is the rule a future recipe
   author checks themselves against.
