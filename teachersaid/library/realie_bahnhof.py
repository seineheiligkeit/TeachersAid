"""Realien flagship — "At the station" (FS1 Englisch, A2). The first communicative Realie.

The proof of `Documents/realien-design.md`: a CONSTRUCTED, invented-coherent everyday text (a
departure board) — no source, no rights gate, because it is a *Sprechanlass, not an Aussage*. The
facts (times, platforms) are fiction guarded only by the internal-consistency lint; what is
load-bearing is the **English** (SME-vetted) and the **communicative** task layer: a scan warm-up
(Lesen), a write-a-message task (Schreiben), and a Sprechkarte role-play (Sprechen — served in the
room, not on paper). *Invent the timetable, vet the French.* (Here: the English.)
"""

from __future__ import annotations

from ..schema.blocks import Serves
from ..schema.texts import AnnotatedText, Annotation, RealieFact

# A constructed departure board. Rows are natural-language ("08:14 to London — Platform 3") so they
# render legibly in a proportional font (no space-aligned columns that would go ragged).
_BOARD = """NEWCASTLE CENTRAL STATION
Departures — have a safe journey!

08:14   to London — Platform 3   (on time)
08:45   to Edinburgh — Platform 1   (on time)
09:10   to Manchester — Platform 2   (boarding now)
09:30   to London — Platform 5   (on time)
10:05   to York — Platform 4   (on time)

Trains can be busy on Friday afternoons.
Please keep your luggage with you at all times.
Need help? Ask at the Information Desk near Platform 1."""

BAHNHOF = AnnotatedText(
    id="fs1-realie-bahnhof", title="At the station", subject="Erste lebende Fremdsprache",
    klasse=2, genre="Fahrplan (departure board)", textsorte="Realie",
    text=_BOARD, scene="Am Bahnhof", cefr="A2", origin="constructed",   # constructed → no source
    facts=[
        RealieFact(label="08:14 to London", value="Platform 3"),
        RealieFact(label="08:45 to Edinburgh", value="Platform 1"),
        RealieFact(label="09:10 to Manchester", value="Platform 2"),
        RealieFact(label="09:30 to London", value="Platform 5"),
        RealieFact(label="10:05 to York", value="Platform 4"),
    ],
    serves=[Serves(competence_id="FS1.US.2.LES.02", relation="exercises"),   # Alltagstext-Infos (Lesen)
            Serves(competence_id="FS1.US.2.SCH.03", relation="exercises"),   # Mitteilung schreiben
            Serves(competence_id="FS1.US.2.SPR.02", relation="exercises")],  # Alltagsgespräch (Sprechen)
    keywords=["Realie", "Fahrplan", "departure board", "A2", "Englisch", "am Bahnhof",
              "scanning", "communicative", "Sprechanlass"],
    annotations=[
        Annotation(kind="vocab", label="departure", answer="die Abfahrt"),
        Annotation(kind="vocab", label="platform", answer="der Bahnsteig / das Gleis"),
        Annotation(kind="vocab", label="to change (trains)", answer="umsteigen"),
        Annotation(kind="vocab", label="single / return", answer="einfach / hin und zurück"),
        # --- a gentle scan to enter (Lesen) ---
        Annotation(kind="comprehension", dimensions=["LES"], cognitive_level="understand",
                   label="When does the next train to Edinburgh leave, and from which platform?",
                   answer="At 08:45, from Platform 1."),
        # --- decide against a deadline: read the board + reason about time (analyze) ---
        Annotation(kind="comprehension", dimensions=["LES"], cognitive_level="analyze",
                   label="You must be in London before 09:00. Which train do you take, and why "
                         "can't you take the 09:30?",
                   answer="The 08:14 train to London (Platform 3). The 09:30 leaves after 09:00, "
                          "so you would arrive too late."),
        # --- use the live status (the 'boarding now' detail becomes the hook) (apply) ---
        Annotation(kind="comprehension", dimensions=["LES"], cognitive_level="apply",
                   label="Look at the board. Which train is boarding now, and what should you do "
                         "if you want to catch it?",
                   answer="The 09:10 to Manchester (Platform 2) is boarding now — go to Platform 2 "
                          "quickly."),
        # --- communicative writing (Schreiben): the model answer's data is on the board ---
        Annotation(kind="communicative", dimensions=["SCH"], cognitive_level="apply",
                   label="Your friend is waiting for you in London. Write a short message "
                         "(3–4 sentences): say which train you take, when it leaves and from "
                         "which platform.",
                   answer="Modelltext: „Hi! I take the 09:30 train to London. It leaves from "
                          "Platform 5. See you soon!“ (3–4 einfache Sätze; Uhrzeit + Bahnsteig "
                          "vom Plan; einfache, weitgehend korrekte Sätze)."),
        # --- role-play (Sprechen): a Sprechkarte; the speaking happens in the room ---
        Annotation(kind="roleplay", dimensions=["SPR"], cognitive_level="apply",
                   label="Work in pairs. Act out a short conversation at the ticket desk.",
                   roles=["You are a traveller. You want to go to Edinburgh. Ask when the next "
                          "train leaves, which platform it goes from, and whether you have to "
                          "change. Be polite.",
                          "You work at the ticket desk. Answer the traveller's questions using "
                          "the departure board. Use full sentences and be friendly."],
                   answer="Erwartet: A fragt z. B. „When does the next train to Edinburgh leave?“, "
                          "„Which platform?“; B antwortet mit Uhrzeit + Gleis vom Plan (08:45, "
                          "Platform 1). Nützliche Wendungen: „Excuse me…“, „The next train "
                          "leaves at…“, „from Platform…“, „You don't have to change.“"),
    ],
)
