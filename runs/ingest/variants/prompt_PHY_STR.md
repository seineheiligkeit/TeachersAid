# Scope-Varianten: Physik — Strahlung und Radioaktivität

Erzeuge für **JEDEN** unten gelisteten Standard-Block je eine **compact**- und eine
**extended**-Variante. Gleiche Kompetenz, gleicher `kind`, gleiche `dimensions`, gleiches
`cognitive_level`, gleiches `serves` — es ändert sich nur der **Inhaltsumfang**:
- **compact**: auf den Kern reduziert, weniger Teilaufgaben, kürzere `est_minutes`.
- **extended**: reichhaltiger (mehr Teilschritte / Scaffolding / ein Beispiel), höhere `est_minutes`.
Deutsch, AHS-Niveau. In JSON-Strings: „…“ oder \" verwenden — nie ein nacktes " im Wert.

## Originalblöcke (Standard-Variante)

### phy-strahlung.str.t1  · kind=open_response · level=understand · dims=['W'] · serves=['PHY.US.4.STR.03'] · ~8 min
- prompt: Beim radioaktiven Zerfall kann man für ein einzelnes Atom nicht sagen, wann es zerfällt – für sehr viele Atome aber sehr genau, wie viele pro Sekunde zerfallen. Erkläre, warum das kein Widerspruch ist.
- answer_key: Zerfall ist ein Zufallsprozess pro Atom; über große Zahlen mittelt sich der Zufall zu einer stabilen Rate (Halbwertszeit) — Statistik, kein Plan.

### phy-strahlung.str.t2  · kind=create_produce · level=create · dims=['W'] · serves=['PHY.US.4.STR.04'] · ~12 min
- prompt: Entwirf eine kleine Info-Karte (5–6 Sätze) für jüngere Schüler:innen zu einer aktuellen Anwendung von Strahlung (z. B. PET im Krankenhaus, Bestrahlung von Lebensmitteln, C-14-Datierung). Erkläre Nutzen UND Grenze.

### phy-strahlung.str.t3  · kind=open_response · level=analyze · dims=['S', 'W'] · serves=['PHY.US.4.STR.02'] · ~6 min
- prompt: WLAN-Signale gehen durch Wände, schaden dir aber nicht – Gammastrahlung dagegen ist gefährlich. Beide durchdringen Materie. Erkläre den Unterschied.

### phy-strahlung.str.t4  · kind=true_false_justify · level=evaluate · dims=['S'] · serves=['PHY.US.4.STR.02'] · ~9 min
- prompt: Entscheide richtig/falsch und begründe oder korrigiere.
- answer_key: 1 falsch (UV schädigt Zellen trotz nicht-ionisierend) · 2 richtig · 3 falsch (Funkwellen, kein Kernzerfall)

### phy-strahlung.str.t5  · kind=open_response · level=analyze · dims=['S'] · serves=['PHY.US.4.STR.02'] · ~10 min
- prompt: Dosen zum Vergleich: 1 Banane ≈ 0,1 µSv · Thorax-Röntgen ≈ 20 µSv · Transatlantikflug ≈ 40 µSv · natürliche Jahresdosis in Österreich ≈ 2–3 mSv. Ordne 'eine Banane essen', 'einmal fliegen' und 'ein Jahr leben' nach Dosis und erkläre, warum Größenordnungen wichtiger sind als Bauchgefühl.

### phy-strahlung.str.t6  · kind=decision_scenario · level=evaluate · dims=['S'] · serves=['PHY.US.4.STR.02'] · ~11 min
- prompt: Eine Schlagzeile behauptet: 'Handystrahlung macht krank!'. Welche EINE Frage würdest du stellen, bevor du das glaubst – und warum entscheidet gerade diese Frage über die Glaubwürdigkeit?

### phy-strahlung.str.t7  · kind=experiment_protocol · level=apply · dims=['E'] · serves=['PHY.US.4.STR.02'] · ~22 min
- prompt: Versuch (mit Zählrohr): Miss die Zählrate in verschiedenen Abständen zu einer schwachen Schulquelle. Protokolliere Abstand und Zählrate und beschreibe, wie die Rate mit dem Abstand zusammenhängt.
- answer_key: Zählrate sinkt mit zunehmendem Abstand (näherungsweise Abstandsgesetz); Abstand ist eine einfache, wirksame Schutzmaßnahme.

## Ausgabe

Schreibe **ausschließlich** dieses JSON nach `runs/ingest/variants/PHY_STR.json` (kein Fließtext):
```json
[ {"original_id": "<id von oben>", "compact": <GenTaskBlock>, "extended": <GenTaskBlock>}, … ]
```
GenTaskBlock-Form (Schülertext ohne Kompetenz-IDs/„Lehrplan“):
{"role":"task","id":"<id>","kind":"<kind>","prompt":"…","payload":null,"response":{"mode":"lines","n":3},"cognitive_level":"<level>","dimensions":[…],"serves":[{"competence_id":"<id>","relation":"exercises"}],"est_minutes":<int>,"answer_key":"…","watch_outs":["…"]}