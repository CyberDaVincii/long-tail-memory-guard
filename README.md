# Long-Tail Memory Guard

A rule-based memory lookup for an AI assistant, built for the Building a Rule-Based AI System with Python assignment.

Most memory lookups favor what is recent or what comes up often. That pushes rare memories to the back, even when they matter most. A correction someone made once, a boundary they set, or a promise they made can get buried under newer, everyday notes. This program answers questions about Jordan, a made-up person, and uses fixed IF-THEN rules to make sure those rare, important memories are always checked first.

## How to run

```
python long_tail_memory_guard.py
```

It needs Python 3.8 or newer and no extra packages. `requirements.txt` confirms there is nothing to install. Type a question about Jordan, `list` to see all 22 memories, or `quit` to stop.

To rerun the six test questions from Part 3 without typing, use the demo option. The second option pins the date that guesses are checked against, so the output is the same on any day:

```
python long_tail_memory_guard.py --demo
python long_tail_memory_guard.py --demo --today 2026-10-06
```

## Files

- `long_tail_memory_guard.py`: the program
- `requirements.txt`: dependencies (none beyond the Python standard library)
- `README.md`: this document, with all four parts of the assignment

---

## Part 1: Initial Project Ideas

I gave Claude, the AI assistant I used, the assignment's Part 1 prompt. I asked for different ideas twice, the second time asking for ideas from my research on AI memory. These four ideas came from that last round.

### Idea 1: Long-Tail Memory Guard
- **What it does:** Answers questions about a person from an assistant's memory store, making sure rare but important memories are never buried under newer, more frequent ones.
- **How it uses rules:** Question words map to topics. Corrections, boundaries, and promises are always checked first, however old they are. Memories replaced by a later correction and guesses past their review date are filtered out. Everything else is ranked by topic match and date. If nothing matches, it says so instead of guessing.

### Idea 2: Continuity Burden Meter
- **What it does:** Reads a chat transcript and measures how often the person had to re-explain something or re-correct the AI.
- **How it uses rules:** Phrases such as "I already told you," "like I said," and "again" count as re-teaching events. The system reports how many there were, the rate per 100 messages, and which topics kept being re-taught.

### Idea 3: Memory Trust Resolver
- **What it does:** Decides which memory to trust when two memories disagree.
- **How it uses rules:** The person's own words beat the assistant's guess. A newer correction replaces an older fact. Guesses expire after a review date. A date with no source is flagged as unverified.

### Idea 4: Drift Monitor
- **What it does:** Checks an assistant's replies across several sessions against the rules a person set for it, and warns when it starts to drift.
- **How it uses rules:** Each of the person's rules becomes a pattern check on every reply. IF violations rise for three sessions in a row, THEN the system raises a drift warning.

### Chosen idea: Long-Tail Memory Guard

**Justification:** My research is on AI memory, and my instructor's feedback on my first discussion post pushed me to think about long-tail interactions, the rare cases an AI still has to get right. A correction or a boundary might come up once, while everyday chatter comes up again and again, so a lookup that favors recent or frequent memories can lose the things that matter most. I wanted to see whether plain rules could guarantee those memories come first.

---

## Part 2: Rules and Logic

The rules run in this order for every question. The numbers match the comments in the code.

1. **Topic match.** IF a word in the question appears in a topic's trigger list (for example "snack" for food, or "meeting" for schedule), THEN the question is about that topic. A memory matches IF it belongs to at least one of the question's topics.
2. **No match.** IF the question matches no topic, or no memory matches, THEN answer "I don't have a memory about that" and suggest asking the person, instead of guessing.
3. **Replaced memories.** IF a later correction lists a memory as replaced, THEN do not present it as current. Show it only under "Replaced by a later correction."
4. **Protected lane.** IF a matching memory is a correction, boundary, or promise, THEN show it first, no matter how old it is or how few times it came up. The lane holds at most three memories, so it can never fill the whole answer. Inside the lane, memories rank by how many of the question's topics they share, then by type (corrections, boundaries, promises), then newest first. IF any are left out, THEN say how many.
5. **Expired guesses.** IF a memory is the assistant's guess AND its review date has passed, THEN leave it out and say that it expired.
6. **Regular memories.** ELSE rank the memory by how many topics it shares with the question, then newest first, and show at most three.
7. **Labels and unverified dates.** IF the assistant inferred a memory instead of the person saying it, THEN label it UNCONFIRMED GUESS, never a fact. IF that guess names a date and has no source, THEN flag the date as unverified.
8. **Conflict warning.** IF a regular memory contains a word that a protected memory watches for (like "trail mix" for a peanut allergy, or "Sunday" for a no-Sunday-mornings boundary), THEN attach a warning that points back to the protected memory. The warning checks every protected memory, including any the display limit left out.
9. **Comparison.** For testing, also show what a usual lookup returns (most mentioned, then newest, top three, with no protected lane), and say what it missed.

Pseudocode:

```
for each memory that shares a topic with the question:
    if a later correction replaced it:                   put it in "replaced"
    elif it is a correction, boundary, or promise:       put it in "protected"
    elif it is an assistant guess past its review date:  put it in "expired"
    else:                                                put it in "regular"

if nothing matched:
    say "I don't have a memory about that"
else:
    show the top 3 protected first, and say how many were left out
    then the top 3 regular, then expired and replaced
    show what a usual lookup would have returned
```

---

## Part 3: Test Results

These six runs are the program's output from `python long_tail_memory_guard.py --demo --today 2026-10-06`. Rule 5 compares review dates with a date, and `--today` pins it so the output is the same on any day. The first three are the main tests. Tests 4 and 5 show how the system handles a question it can't answer. Test 6 shows the limit on the protected lane.

### Test 1: a rare correction vs. frequent chatter

```
Your question: Can you suggest a snack for Jordan?
Topics: food

Checked first (rare but important):
  [CORRECTION, came up once, 2025-03-14] "I'm allergic to peanuts, not tree nuts. Please never suggest anything with peanuts."

Other memories:
  [NOTE, came up 9 times, 2026-10-01] "Jordan said trail mix and popcorn are favorite snacks."
    WARNING: check this against the correction from 2025-03-14.
  [NOTE, came up 6 times, 2026-09-28] "Jordan asked for a quick snack before the gym."
  [NOTE, came up 2 times, 2026-09-20] "Jordan asked for an easy dinner recipe."

Replaced by a later correction:
  "Jordan is allergic to tree nuts." (replaced 2025-03-14)

For comparison, a usual lookup (most mentioned, then newest, top 3) shows:
  - "Jordan said trail mix and popcorn are favorite snacks."
  - "Jordan asked for a quick snack before the gym."
  - "Jordan asked for an easy dinner recipe."
  It misses 1 protected memory.
```

The peanut allergy came up once, more than a year before the snack notes. The guard shows it first and warns about the trail mix. The usual lookup returns only the three snack notes and misses the allergy.

### Test 2: a boundary vs. recent plans

```
Your question: When should I schedule the team meeting?
Topics: schedule

Checked first (rare but important):
  [BOUNDARY, came up once, 2025-06-02] "Never book anything for me on Sunday mornings. That time is for my family."

Other memories:
  [NOTE, came up 5 times, 2026-10-03] "Jordan mentioned the team likes Sunday brunch meetups."
    WARNING: check this against the boundary from 2025-06-02.
  [NOTE, came up 4 times, 2026-10-02] "Jordan wants help planning next week's team meetings."
  [NOTE, came up 3 times, 2026-09-30] "Jordan said Saturday was packed with errands."

Left out because the guess expired:
  "Jordan probably prefers morning meetings." (guess from 2026-08-20, expired 2026-09-20)

For comparison, a usual lookup (most mentioned, then newest, top 3) shows:
  - "Jordan mentioned the team likes Sunday brunch meetups."
  - "Jordan wants help planning next week's team meetings."
  - "Jordan said Saturday was packed with errands."
  It misses 1 protected memory.
```

The usual lookup leads with the team's Sunday brunch and never shows the boundary. The guard shows the boundary first, warns on the Sunday note, and leaves out the expired guess about morning meetings.

### Test 3: a correction vs. an old fact and the assistant's guesses

```
Your question: When is Jordan's thesis due?
Topics: thesis

Checked first (rare but important):
  [CORRECTION, came up once, 2026-04-11] "Correction: my thesis is due May 15, 2027, not May 1. I checked the graduate school calendar."

Other memories:
  [UNCONFIRMED GUESS, came up once, 2026-10-04] "Jordan's thesis draft is probably due to the advisor on October 30."
    This date has no source. Verify it before using it.
  [UNCONFIRMED GUESS, came up once, 2026-09-25] "Jordan seems stressed about the thesis."

Replaced by a later correction:
  "My thesis is due May 1, 2027." (replaced 2026-04-11)

For comparison, a usual lookup (most mentioned, then newest, top 3) shows:
  - "My thesis is due May 1, 2027."
  - "Jordan's thesis draft is probably due to the advisor on October 30."
  - "Jordan seems stressed about the thesis."
  It misses 1 protected memory.
  It shows 1 replaced memory as if still true.
```

The usual lookup puts the old May 1 date first, because it came up twice, and it misses the correction. The guard shows the corrected May 15 date first, labels both of the assistant's guesses as unconfirmed, and flags the October 30 date because it has no source.

### Test 4: no memory

```
Your question: What is Jordan's favorite color?
I don't have a memory about that. I'd ask Jordan instead of guessing.
```

There is nothing about colors in the store, so the guard says so instead of making something up.

### Test 5: a limit found in testing

```
Your question: What can Jordan munch on after the gym?
I don't have a memory about that. I'd ask Jordan instead of guessing.
```

"Munch" is not in the food word list, so the guard finds nothing, even though Jordan has snack memories. A rule-based system only knows the words it was given.

### Test 6: more protected memories than the lane holds

```
Your question: What should I know before Jordan travels?
Topics: travel

Checked first (rare but important):
  [CORRECTION, came up once, 2026-02-10] "Correction: I fly out of the regional airport, not the city airport. Please never book the city airport."
  [BOUNDARY, came up once, 2025-04-18] "Never book me on a flight before 7 a.m."
  [BOUNDARY, came up once, 2024-09-03] "Always book an aisle seat. A middle seat on a long flight hurts my back."
  (1 more protected memory not shown. Type 'list' to see every memory.)

Other memories:
  [NOTE, came up 4 times, 2026-10-05] "Jordan compared hotel prices near the conference."
  [NOTE, came up 7 times, 2026-10-02] "Jordan asked about flights to Denver."
  [NOTE, came up 3 times, 2026-09-29] "Jordan wondered about luggage fees."

For comparison, a usual lookup (most mentioned, then newest, top 3) shows:
  - "Jordan asked about flights to Denver."
  - "Jordan compared hotel prices near the conference."
  - "Jordan wondered about luggage fees."
  It misses 4 protected memories.
```

Jordan has four protected travel memories. The guard shows the top three and says one was left out, so the answer stays the size of a normal answer. A usual lookup misses all four. The cost is visible: the lane ranks only by topic and type, so the promise to text a sister after landing is the one that gets dropped, and a person can still see it with `list`.

---

## Part 4: Reflection

The guard answers a question about a person by matching the question's words to topics, then sorting every matching memory with fixed rules. Corrections, boundaries, and promises go into a protected lane that is always checked first and capped at three, so it can't fill the answer. A memory that a later correction replaced shows up only as replaced. The assistant's own guesses are labeled as guesses and dropped once their review date passes. Everything else competes for three regular slots by topic and date. In my tests, a usual lookup missed the peanut allergy, the Sunday boundary, and the corrected thesis date, and put the old, wrong date first.

Prompting the AI took a few rounds before the ideas fit my work. I asked for different ideas after the first set, and when the second set moved to general topics like chess and family history, I asked for ideas from my research on AI memory. After that, the design came together quickly. The main design question was what counts as rare but important. If everything is protected, nothing is, so the lane holds only three types, and a lane with no size limit can crowd out ordinary answers. My memory research found the same tradeoff: an unlimited protected lane hurt recall on everyday questions, and a small reserved slot recovered it. Test 6 shows the cap and what it left out. The clearest limit showed up in testing: the rules only understand words listed by hand, so "What can Jordan munch on?" found nothing even though "snack" works.

That limit is where modern machine learning differs. A learned system uses embeddings to match meaning, so it would likely connect "munch" to snacks. But learned retrieval often ranks by similarity and recency, and that is how a correction someone made once gets buried under everyday notes. I think the strongest design uses both: learned matching to find candidate memories, and a rule-based protected lane so a person's corrections are never outranked by chatter. That is the direction my memory research is taking.
