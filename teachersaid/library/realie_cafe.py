"""Realien flagship #2 — "At the café" (FS1 Englisch, A2). The second genre.

Proves the engine isn't timetable-locked: a CONSTRUCTED café menu (no source, no rights gate)
exercises the price path the departure board didn't — the scan answers and the order total are
£-prices the internal-consistency lint checks against the menu. Café language naturally involves
adding up an order, so one task shows a sum ("£2.00 + £3.00 = £5.00"): the lint exempts a *shown*
sum (a computation over the menu) while still catching a bare wrong price. Same shape as the
station Realie: scan warm-up (Lesen) · write-an-order (Schreiben) · a customer/waiter Sprechkarte
(Sprechen, oral). *Invent the menu, vet the English.*
"""

from __future__ import annotations

from ..schema.blocks import Serves
from ..schema.texts import AnnotatedText, Annotation, RealieFact

# A constructed café menu — natural rows ("Tea — £1.50") so it renders legibly in a proportional
# font (no dotted leaders that would go ragged).
_MENU = """THE CORNER CAFÉ
Fresh coffee and homemade cakes — family-run since 1985

DRINKS
Tea — £1.50
Coffee — £2.00
Hot chocolate — £2.50
Orange juice — £2.50
(All our drinks are also available to take away.)

SNACKS
Cheese sandwich — £3.50
Tomato soup — £4.00   (served with warm bread)
Apple pie — £3.00   — our customers' favourite!
Chocolate cake — £3.50

Open every day, morning till evening · Free Wi-Fi
Thank you, and enjoy your visit!"""

CAFE = AnnotatedText(
    backdrop_asset="img-realie-cafe-backdrop",
    id="fs1-realie-cafe", title="At the café", subject="Erste lebende Fremdsprache",
    klasse=2, genre="Speisekarte (café menu)", textsorte="Realie",
    text=_MENU, scene="Im Café", cefr="A2", origin="constructed",   # constructed → no source
    facts=[
        RealieFact(label="Tea", value="£1.50"),
        RealieFact(label="Coffee", value="£2.00"),
        RealieFact(label="Hot chocolate", value="£2.50"),
        RealieFact(label="Orange juice", value="£2.50"),
        RealieFact(label="Cheese sandwich", value="£3.50"),
        RealieFact(label="Tomato soup", value="£4.00"),
        RealieFact(label="Apple pie", value="£3.00"),
        RealieFact(label="Chocolate cake", value="£3.50"),
    ],
    serves=[Serves(competence_id="FS1.US.2.LES.02", relation="exercises"),   # Alltagstext-Infos (Lesen)
            Serves(competence_id="FS1.US.2.SCH.03", relation="exercises"),   # Mitteilung schreiben
            Serves(competence_id="FS1.US.2.SPR.02", relation="exercises")],  # Alltagsgespräch (Sprechen)
    keywords=["Realie", "Speisekarte", "café menu", "A2", "Englisch", "im Café",
              "ordering", "prices", "communicative", "Sprechanlass"],
    annotations=[
        Annotation(kind="vocab", label="to order", answer="bestellen"),
        Annotation(kind="vocab", label="the bill", answer="die Rechnung"),
        Annotation(kind="vocab", label="a snack", answer="eine Kleinigkeit zu essen"),
        Annotation(kind="vocab", label="Would you like…?", answer="Möchtest du…? / Hättest du gern…?"),
        # --- a gentle scan to enter (Lesen) ---
        Annotation(kind="comprehension", dimensions=["LES"], cognitive_level="understand",
                   label="How much is a cheese sandwich?", answer="£3.50."),
        # --- decide under a constraint: read the menu against a budget (analyze) ---
        Annotation(kind="comprehension", dimensions=["LES"], cognitive_level="analyze",
                   label="You have £4. Can you buy a coffee AND a tomato soup together? "
                         "Why or why not?",
                   answer="No: £2.00 + £4.00 = £6.00, and that is more than £4."),
        # --- recommend with a reason: categorise the menu (evaluate) ---
        Annotation(kind="comprehension", dimensions=["LES"], cognitive_level="evaluate",
                   label="Your friend doesn't like sweet things. Which snack would you recommend, "
                         "and why?",
                   answer="The cheese sandwich (£3.50) or the tomato soup (£4.00) — they are not "
                          "sweet, while the apple pie and the chocolate cake are."),
        # --- communicative writing (Schreiben): a written order, with the total shown ---
        Annotation(kind="communicative", dimensions=["SCH"], cognitive_level="apply",
                   label="You have £6. Write a short note to the waiter: order two things from the "
                         "menu and write the total.",
                   answer="Modelltext: „Hello! I would like a coffee and a chocolate cake, please. "
                          "That is £2.00 + £3.50 = £5.50. Thank you!“ (2 Dinge von der Karte; Summe "
                          "gezeigt; einfache, weitgehend korrekte Sätze)."),
        # --- role-play (Sprechen): a customer/waiter Sprechkarte; the speaking happens in the room ---
        Annotation(kind="roleplay", dimensions=["SPR"], cognitive_level="apply",
                   label="Work in pairs. Act out ordering at the café.",
                   roles=["You are the customer. Order one drink and one snack from the menu. Ask "
                          "how much it is, and ask for the bill. Be polite.",
                          "You are the waiter. Greet the customer, take their order and tell them "
                          "the price (use the menu). Be friendly."],
                   answer="Erwartet: Kund:in bestellt („Can I have…?“, „I'd like…“) + fragt „How "
                          "much is it?“; Kellner:in nennt den Preis von der Karte (z. B. „That's "
                          "£4.00, please.“) und reagiert höflich. Summe darf gebildet werden."),
    ],
)
