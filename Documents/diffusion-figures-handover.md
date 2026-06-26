# Diffusion handover — CONTENT figures (educational illustrations) · TEST RUN

**Audience:** the SME's image-generation agent. This is a **deliberate experiment**, run in the
full human-in-the-loop stage, to gauge how well diffusion does on *educationally helpful*
illustrations — and where it hallucinates. It is **separate from, and stricter than, the decorative
handover** (`diffusion-handover.md`).

## Read this first — these figures are CONTENT-BEARING (they can be wrong)

Unlike decorative assets (which only have to be content-free), every figure below **teaches
something** — a labelled cell, a circuit, a force diagram, a historical scene. That means it **can be
factually wrong in ways a skim won't catch.** So:

- **Nothing here is cleared for use.** Each output is a *candidate* that a human subject expert must
  **fact-check against the "must be correct" note** before it could ever be used. The platform's
  media-policy gate will FLAG these (a content figure from diffusion is normally not allowed — that's
  the rule we're testing), so they enter an **`unverified` / experimental** lane, never the live library.
- **The point of the run is data:** how many come back correct, what kinds you get right (apparatus?
  scenes? labelled biology?), and how the failures look. So please **self-report uncertainty** (below).

## Hard rules

- **Avoid baked-in text.** Diffusion garbles text-in-images. Do **not** render the labels into the
  picture — we overlay labels/captions ourselves afterward. Generate the clean illustration; the
  `labels` list tells you what the figure must *depict* (so the parts are present and correct), not
  text to draw. If a figure is meaningless without a label, flag it rather than writing garbled text.
- **Respect the "must be correct" note** for each figure — those are the specific things a vetter will
  check (e.g. DNA right-handed; only one nail rusts; actio/reactio arrows on different bodies).
- **Style:** clean, neutral textbook illustration; flat or lightly shaded; clear, uncluttered; white/
  transparent background; palette near ink `#1f3a52` / accent `#b5651d` / green `#2e6b3a` where colour
  is free. Audience age ~10–14, Austrian/Central-European where a setting is implied. No real people,
  brands, or copyrighted characters.
- **Out of scope (do NOT generate):** anything that needs a *real* source (a real map, a real artwork,
  a real historical document/photo) — those are listed at the end as `sourced` and must come from a
  real source, not diffusion. Quantitative/geometric figures are handled by our code generators.

## Output

- One **PNG per id**, named exactly the id (e.g. `fig-bio-1.png`), RGBA, ~1024px long edge, no text overlay.
- Return the files + a short **per-figure self-report**: `confident` | `unsure` | `couldn't do correctly`,
  with one line on anything you think a vetter should look at hardest. That self-report is as valuable
  as the images.

## The review loop

outputs → a **content-vetting pass** (a subject expert checks each against its "must be correct" note)
→ only verified figures survive, and even then they live in a flagged lane until explicitly cleared.
Machine-readable list of all 33 test figures: `runs/ingest/figure_survey/diffusion_figures.json`.

---

# The 33 illustration candidates (the test set)


## Bewegung und Sport

### `fig-bus-2` — Fünf stilisierte Linienfiguren der Turnübungen aus t2: Rolle vorwärts (eingerollt), Handstandannäherung (Hände am Boden, Körper aufrecht), Liegestützposition, Strecksprung (Körper in der Luft gestreckt), Hang am Reck
- **Depict (parts that must be present):** A – Rolle vorwärts · B – Handstand (Annäherung) · C – Liegestützposition · D – Strecksprung · E – Hang am Reck
- **Must be correct (vetter checks):** Low. Figures must be anatomically plausible for the exercise; reviewer checks that body proportions and postures are correct (e.g. Handstand: arms vertical, body straight, NOT bent). No specific athlete depicted, no gender cues needed.
- **Caption (we add, not in image):** Fünf Turnübungen als Linienfiguren (A–E) zur Zuordnung der Bewegungsmerkmale in Aufgabe 2
- *Source:* c0007 — Turnen: Bewegungsmerkmale wahrnehmen und Feedback geben · s1/t2 — matching 5 Turnübungen (Rolle vorwärts, Handstand, Liegestützposition, Strecksprung, Hang) to Bewegungsmerkmalen


## Biologie

### `fig-bio-1` — Schematisches Chromosomenpaar (homologe Chromosomen): zwei identisch geformte Chromosomen nebeneinander, je ein Locus für das betrachtete Gen markiert, Allele beschriftet (z. B. B auf einem, b auf dem anderen), Herkunft (von Vater / von Mutter) mit Pfeil
- **Depict (parts that must be present):** Chromosom (väterlich) · Chromosom (mütterlich) · Gen-Locus (z. B. Augenfarbe) · Allel B (dominant) · Allel b (rezessiv) · Genotyp: Bb (heterozygot) · Centromer
- **Must be correct (vetter checks):** Chromosomenmorphologie: Vetter prüft Centromerlage (nicht immer in der Mitte — metazentrisch als didaktische Vereinfachung ok, aber nicht sublateral oder akrozentrisch darstellen ohne Hinweis); Anzahl der markierten Loci auf 1 beschränken (mehr Loci auf einem Chromosom würden die Abbildung überladen und ein falsches Bild von Gendichte geben).
- **Caption (we add, not in image):** Homologe Chromosomen tragen an derselben Position (Locus) je ein Allel — eines vom Vater, eines von der Mutter. Dieser Mensch ist heterozygot (Bb).
- *Source:* c0004 — Erbanlagen, DNA und Vererbungsregeln · s1/intro — 'DNA … in Abschnitte (Gene) unterteilt … Von jedem Gen zwei Varianten (Allele) — eine vom Vater, eine von der Mutter'

### `fig-bio-2` — Vollständig beschriftetes Kreuzungsschema (Punnet-Quadrat) für Gg × Gg mit vier Feldern, darüber und links die Elterngameten (G und g), Genotyp in jedem Feld, darunter Phänotyp-Legende: GG + Gg = gelbe Samen, gg = grüne Samen — als Referenz-Muster, das Schüler:innen für eigene Kreuzungen adaptieren
- **Depict (parts that must be present):** Gameten Vater: G / g · Gameten Mutter: G / g · GG (homozygot dominant — gelb) · Gg (heterozygot — gelb) · gg (homozygot rezessiv — grün) · Phänotyp-Verhältnis 3:1
- **Must be correct (vetter checks):** Punnet-Quadrate haben keine anatomische Fehlerquelle, aber didaktische: Vetter prüft, dass die Eltern-Gameten-Spalten/Zeilen eindeutig als Gameten (haploide Schreibweise G oder g, nicht GG/gg) beschriftet sind. Phänotyp-Farbcodierung (gelb für GG und Gg) darf nicht als Genotyp-Identität missverstanden werden.
- **Caption (we add, not in image):** Kreuzungsschema (Gg × Gg): Von vier möglichen Nachkommen-Genotypen sind drei gelb und einer grün — das klassische 3:1-Verhältnis nach Mendel.
- *Source:* c0004 — Erbanlagen, DNA und Vererbungsregeln · s2/t3 — 'Zwei heterozygote Pflanzen (Gg × Gg) werden gekreuzt … Kreuzungsschema ausfüllen'

### `fig-bio-3` — Hierarchische Einbettungs-Grafik (Zelle → Zellkern → Chromosom → DNA-Doppelhelix → Gen-Abschnitt) als 'zoom-in'-Schema mit fünf verschachtelten Darstellungsebenen und Dimensionsangaben
- **Depict (parts that must be present):** Zelle (~10 µm) · Zellkern · Chromosom · DNA-Doppelhelix · Gen (Abschnitt ~1000 Basenpaare) · Allel
- **Must be correct (vetter checks):** Größenverhältnisse sind bei vereinfachten Schemata immer irreführend. Vetter prüft: keine realistischen Größenverhältnisse suggerieren (nur symbolisch); Doppelhelix muss rechtsgängig gezeichnet sein (die meisten Lehr-Illustrationen sind korrekt, aber KI-Generationen verwechseln dies manchmal); DNA-Stränge müssen antiparallel sein — bei reiner Schemadarstellung ist dieser Fehler latent.
- **Caption (we add, not in image):** Von der Zelle zum Gen: Die DNA ist in Chromosomen verpackt und enthält Gene als funktionale Abschnitte — Allele sind verschiedene Varianten desselben Gens.
- *Source:* c0004 — Erbanlagen, DNA und Vererbungsregeln · s1/intro + t2 — 'DNA: langes Molekül im Zellkern … Gen: Abschnitt der DNA … Chromosom: fadenförmige Struktur im Zellkern'


## Chemie

### `fig-che-1` — Querschnitt einer brennenden Kerze: Docht, Schmelzzone (flüssiges Wachs), Verdampfungszone, leuchtende Flamme mit Bereichen beschriftet (Reaktionszone, Verbrennungsprodukte CO₂ + H₂O oben), Sauerstoffzufuhr von den Seiten
- **Depict (parts that must be present):** Docht · flüssiges Wachs (Schmelzzone) · Wachsdampf · Reaktionszone (O₂ + Wachsdampf) · CO₂ + H₂O (Reaktionsprodukte) · Luft (Sauerstoffzufuhr)
- **Must be correct (vetter checks):** Flammengeometrie ist vereinfacht. Vetter prüft: innerer dunkler Bereich (unverbrannter Dampf) muss erkennbar sein; äußerer leuchtender Bereich (vollständige Verbrennung) separat beschriftet; Sauerstoffpfeile zeigen von außen nach innen (nicht von unten — Konvektion nicht falsch dargestellt).
- **Caption (we add, not in image):** Querschnitt einer Kerzenflamme: Nicht das Wachs selbst brennt, sondern der verdampfte Wachsdampf, der in der Reaktionszone mit Sauerstoff reagiert.
- *Source:* c0078 — Verbrennung, Rost und Licht — Chemische Reaktionen erkennen und beschreiben · s1/t2 — 'Kerzenverbrennung … Wachs verdampft … reagiert mit Sauerstoff … Wärme und Licht'

### `fig-che-2` — Beschriftete Darstellung von drei nebeneinanderstehenden Reagenzgläsern mit je einem Eisennagel: (1) Nagel + Wasser + Luft → Rost sichtbar, (2) Nagel + Trockenmittel (kein Wasser) → kein Rost, (3) Nagel + abgekochtes Wasser (kein O₂) + Ölschicht → kein Rost
- **Depict (parts that must be present):** Reagenzglas 1: Wasser + Luft → rostet · Reagenzglas 2: Trockenmittel (CaCl₂) → kein Rost · Reagenzglas 3: abgekochtes Wasser + Öl → kein Rost · Eisennagel · Ölschicht (O₂-Barriere)
- **Must be correct (vetter checks):** Rost-Darstellung: Vetter prüft, dass nur Reagenzglas 1 Rostfarbe (braun-orange) am Nagel zeigt — nicht alle drei. Öl-Schicht in Glas 3 muss klar als Sauerstoffbarriere erkennbar sein (Schichtung). Beschriftung muss die Variable (Wasser / Sauerstoff) klar benennen, nicht nur das Ergebnis.
- **Caption (we add, not in image):** Drei-Bedingungen-Versuch zur Rostbildung: Nur bei gleichzeitiger Anwesenheit von Wasser und Sauerstoff rostet der Eisennagel (Glas 1).
- *Source:* c0078 — Verbrennung, Rost und Licht — Chemische Reaktionen erkennen und beschreiben · s1/t6 — 'Eisennägel in drei Reagenzgläsern … Wasser + Luft / kein Wasser / kein Sauerstoff … Rostbildung vergleichen'

### `fig-che-3` — Zwei nebeneinander gestellte Bohr-Schalenmodelle: Natrium (Na, Z=11) mit 2+8+1 Elektronen auf drei Schalen; Chlor (Cl, Z=17) mit 2+8+7 Elektronen auf drei Schalen — Pfeil zeigt Elektronenübertragung von Na-Valenzschale zu Cl-Valenzschale, Produkte Na⁺ und Cl⁻ beschriftet
- **Depict (parts that must be present):** Na (Z=11): 2 / 8 / 1 · Cl (Z=17): 2 / 8 / 7 · Valenzelektron wird abgegeben · Na⁺ (Edelgaszustand: 8 VE) · Cl⁻ (Edelgaszustand: 8 VE) · Neon-Konfiguration · Argon-Konfiguration
- **Must be correct (vetter checks):** Elektronenzahlen pro Schale sind exakt bekannt — kein Halluzinationsrisiko für die Zahlen selbst. Vetter prüft: Schalenbesetzung nach Aufbauprinzip (2/8/8-Regel korrekt angewendet); Pfeilrichtung (von Na zu Cl, nicht umgekehrt); Ladungszeichen (Na⁺, Cl⁻) korrekt eingezeichnet.
- **Caption (we add, not in image):** Elektronenübertragung bei der Bildung von Natriumchlorid: Natrium gibt sein Valenzelektron ab, Chlor nimmt es auf — beide erreichen die stabile Edelgaskonfiguration mit 8 Außenelektronen.
- *Source:* c0079 — Atome, Elektronen und das Periodensystem — Bausteine der Materie verstehen · s1/t3 + t4 — 'Proton, Neutron, Elektron, Atomhülle, Valenzelektronen … Na gibt 1 Valenzelektron ab … Cl nimmt es auf'


## Deutsch

### `fig-deu-1` — Abstract atmospheric illustration evoking 'the feeling of reading poetry': an open book with soft light radiating, surrounded by floating word-shapes (no readable words — abstract letter-fragment silhouettes only), autumn leaves or similar evocative natural elements.
- **Depict (parts that must be present):** poetry · atmosphere · reading · abstract
- **Must be correct (vetter checks):** low — fully abstract; no factual referent; no text needed in image
- **Caption (we add, not in image):** Lyrik entdecken — was löst ein Gedicht in dir aus?
- *Source:* c0013 — Lyrik entdecken: Sprache, Rhythmus und eigene Lesarten · worksheet intro / t1 area — the entire worksheet is built around pupils encountering and responding to a poem. No existing visual anchor.

### `fig-deu-2` — A simple three-panel comic-strip showing the structure of an argument: panel 1 = a figure stating a bold position (speech bubble blank/empty); panel 2 = same figure offering a reason with a second figure listening; panel 3 = a third figure raising a counter-point. No text in bubbles.
- **Depict (parts that must be present):** argumentation · diagram · three-move · comic
- **Must be correct (vetter checks):** low — abstract process illustration; speech bubbles intentionally blank; no text required in image
- **Caption (we add, not in image):** These — Argument — Gegenargument: So ist ein Argument aufgebaut.
- *Source:* c0011 — Argumentieren und informierendes Schreiben: Meinungen begründen · t3 — 'Wähle eine der folgenden Thesen und schreibe dazu zwei Argumente und ein Gegenargument: „In der Schule sollte mehr Sport angeboten werden.“ / „Smartphones sollten im Unterricht erlaubt sein.“ / „Schüler:innen sollten ihre Noten mitbestimmen dürfen.“'


## Erste lebende Fremdsprache

### `fig-fs1-1` — Simple top-down school grounds map showing main entrance, a left turn, a straight path, a car park on the right, and a sports hall behind it — no labels, or labels in neutral icons only (no English text in the image)
- **Depict (parts that must be present):** route · school-grounds · top-down · spatial
- **Must be correct (vetter checks):** low — generic layout, no real place, no text in image
- **Caption (we add, not in image):** Schulgelände: Finde den Weg zur Sporthalle.
- *Source:* c0050 — Anweisungen und Auskünfte verstehen · t3 — 'To get to the sports hall, first go out of the main entrance. Then turn left and walk straight ahead for about two minutes. You will see a big car park on your right.'

### `fig-fs1-2` — Two teenagers in a casual school setting (corridor or classroom doorway) facing each other mid-conversation — one gesturing to speak, the other attentive. No speech bubbles, no text in image.
- **Depict (parts that must be present):** speaking · peer-conversation · school-corridor
- **Must be correct (vetter checks):** low — generic scene, no text, no culturally specific markers needed
- **Caption (we add, not in image):** Sich vorstellen — stell dich deiner Partnerin / deinem Partner vor.
- *Source:* c0053 — Sich vorstellen und über sich sprechen · t4 — 'Prepare a short self-introduction (5–7 sentences). Include: Your name and age / Where you live / family / Your favourite subject / One hobby or interest / A closing sentence. Practise saying it ALOUD first.'

### `fig-fs1-3` — A collage-style vignette: a teenager at a desk looking at a glowing screen that shows a distant snow-capped mountain range and a silhouette of ancient columns — dreamy, slightly wistful atmosphere. No text on screen, no brand logos.
- **Depict (parts that must be present):** reading · emotions · travel-dream · teenager
- **Must be correct (vetter checks):** low — generic dreamy scene; no real place, no text required in image
- **Caption (we add, not in image):** Emma träumt von fernen Ländern — was fühlt sie dabei?
- *Source:* c0051 — Wünsche und Gefühle in Texten erkennen · i1 — Emma's pen-pal letter: 'My big dream is to travel. I have never been outside the UK and I want to see mountains, ancient cities, and maybe try food I have never heard of. I follow lots of travel accounts online, but looking at other people's photos makes me feel both excited and a little sad at the same time.'


## Geographie und wirtschaftliche Bildung

### `fig-gwb-1` — Schematischer Wirtschaftskreislauf: drei Akteure (Haushalte, Unternehmen, Staat) mit beschrifteten Pfeilen für Geld- und Güterflüsse
- **Depict (parts that must be present):** Haushalte · Unternehmen · Staat · Arbeit · Löhne · Steuern · öffentliche Leistungen
- **Must be correct (vetter checks):** Pfeile könnten falsch gerichtet sein (z.B. Güterfluss vs. Geldfluss verwechselt); OeNB und Sozialpartner nicht im Kern-Dreieck — Vetter muss Vollständigkeit und Pfeilrichtungen prüfen.
- **Caption (we add, not in image):** Abb. X: Der einfache Wirtschaftskreislauf — Haushalte, Unternehmen und Staat im Zusammenspiel
- *Source:* c0080 — Preise und Märkte in Österreich · t6 — 'Den Wirtschaftskreislauf vereinfacht skizzieren: Haushalte (Arbeit + Konsum) ↔ Unternehmen (Güter + Löhne) ↔ Staat (Steuern + Leistungen).'

### `fig-gwb-2` — Stilisierte Querschnittskizze einer wachsenden Megastadt: Stadtzentrum mit Hochhäusern, angrenzende informelle Siedlungen (Wellblechhütten) am Rand, sichtbarer Kontrast in Bebauungs- und Infrastrukturdichte
- **Depict (parts that must be present):** Stadtzentrum · Wohnviertel · informelle Siedlung · keine Wasserversorgung · keine Schulen
- **Must be correct (vetter checks):** Gefahr der stereotypen Darstellung von Städten im Globalen Süden als rückständig; Vetter muss sicherstellen, dass die Illustration nicht diskriminierend wirkt und beide Pole (auch die Chancen der Stadt) zeigt oder zumindest nicht einseitig negativ konnotiert.
- **Caption (we add, not in image):** Abb. X: Wachstum einer Großstadt im Globalen Süden — Stadtzentrum und informelle Siedlung im Vergleich (schematisch)
- *Source:* c0081 — Weltbevölkerung und Urbanisierung · t5 — 'Szenario: Eine Großstadt in einem ärmeren Land wächst so schnell, dass Trinkwasser, Schulen und öffentliche Verkehrsmittel nicht mehr für alle reichen.'

### `fig-gwb-3` — Vogelperspektivskizze einer österreichischen Kleingemeinde (ca. 2000 Einwohner) mit Dorfkern, Wohnhäusern, Feldern am Rand — drei überlagerte Symbole für die drei Maßnahmen (Windrad, gedämmtes Haus mit Heizsymbol, Busroute)
- **Depict (parts that must be present):** Windpark (A) · Wärmedämmung (B) · Busnetz (C) · Wohngebiet · Ortsrand
- **Must be correct (vetter checks):** Symbole müssen neutral und eindeutig zuordnungsfähig sein. Kein Risiko falscher Fakten, da rein schematisch. Vetter prüft, ob Windrad-Symbol nicht übermäßig dominant oder negativ wirkt.
- **Caption (we add, not in image):** Abb. X: Drei Maßnahmen für eine klimaneutrale Gemeinde — Wo würden sie wirken? (schematisch)
- *Source:* c0082 — Energie und Klimawandel · t6 — 'Szenario: Eine österreichische Gemeinde will bis 2035 klimaneutral werden… (A) Windpark… (B) Wärmedämmung… (C) Busnetz'

### `fig-gwb-4` — Schematische Darstellung des österreichischen Bildungswegsystems nach der 4. Klasse AHS: Matura → Universität/FH/PH, Lehre → Berufsschule/Betrieb, BMS/BHS-Alternativen — als Baumdiagramm oder Flussdiagramm
- **Depict (parts that must be present):** Matura · Universität · Fachhochschule · Lehrausbildung · BHS · Berufseinstieg
- **Must be correct (vetter checks):** Österreichisches Bildungssystem ändert sich gelegentlich. Vetter prüft, ob aktuelle Bezeichnungen korrekt sind (z.B. BAfEP, HTL, HAK als BHS-Typen); keine erfundenen Institutionen.
- **Caption (we add, not in image):** Abb. X: Bildungswege in Österreich nach der AHS-Unterstufe (vereinfachte Übersicht)
- *Source:* c0033 — Berufe, Bildungswege und Arbeitsleben in Österreich · GWB.US.3.BIL.01 — Bildungswege nach der AHS; das Arbeitsblatt behandelt Bildungswege und Berufsbilder in Österreich

### `fig-gwb-5` — Schematische Karte Europas (stilisiert, nicht als Realatlas) mit den vier Grundfreiheiten als Pfeil-Overlays — Waren-LKW, Personen-Silhouette, Geldpfeil, Dienstleistungs-Symbol über einem vereinfachten EU-Umriss
- **Depict (parts that must be present):** Waren · Personen · Kapital · Dienstleistungen
- **Must be correct (vetter checks):** Karte muss aktuelle EU-Mitgliedsstaaten zeigen (z.B. kein UK nach Brexit). Vetter prüft EU-Grenzen und stellt sicher, dass keine Nicht-Mitglieder als EU dargestellt werden.
- **Caption (we add, not in image):** Abb. X: Die vier Grundfreiheiten der EU — freier Verkehr über Grenzen hinweg (schematisch)
- *Source:* c0034 — Die Europäische Union: Werte, Grundfreiheiten und Herausforderungen · GWB.US.4.EUR.02 — 'vier Grundfreiheiten (Waren, Personen, Kapital und Dienstleistungen)' im Hinblick auf das eigene Leben reflektieren

### `fig-gwb-6` — Stilisierter Stadtplan-Ausschnitt eines fiktiven österreichischen Stadtviertels: Schule markiert, Wohnblöcke, Platz, Supermarkt — mit eingezeichneter Himmelsrose und Maßstabsbalken
- **Depict (parts that must be present):** Schule · Supermarkt · Park · Wohnhaus · N/S/O/W
- **Must be correct (vetter checks):** Kein Risiko falscher Fakten, da fiktiv. Vetter prüft nur ob Legende konsistent und Maßstabsbalken plausibel ist.
- **Caption (we add, not in image):** Abb. X: Stadtplan-Ausschnitt (fiktiv, M 1:5 000) — Übe deine Orientierung!
- *Source:* c0030 — Bedürfnisse, Geld und mein Wohnort · t4 — 'Beschreibe in 4–5 Sätzen, wie du von deiner Wohnung zur Schule kommst. Nenne dabei mindestens zwei Orientierungspunkte'


## Geschichte und politische Bildung

### `fig-gpb-1` — Vereinfachte Rekonstruktionszeichnung eines ägyptischen Grabwandreliefs: Pharao in Triumphpose mit Bogen, stilisierte Feinde — mit sichtbarer Hieroglyphen-Begleitung am Rand, in grafischer Stilisierung (nicht fotorealistisch)
- **Depict (parts that must be present):** Pharao · Feinde · Hieroglyphen (Beischrift) · — Diese Darstellung ist eine Quelle. Was zeigt sie? Was zeigt sie nicht?
- **Must be correct (vetter checks):** Anachronismen im Bildstil möglich (falsche Rüstung, moderne Proportionen). Vetter — idealerweise mit Ägyptologie-Wissen — prüft ob Figurenkanon (Frontalsicht Augen/Schultern, Seitenansicht Beine) und typische Attribute (Doppelkrone, Bogen) korrekt stilisiert sind. Keine Verwechslung mit spezifischem historischen Ereignis.
- **Caption (we add, not in image):** Abb. X: Stilisierte Rekonstruktionszeichnung eines ägyptischen Triumphreliefs — Was zeigt diese Darstellung, und was lässt sie offen?
- *Source:* c0025 — Leben am Nil: Wie wissen wir, was wir über das Alte Ägypten zu wissen glauben? · t1 — 'Ein Forscher findet in einem ägyptischen Grab ein Wandbild, das einen Pharao beim Besiegen seiner Feinde zeigt.'

### `fig-gpb-2` — Stilisierter Propagandaentwurf: ein einfaches, schwarz-weiß gehaltenes Kinderbuchbild im Stil von 1914–1918 — Soldat mit Gewehr winkt, Kinder jubeln mit erhobenen Händen, vereinfachte Linienzeichnung ohne Gewaltdarstellung
- **Depict (parts that must be present):** — Welche Mittel nutzt dieses Bild, um Begeisterung zu erzeugen?
- **Must be correct (vetter checks):** Gefahr, unbeabsichtigt tatsächliche Kriegsverherrlichung zu reproduzieren. Vetter muss prüfen: Keine erkennbaren Uniformen echter Armeen, keine Flaggen mit historischer Spezifizität (kein k.u.k. Adler). Stilisiert genug, dass es als Beispiel-Objekt erkennbar ist, nicht als Authentikum.
- **Caption (we add, not in image):** Abb. X: Typische Kriegspropaganda für Kinder im Ersten Weltkrieg — stilisierte Illustration (kein historisches Original)
- *Source:* c0026 — Krieg als Helden-Abenteuer? Wie Kinder und Jugendliche im Ersten Weltkrieg den Krieg erleben sollten · t1 — 'Lies diesen Auszug aus einem österreichischen Schullesebuch für Volksschulen, erschienen 1915'

### `fig-gpb-4` — Schematische Darstellung einer Migrationsbiografie: Ausgangspunkt (Dorf/Stadt im Herkunftsland) → Grenzübergang → Ankunft (Fabrik/Stadtviertel im Zielland). Push-Symbole links (Dürre, Bomben, Armut-Symbol), Pull-Symbole rechts (Arbeit, Familie, Schule-Symbol). Stilisierte Silhouetten, kein spezifisches Land.
- **Depict (parts that must be present):** Herkunftsland · Zielland · Push: Armut / Krieg / Verfolgung · Pull: Arbeit / Familie / Sicherheit
- **Must be correct (vetter checks):** Keine spezifischen Nationalitäten oder Ethnien. Vetter prüft auf stereotypisierende Symbole (z.B. kein Schlauchboot — das würde eine bestimmte Fluchtroute implizieren). Symbole müssen für viele Migrationsformen anwendbar bleiben.
- **Caption (we add, not in image):** Abb. X: Migration — Warum brechen Menschen auf? Push- und Pull-Faktoren (schematisch)
- *Source:* c0028 — Aufbrechen, Ankommen, Dazugehören: Was bedeutet Migration gestern und heute? · t4 — Vergleichstabelle Arbeitsmigration vs. Flucht; teacher_overview — 'Push-Faktoren vs. Pull-Faktoren: kaum eine Migrationsentscheidung ist entweder/oder'

### `fig-gpb-7` — Stilisierte Illustration einer Wiener Wohnküche um 1915: Frau am Herd, Brief auf dem Tisch, Zeitungsseite mit Kriegsmeldungen sichtbar, spartanisches Mobiliar — Heimatfront-Atmosphäre ohne Gewaltdarstellung
- **Depict (parts that must be present):** Kachelofen · Brief vom Vater · Zeitung (Kriegsmeldungen)
- **Must be correct (vetter checks):** Anachronismen möglich: elektrisches Licht gab es in Wien 1915 teilweise bereits (Gaslampen vs. Strom je nach Viertel). Keine spezifischen Uniformen oder erkennbaren Personen. Vetter mit Wien-1915-Kenntnissen prüft Details der Ausstattung. Kein Risiko erfundener Fakten, da fiktive Szene.
- **Caption (we add, not in image):** Abb. X: Wiener Wohnküche um 1915 — Alltag an der Heimatfront (stilisierte Illustration)
- *Source:* c0026 — Krieg als Helden-Abenteuer? Wie Kinder und Jugendliche im Ersten Weltkrieg den Krieg erleben sollten · t6 — 'Du sollst einen kurzen eigenen Text schreiben aus der Perspektive eines 12-jährigen Mädchens, das in Wien 1915 lebt'


## Latein

### `fig-lat-1` — Cutaway or simplified isometric view of a Roman domus showing: entrance corridor (fauces), atrium with impluvium (small pool), tablinum (master's room opening off atrium), and garden (hortus) at the rear. Figures at scale for proportion but not labelled in the image itself.
- **Depict (parts that must be present):** Roman-domus · atrium · architecture · culture-context
- **Must be correct (vetter checks):** medium — architectural illustration has factual content; vetter must check impluvium placement is correct and no anachronistic details (electricity, modern furniture) slip in
- **Caption (we add, not in image):** Eine römische Domus: Das Atrium mit Impluvium im Zentrum des Hauses.
- *Source:* c0062 — Römisches Alltagsleben: Die Familie und das Haus · t1 — 'Marcia et Marcus in Roma habitant ... Filius eorum Quintus in ludo discit. Filia eorum Claudia domi manet. Servus aquam portat.' / t3 — 'Was ist ein Atrium in einem römischen Haus? ... Das Atrium war der zentrale offene Innenhof des römischen Hauses, oft mit einem Wasserbecken — dem impluvium.'

### `fig-lat-2` — A Roman child at a wooden writing tablet (tabula cerata) — sitting cross-legged on a low bench in a simply furnished Roman room, stylus in hand, concentrating. Through an arched doorway in the background, an atrium/garden is just visible.
- **Depict (parts that must be present):** Roman-daily-life · child · writing · empathy
- **Must be correct (vetter checks):** low-medium — Roman setting, no factual claims; vetter checks: no anachronisms, correct stylus/tablet prop, not a realistic photo of a child
- **Caption (we add, not in image):** Quintus oder Claudia schreibt einen Brief — wie sah ein Tag in einer römischen Familie aus?
- *Source:* c0062 — Römisches Alltagsleben: Die Familie und das Haus · t6 — 'Stell dir vor, du bist Quintus (oder Claudia) und schreibst einen kurzen Brief an einen Freund in Griechenland. Beschreibe deinen Alltag in der römischen Familie in 4–5 deutschen Sätzen.'

### `fig-lat-3` — Three simple comic-strip panels illustrating the three sentences: (1) a girl looking at a slave figure; (2) a man walking onto/entering a wide road; (3) a man gesturing approvingly toward a girl. Stick-figure or line-art style — no text inside the panels.
- **Depict (parts that must be present):** grammar · Nominativ · Akkusativ · comic-panels · action-scene
- **Must be correct (vetter checks):** low — line-art action panels; no factual claims; vetter checks: consistent simple Roman tunic style, no anachronisms, actions clearly directional
- **Caption (we add, not in image):** Wer handelt? Wer wird betroffen? Erkenne Nominativ und Akkusativ in den Bildern.
- *Source:* c0060 — Nomen und Kasus: Nominativ und Akkusativ · t3 — 'Übersetze die folgenden lateinischen Sätze ins Deutsche. Unterstreiche dabei das Subjekt (Nominativ) und kreise das Objekt (Akkusativ) ein. 1. Puella servum videt. 2. Servus viam longam intrat. 3. Dominus puellam laudat.'


## Physik

### `fig-phy-1` — Schematischer Querschnitt Erde–Atmosphäre mit beschrifteten Strahlungspfeilen: kurzwellig (Sonne→Boden), langwellig (Boden→Atmosphäre), Rückstrahlung (Atmosphäre→Boden), reflektierter Anteil ins All
- **Depict (parts that must be present):** Sonnenstrahlung (kurzwellig) · Reflexion · Absorption (Boden) · Infrarotstrahlung (langwellig) · Treibhausgase (CO₂, H₂O, CH₄) · Rückstrahlung · Temperaturerhöhung
- **Must be correct (vetter checks):** Pfeildichte und -breite können falsche Mengenverhältnisse suggerieren (z. B. zu viel Reflexion). Vetter muss prüfen: Rückstrahlung in beide Richtungen (nicht nur nach unten); Atmosphärenschicht nicht zu dick/dünn; Ozonschicht nicht mit Treibhausgasschicht verwechselt darstellen.
- **Caption (we add, not in image):** Natürlicher Treibhauseffekt: Sonnenlicht (kurzwellig) erreicht die Erdoberfläche; diese gibt Wärmestrahlung (langwellig) ab, die Treibhausgase teilweise zurückwerfen.
- *Source:* c0088 — Treibhauseffekt, Energiehaushalt und Klimaschutz · info1 / t1 — 'Kurzwellige Sonnenstrahlung … Infrarotstrahlung … Treibhausgase absorbieren … strahlen zurück'

### `fig-phy-2` — Vereinfachter Stromkreis-Schaltplan: Netz (230 V, Phase + Nullleiter), Mensch als Widerstand (R_Körper), Erdanschluss — zeigt den geschlossenen Stromkreis durch den Körper beim Berühren einer Leitung
- **Depict (parts that must be present):** Phase (L) · Nullleiter (N) · R_Körper (trocken ~5000 Ω, nass ~1000 Ω) · Erde · I (gefährlich ab 30 mA)
- **Must be correct (vetter checks):** Schaltplan muss physikalisch korrekt sein: Stromfluss Phase→Körper→Erde (nicht N→Körper). Vetter prüft: Pfeilrichtung des konventionellen Stroms; Schutzleiter (PE) separat von N darstellen, um FI-Schalter-Wirkung nicht vorwegzunehmen.
- **Caption (we add, not in image):** Wie schließt sich der Stromkreis durch den Körper? Bei Berühren der Phase fließt Strom von Phase durch den Körper zur Erde.
- *Source:* c0086 — Spannung, Strom und Schutz im Stromkreis · s2/info1 + t3 — 'Der menschliche Körper leitet elektrischen Strom … Widerstand … 230 V / 1000 Ω = 230 mA'

### `fig-phy-3` — Schematische Darstellung des Elektronengasmodells: Metallgitter (positiv geladene Ionenrümpfe als Kreise angeordnet), freie Elektronen als Punkte zwischen den Gitterplätzen, Pfeil für Driftbewegung der Elektronen in Feldrichtung, Stoß-Symbol an einem Gitterpunkt
- **Depict (parts that must be present):** Metallion (positiv) · freies Elektron · Driftrichtung (Strom) · Stoß → Erwärmung · Gitterpunkt
- **Must be correct (vetter checks):** Das Modell vereinfacht stark: Elektronen bewegen sich nicht geradlinig zwischen Stößen. Vetter prüft: Elektronen nicht als 'Faden' darstellbar — mehrere ungerichtete Elektronen zeigen; Drift-Pfeil nur als Nettorichtung; Modell gilt nur für Metalle — kein Halbleiter-Kontext.
- **Caption (we add, not in image):** Das Elektronengasmodell: Freie Elektronen stoßen mit den Gitterionen — das überträgt Energie (Erwärmung) und ist die Ursache des elektrischen Widerstands.
- *Source:* c0086 — Spannung, Strom und Schutz im Stromkreis · s3/t5 + teacher_overview — 'Elektronengasmodell: frei bewegliche Elektronen im Metallgitter … Stöße → Erwärmung'

### `fig-phy-4` — Kräftediagramm eines bremsenden Fahrrads: Fahrrad-Silhouette von der Seite, Kraftpfeile am Rad-Boden-Kontaktpunkt: Bremskraft (rückwärts, auf Reifen), Gegenkraft (vorwärts, auf Straße); Gewichtskraft (senkrecht nach unten), Normalkraft (senkrecht nach oben)
- **Depict (parts that must be present):** Bremskraft (rückwärts auf Reifen) · Gegenkraft auf Straße (Reaktion) · Gewichtskraft (mg) · Normalkraft (N) · Fahrtrichtung
- **Must be correct (vetter checks):** Pfeilgröße und -position sind kritisch: Bremskraft und Reaktionskraft müssen gleich groß (actio = reactio) und an verschiedenen Körpern angreifen. Vetter prüft: Bremskraft greift am Reifen (nicht am Fahrrad-Rahmen) an; Wechselwirkungspfeil auf der Straße, nicht auf dem Fahrrad — sonst wird das Gesetz falsch gelesen.
- **Caption (we add, not in image):** Kräfte beim Bremsen: Die Straße bremst den Reifen (Reibungskraft rückwärts) — und nach dem Wechselwirkungsgesetz drückt der Reifen gleichzeitig vorwärts auf die Straße.
- *Source:* c0087 — Kräfte, Bewegung und das Anhalten eines Fahrzeugs · s3/t5 + extensions — 'Wechselwirkungsgesetz … Straße übt auf Reifen Reibungskraft rückwärts aus … Kraftpfeil-Diagramm'


## Zweite lebende Fremdsprache

### `fig-fs2-1` — A warm French pavement café scene: small round tables with chairs, a waiter figure approaching, a menu-board visible in the background but with no readable text — just chalk-mark shapes suggesting a list. Sunny street backdrop.
- **Depict (parts that must be present):** speaking · café · France · roleplay
- **Must be correct (vetter checks):** low — generic café; no text in image required; menu board deliberately illegible
- **Caption (we add, not in image):** Au café — Bestellst du bitte für uns beide?
- *Source:* c0058 — Au café et en ville — Im Alltag auf Französisch kommunizieren · t3 — 'Partnerübung: Spielt ein Gespräch im Café nach. Eine Person ist Kellner:in, die andere ist Gast ... Wählt mindestens 3 Dinge aus dieser Getränkekarte: Un café — 2,50 € | Un thé — 2,00 € | Un jus d'orange ...'

### `fig-fs2-2` — A generic Parisian street corner scene viewed from pedestrian eye-level: a wide pavement, a street stretching straight ahead, a crossing, and a figure pointing left. Landmark-free — no visible Eiffel Tower in frame (the destination is around the corner).
- **Depict (parts that must be present):** speaking · directions · street-scene · Paris-generic
- **Must be correct (vetter checks):** low-medium — Paris is named in the task; street should be 'Haussmann-style generic city' with no text on buildings; vetter checks no accidental landmarks are wrong
- **Caption (we add, not in image):** Entschuldigung, wie komme ich zum Eiffelturm?
- *Source:* c0058 — Au café et en ville — Im Alltag auf Französisch kommunizieren · t4 — 'Du bist in Paris und fragst jemanden nach dem Weg zum Eiffelturm. Die Person antwortet: Alors, vous allez tout droit, puis vous tournez à gauche et c'est à cinq minutes à pied.'

### `fig-fs2-3` — Two teenagers side by side in a friendly first-meeting pose — one holding a small football, the other with headphones around her neck. City skylines visible but not identifiable in the background.
- **Depict (parts that must be present):** listening · characters · introduction · A1
- **Must be correct (vetter checks):** low — generic characters; no text; no specific city required
- **Caption (we add, not in image):** Wer ist wer? Emma und Lucas stellen sich vor.
- *Source:* c0055 — Wer bist du? — Kurze Dialoge verstehen · t2 — '[Teacher reads:] Bonjour ! Je m'appelle Emma. J'ai treize ans. J'habite à Vienne. Mon hobby, c'est la musique. — Salut Emma ! Moi, c'est Lucas. J'ai quatorze ans. J'habite à Graz. J'aime le football.' [pupils fill a table: Prénom / Âge / Ville / Hobby]

### `fig-fs2-4` — A simple, warm family scene: two adults and two children of varied ages sitting together at a table or in a garden. Generic and inclusive — no specific cultural markers, no single 'ideal' family model. No text anywhere.
- **Depict (parts that must be present):** writing · family · context-illustration · A1
- **Must be correct (vetter checks):** low — generic family scene; vetter checks for diverse representation and absence of specific cultural markers
- **Caption (we add, not in image):** Ma famille — schreibe über deine Familie auf Französisch.
- *Source:* c0057 — Ma famille et mes loisirs — Über Familie und Hobbys schreiben · t3 — 'Schreibe 4–5 Sätze auf Französisch über deine Familie. Benutze die Satzanfänge: Dans ma famille, il y a... / Ma mère / Mon père s'appelle... / J'ai un frère / une sœur. Il/Elle a ... ans.'


---

# NOT for diffusion


**We build these ourselves with code generators (11)** — correct by construction:

- `fig-phy-5` (Physik): Beschriftete Strecken-Zeitlinie (Reaktionsweg + Bremsweg) aus 30 km/h auf drei Untergründe — matplotlib:bar_chart als horizontales gestapeltes Diagramm mit zwei Segmenten (R
- `fig-gpb-3` (Geschichte und politische Bildung): Horizontale Zeitleiste 1933–1955 mit den sechs Ereignissen als beschriftete Markierungen,  — matplotlib:timeline oder number_line — horizontale Achse 1933–1960, sechs Markie
- `fig-ged-1` (Geometrisches Zeichnen): Dreitafelprojektion eines einfachen L-förmigen Körpers mit beschrifteten Ansichten (Grundr — matplotlib/SVG orthographic-projection schematic: L-shaped solid, three views ar
- `fig-ged-2` (Geometrisches Zeichnen): Tabellarische Übersicht der fünf Grundkörper (Würfel, Quader, Prisma, Pyramide, Zylinder,  — matplotlib 3D axes or SVG: oblique projections of the 7 standard solids, each la
- `fig-ted-1` (Technik und Design): Schematische Schnittzeichnung eines Kurbel-Pleuel-Mechanismus mit beschrifteten Teilen (Ku — SVG/matplotlib schematic: crank at 45°, connecting rod, piston in guide channel;
- `fig-ted-2` (Technik und Design): Schematisches Zahnradpaar mit eingezeichneten Zähnezahlen (z.B. 36 und 12) und Drehzahlpfe — SVG: two meshing gear circles, large (36T) with slow arrow, small (12T) with fas
- `fig-kug-1` (Kunst und Gestaltung): Zwölfteiliger Farbkreis (Primär-, Sekundär- und Tertiärfarben) mit eingezeichneten Komplem — matplotlib polar color wheel: 12 segments filled with correct hues (HSV interpol
- `fig-bus-1` (Bewegung und Sport): Superkompensationskurve: Leistungsfähigkeit (y-Achse) über Zeit (x-Achse) mit beschriftete — matplotlib line chart: smooth curve starting at baseline, dipping (Ermüdung), ri
- `fig-bus-3` (Bewegung und Sport): Vereinfachter Hallenplan (Basketball/Handball) von oben: linke Hälfte zeigt Angriffsspiele — SVG or matplotlib: simplified rectangular court outline (half-court each side), 
- `fig-dgb-1` (Digitale Grundbildung): Flussdiagramm des Pseudocode-Algorithmus aus t3: Start → Zahl=1 → Bedingungsraute (Zahl ≤  — SVG flowchart with standard symbols: rectangle (process), diamond (decision), ar
- `fig-dgb-2` (Digitale Grundbildung): Generisches Datenfluss-Schema: Nutzer:in (links) → App/Plattform → Datenhändler (Data Brok — SVG flow diagram: 4-column left-to-right layout; generic icons (person silhouett

**These need a REAL source (6)** — sourced + rights-cleared, never faked by diffusion:

- `fig-gpb-5` (Geschichte und politische Bildung): Schematische Karte Europa–Amerika mit Migrationspfeilen: 1) dicker Pfeil Tirol → New York  — Benötigt eine ECHTE Basiskarte Europa–Nordamerika mit korrekt verorteten Städten
- `fig-gpb-6` (Geschichte und politische Bildung): Schematische Karte Österreichs 1945–1955 mit den vier Besatzungszonen: US (grün), UK (blau — Benötigt eine ECHTE geografisch korrekte Österreichkarte mit korrekten Bundeslan
- `fig-gwb-7` (Geographie und wirtschaftliche Bildung): Schematische Österreichkarte mit farbig markierten Wirtschaftsregionstypen: Industrieregio — Benötigt eine geografisch korrekte Österreichkarte mit akkuraten Bundeslandgrenz
- `fig-kug-2` (Kunst und Gestaltung): Reproduction of Albrecht Dürer, Selbstbildnis im Pelzrock (1500, Alte Pinakothek München) — Public domain (pre-1928 work). Source: Wikimedia Commons — https://commons.wikim
- `fig-mus-1` (Musik): Fotografien der fünf Instrumente aus t1 in einer Bildleiste (Geige, Querflöte, Kleine Trom — All five instruments are real physical objects; a diffusion illustration would b
- `fig-mus-2` (Musik): Faksimile der Titelseite der Eroica-Partitur (Beethoven, op. 55) mit der durchgestrichenen — The Eroica title-page facsimile is widely reproduced. The Gesellschaft der Musik