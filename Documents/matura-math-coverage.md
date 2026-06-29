# Matura → math-engine coverage (demand map)

*Turns the extracted Zentralmatura corpus into a **demand-driven spec** for the parametric
math engine (`pipeline/parametrize.py`). Source: 6 AHS-Math Haupttermin exams 2014–2025,
141 tasks, via `tools/extract_matura.py`. The topic read is from task titles + GK codes +
the Lösungserwartung formulas — enough for a coverage map without the accessible (linearized-
math) versions; those help only when specing a chosen recipe's exact parameter ranges.*

## The strategy this serves — *Matura-backward design*

The SRDP/Matura is the competence **endpoint**, and in the exam it usually appears in its
most **minimal** form — a checkbox, a one-line *„Kreuzen Sie an“*, a single value. That
terseness is an **assessment** artefact, not a teaching one. Our value is to **invert** it:
take the endpoint competence the Matura certifies and build the *rich, scaffolded,
parametrized, fully-explained path* to it — **earlier** in the curriculum (a Klasse-6
worksheet that genuinely teaches what the Klasse-8 Matura merely ticks off).

- The Matura is a **demand signal** — what must eventually be reachable, so anchoring to it
  guarantees curricular relevance — used *backward* to spec earlier material.
- It is **not a template** (we don't ship exam-style drill) and **not a ceiling** (worksheets
  may range well beyond it). The exam's format is the floor; our pedagogy is free above it.
- It **generalizes across subjects**: the SRDP endpoints + the standardized Operatoren are a
  province-wide, rights-clean (CC BY) demand map for every subject we generate. Maths is the
  first probe; the same mining should pay off for the sciences, GWB, languages, …

## Coverage today (`pipeline/parametrize.py`, correct-by-construction via sympy)

`linear_equation(_both_sides)` · `percentage(_rate)` · `proportion` · `fraction_add/multiply`
· `pythagoras` · `rectangle` · `linear_system_2/3` · `polynomial_curve` (Kurvendiskussion) ·
`definite_integral` · `binomial_distribution` · `vector_dot_angle` · `mean_median`.

## Gaps the corpus exposes (computational slice)

| Pri | Strand | Matura demand (example titles) | Status | Note |
|---|---|---|---|---|
| 1 | FA | **Exponential / growth-decay / compound interest** — Wachstum, Zerfallsprozess, Population, Jahreszinssatz, Wachstumsprozesse (FA 1.7/5.1) | ❌ | ubiquitous; trivial sympy |
| 2 | AN | **Differentiation atoms** — Tangentensteigung, Ableitungsfunktion, Regeln des Differenzierens | ❌ | have Kurvendiskussion, not the atoms |
| 2 | AN | **Rate of change** — mittlere/momentane Änderungsrate, Differenzenquotient (AN 1.1/1.3) | ❌ | sympy + Rechenweg |
| 3 | AG | **Analytic geometry of lines** — Geradengleichung, Parameterdarstellung, Normalvektor, Schnitt, parallel/normal | ❌ | extends `vector_dot_angle` |
| 4 | FA | **Trigonometric / Sinusfunktion** — amplitude·period·phase, Winkelfunktionen, Kreisbewegung | ❌ | |
| 4 | AG | **Quadratic equations** — solve, Diskriminante | ❌ | |
| 5 | WS | **Descriptive stats beyond mean/median** — Quartile/Boxplot, Standardabweichung | ⚠️ | `mean_median` partial |
| 5 | WS | **General probability** — Erwartungswert, diskrete Zufallsvariable, bedingte W., Laplace | ⚠️ | only `binomial_distribution` |

**Caveat:** a chunk of Teil 1 is *conceptual recognition* (ankreuzen „welche Zahl ist
rational“, „definiere die Winkelfunktionen“) — concept-MC, not computational, so not
parametric-recipe targets. The table is the computational slice, where the engine adds value.

## Recommended build order

1. **Exponential / growth-decay / compound interest** (FA) — highest frequency, cleanest.
2. **Differentiation atoms + rate of change** (AN).
3. **Analytic geometry of lines/vectors** (AG).
4. **Trigonometric functions** (FA), then **quadratic equations** (AG), then **stats/
   probability** rounding (WS).

Each is a `@_recipe` (sympy owns sampling + solving + the worked Rechenweg), turning a Matura
checkbox into N correct-by-construction, fully-explained variants for earlier grades. When we
pick one to build, a couple of accessible-version exams help pin the exact parameter ranges
and answer-format conventions for that topic.
