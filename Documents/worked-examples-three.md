# Three Worked Examples — at the content-object level

Three brainstorm ideas built into real `WorksheetContent`: actual blocks, real prompts, real answer
keys, anchored to real Lehrplan competences. No rendering — this is the object that *precedes* a PDF.
Each also exercises several **v0.4 deltas**, so building them doubles as a check that v0.4 is right.

Notation per block: `id · role/kind · cognitive_level · dimension(s) → serves`.

---

## 1 · "Listen to History" — Lebende Fremdsprache (Englisch), 3./4. Klasse (≈ B1)

*Listen to a famous English speech, then craft your own persuasive reply.* Worksheet language: **English**.

```yaml
meta:
  subject_models: [ "lebende_fremdsprache" ]
  klasse: 4
  content_language: en                 # v0.4 A5
  kernfrage: "How do great speakers make us feel and act — and can you do it too?"
  fassung: BGBl. II 204/2024
assets:
  - id: speech_audio
    medium: audio                       # v0.4 A3
    machine_generatable: false          # a real human speech — TTS would defeat the rhetoric lesson
    provenance: { source: "teacher-chosen famous English speech, 45–60 s excerpt",
                  rights: "cleared", note: "MUST be public-domain or licensed before use" }   # v0.4 B4
  - id: speech_transcript
    medium: visual
    provenance: { source: "transcript of the excerpt", rights: "cleared" }
```

| Block | content (real) | response | key / rubric |
|---|---|---|---|
| `e0` info/prose · — | "You'll hear part of a famous speech. First listen for the **big picture**, then for **detail**, then look at *how* it's built." | — | — |
| `e1` task/**listening_task** · understand · Hören → *Hörverstehen* | "Listen once, transcript closed. In one sentence: what does the speaker want the audience to **do or feel**?" `asset: speech_audio` | lines 1 | acceptable: any answer naming the persuasive intent/emotion |
| `e2` task/listening_task · apply · Hören | "Listen again. Tick everything the speaker actually does: ☐ addresses the audience directly ('you') ☐ repeats a key phrase ☐ names a problem ☐ paints a hopeful future ☐ tells a short story" | choices many | key: depends on clip; teacher fills from transcript |
| `e3` task/**text_analysis** · analyze · Lesen → *Leseverstehen* | "Now with the transcript: find **one repetition** and **one contrast** (e.g. *not X, but Y*). Why does each make the message stronger?" `asset: speech_transcript` | table 2×2 (Device / Why it works) | acceptable_reasoning: repetition = emphasis/memorability; contrast = makes the choice feel sharp/clear |
| `e4` task/**speaking_task** · create · Sprechen → *Zusammenhängendes Sprechen* · **modality: oral** | "Record a **30-second** persuasive reply about something *you* care about (more sport at school, later start times…). Use **at least one** device from the speech." | **artifact**: "30-sec audio recording" (v0.4 A4) | **rubric** (v0.4 A4): ▸ states a clear position ▸ uses ≥1 named device ▸ speaks fluently enough to follow ▸ range/accuracy appropriate to B1 — each ∈ {nicht erreicht / teilweise / erreicht} |

```yaml
teacher_watch_outs:
  - "Audio rights cleared before use (see provenance)."
  - "e4 is ORAL — it never appears on the printed sheet; it is assessed by the rubric, recorded on a phone/tablet."
  - "Weaker learners: offer sentence frames ('I believe… because… Imagine if…')."
derived:
  printable_coverage_note: "e4 (Sprechen) is the oral slice — exactly the modality the audit flagged."
```
**Demonstrates:** A3 audio, A4 artifact+rubric, A5 content_language, B4 provenance, oral modality.
**Scrutinize:** Is e3→e4 a real climb (analyze a device → use it)? Is the rubric the right way to assess
speaking, or too loose? Is "teacher-chosen clip" a cop-out, or correctly leaving rights/level to the pro?

---

## 2 · "Die geschönte Kurve" — Physik (Wetter & Klima, 4. Kl.) × Mathematik *(cross-curricular)*

*A real-data temperature graph, drawn to deceive — find the trick, then redraw it honestly.*

```yaml
meta:
  subject_models: [ "physik", "mathematik" ]      # v0.4 B5 — two models, primary first
  klasse: 4
  content_language: de
  kernfrage: "Kann eine Grafik mit echten Daten trotzdem lügen?"
assets:
  - id: trick_graph
    medium: visual
    machine_generatable: true                      # code-generated (correct-by-construction tooling)
    intentionally_flawed:                           # v0.4 B3 — wrong ON PURPOSE
      what: "y-Achse bei 13,8 °C abgeschnitten + nur 2012–2019 gezeigt → ~0,6 °C realer Anstieg wirkt dramatisch.
             Die Daten sind echt; die Darstellung täuscht. Pipeline darf das NICHT 'korrigieren'."
    provenance: { source: "reale Sommermittel-Temperaturen AT (GeoSphere Austria)", rights: "cleared",
                  note: "Daten verifizieren (Verification-Stage)" }
  - id: honest_graph    # teacher key only
    medium: visual
    machine_generatable: true
```

| Block | content (real) | response | key / reasoning |
|---|---|---|---|
| `k0` info/prose · — | "Diese Grafik kursiert online mit dem Titel **„Hitze außer Kontrolle!"**. Sie zeigt **echte** Messdaten — und täuscht trotzdem. Finde heraus, wie." `asset: trick_graph` | — | — |
| `k1` task/**data_interpretation** · analyze · Math:*Darstellen u. Interpretieren* → "Diagramme interpretieren" | "Lies ab: Wo **beginnt** die y-Achse? Um wie viel °C steigt die Kurve **tatsächlich** vom ersten zum letzten Jahr?" `asset: trick_graph` | lines 2 | key: y-Achse beginnt bei **13,8 °C** (nicht 0); realer Anstieg ≈ **0,6 °C** |
| `k2` task/open_response · analyze→evaluate · Physik:**S** → "Aussagen/Daten kritisch bewerten" | "Nenne **zwei Tricks**, mit denen diese Grafik täuscht." | lines 3 | acceptable: (1) **abgeschnittene y-Achse** übertreibt die Steigung; (2) **nur 8 Jahre** ausgewählt → kurzfristige Schwankung sieht aus wie dramatischer Trend (cherry-picking); (auch: reißerischer Titel) |
| `k3` task/**drawing** · create · Math:*Darstellen* + Physik:S | "Zeichne dieselben Daten **ehrlich**: y-Achse bei **0** beginnen, sachlich beschriften. Vergleiche mit **deiner Antwort aus k1** — wie ändert sich der Eindruck?" *(intra-sheet ref → k1, v0.4 B2)* | **drawing** (guide: leeres Achsenkreuz mit 0-Start) | key: dieselbe Linie wirkt jetzt **flach/leicht steigend**; der „dramatische" Eindruck verschwindet |
| `k4` task/decision_scenario · evaluate · Physik:S | "Heißt **„die Grafik täuscht"**, dass der Klimawandel **nicht echt** ist? Begründe." | lines 3 | acceptable_reasoning: **Nein.** Die Daten sind echt und zeigen real einen Anstieg — nur die **Darstellung** ist manipulativ. Eine schlechte Grafik widerlegt die Sache nicht. |

```yaml
teacher_watch_outs:
  - "trick_graph ist ABSICHTLICH falsch — nicht 'reparieren' lassen."
  - "Schlüssel-Nuance (k4): 'manipulative Darstellung ≠ Thema ist falsch'. SuS dürfen NICHT als Klima-Leugner herausgehen — diese Falle aktiv ansprechen."
  - "Daten echt halten (GeoSphere Austria); Verification-Stage."
derived:
  serves: { physik: "S / Wetter u. Klima", math: "Darstellen u. Interpretieren / Daten" }   # one sheet, two competence sources
```
**Demonstrates:** B3 intentionally-flawed asset, B5 cross-curricular dimensions, B1 drawing response,
B2 intra-sheet reference, code-generated content-bearing figure, contested-content handling.
**Scrutinize (physicist hat):** Is the critique exactly right (truncation exaggerates slope; short
window ≠ trend)? Is the k4 nuance correct and *sufficient* to prevent the denialist misread? Whose
`Nachweis`/Fassung governs when two subjects are served — both?

---

## 3 · "Baue ein unfaires Glücksspiel und tarne es" — Mathematik (Daten & Zufall, 2. Kl.)

*Design a game that looks fair but secretly favours one player — and prove the bias.*

```yaml
meta:
  subject_models: [ "mathematik" ]
  klasse: 2
  content_language: de
  kernfrage: "Wann ist ein Spiel wirklich fair — und wie versteckt man Unfairness?"
assets: []     # a 6×6 sum-grid template is generated inline (machine_generatable: true)
```

| Block | content (real) | response | key / rubric |
|---|---|---|---|
| `g0` info/prose+example · — | "Ein **faires** Spiel gibt beiden gleiche Gewinnchancen. Manche Spiele *sehen* fair aus, sind es aber nicht. Aufwärmen:" | — | — |
| `g1` info/example · — | "**Zwei Würfel**, die **Augensumme** zählt. **Anna** gewinnt bei Summe 5, 6, 7, 8, 9 — **Ben** bei 2, 3, 4, 10, 11, 12. Ben hat **mehr Zahlen** (6 gegen 5). Klingt fair für Ben?" | — | — |
| `g2` task/**table_fill** · apply · Operieren | "Trage in die 6×6-Tabelle alle Augensummen ein. Wie viele der 36 Kombinationen ergeben jede Summe?" | table 6×6 | key: Summen 6,7,8 am häufigsten (5,6,5 Wege); 2 und 12 je 1 Weg |
| `g3` task/calculation · analyze · Vermuten u. Begründen | "Wie oft gewinnt **Anna**, wie oft **Ben** (von 36)? Wer gewinnt öfter — **obwohl** Ben mehr Zahlen hat?" | lines 2 | key: **Anna 24/36 = ⅔**, **Ben 12/36 = ⅓** → Anna gewinnt **doppelt** so oft. *Mehr Zahlen ≠ bessere Chance.* |
| `g4` task/**create_produce** · create · Vermuten u. Begründen | "Erfinde **dein eigenes** Spiel, das **fair aussieht**, aber heimlich einen Spieler bevorzugt. Beschreibe die Regeln **und beweise** mit Häufigkeiten/Wahrscheinlichkeit, dass es unfair ist." | **artifact**: "beschriebenes Spiel + Beweis" (v0.4 A4) | **rubric** (v0.4 A4): ▸ wirkt auf den ersten Blick fair ▸ Unfairness ist **echt** (nicht nur behauptet) ▸ Begründung mit Häufigkeiten **korrekt** ▸ Regeln klar beschrieben — je ∈ {nicht erreicht / teilweise / erreicht} |
| `g5` task/open · evaluate · Vermuten u. Begründen · *(optional; social seed)* | "Tausche mit einer Mitschülerin: Findest du den **versteckten Trick** in ihrem Spiel?" | lines 2 | — *(peer step — see note)* |

```yaml
teacher_watch_outs:
  - "Häufiger Fehler: Ausgänge statt Summen zählen — die Summen müssen mit ihrer Anzahl an Wegen gewichtet werden (36 Kombinationen, nicht 11 Summen)."
  - "g4 ist offen → Rubric, kein Lösungsschlüssel; das ist Absicht (Niveau 'create')."
  - "g5 (Tausch) ist der KEIM eines Lernarrangements (v0.5, sozial) — im Arbeitsblatt bleibt es optional."
derived:
  depth_profile: { by_level: {apply:1, analyze:1, create:1, evaluate:1}, climbs_to: "create" }
```
**Demonstrates:** `create` level, A4 artifact+rubric, Daten & Zufall with correct probability, and a
visible **seam to v0.5** (the peer-swap is a worksheet task that "wants" interaction).
**Scrutinize:** Is the warm-up (24/36 vs 12/36) the right scaffold before the open create-task, or does
it hand away too much? Is a rubric enough to keep an open "create" task assessable and fair?

---

## What building these revealed
- **v0.4 holds.** Every delta got used in a real task and behaved — audio + rubric + content_language
  (Ex.1), intentionally-flawed asset + cross-subject + drawing + intra-sheet ref (Ex.2), artifact +
  create (Ex.3). No new field was needed that v0.4 doesn't already have.
- **The teacher-in-the-loop seam is exactly where auto-grading stops** — the oral reply, the redrawn
  graph, the invented game are all rubric/artifact, not answer-key. That is not a gap; it's the honest
  boundary of what a generator should grade, and it matches our posture.
- **One genuine open question** (from Ex.2): when a worksheet serves **two** subjects, whose `Nachweis`
  and which `Fassung` govern? Cleanest answer: the worksheet cites *both* competence sources and is
  stamped to both subjects' Fassung windows — but worth deciding explicitly when v0.4 is formalised.
- **The v0.5 seam is real, not theoretical** (Ex.3 `g5`): you can *see* the point where a single-learner
  worksheet wants to become a two-role interaction. That's the boundary the Lernarrangement picks up.
