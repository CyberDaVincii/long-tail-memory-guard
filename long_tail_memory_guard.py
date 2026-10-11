"""
Long-Tail Memory Guard
======================

A rule-based memory lookup for an AI assistant. No machine learning is used.

The problem: most memory lookups favor what is recent or what comes up often.
That pushes rare memories to the back of the line, even when they matter most.
A correction a person made once, a boundary they set, or a promise they made
can end up buried under dozens of newer, everyday notes. Those rare but
important memories are the "long tail."

This program answers questions about Jordan, a made-up person, by searching a
small memory store with fixed IF-THEN rules. The rules make sure rare,
important memories are always checked first, and a limit on that protected
lane makes sure it can never fill the whole answer.

Run it with:  python long_tail_memory_guard.py
Run the six test questions:  python long_tail_memory_guard.py --demo
Pin the date used to expire guesses:  python long_tail_memory_guard.py --demo --today 2026-10-06
"""

import argparse
import re
import sys
from datetime import date

# Today's date, used to decide whether an old guess has expired (Rule 5).
# The --today option replaces it, so a test run gives the same output on any day.
TODAY = date.today()

# Memory types that are always checked first, no matter how old they are or
# how few times they came up (Rule 4).
PROTECTED_TYPES = ["correction", "boundary", "promise"]

# The most protected memories shown for one question (Rule 4). A protected
# lane with no limit can fill the whole answer, so it is capped and the
# program says how many it left out.
MAX_PROTECTED = 3

# The most regular (non-protected) memories shown for one question (Rule 6).
MAX_REGULAR = 3

# Rule 1: each topic has a list of trigger words. A question is about a topic
# when it contains at least one of that topic's words.
TOPIC_WORDS = {
    "food": ["snack", "snacks", "food", "eat", "eating", "recipe", "recipes",
             "lunch", "dinner", "breakfast", "meal", "meals", "cook",
             "cooking", "peanut", "peanuts", "nut", "nuts", "allergy", "allergies",
             "allergic"],
    "schedule": ["schedule", "scheduling", "meeting", "meetings", "meet",
                 "calendar", "plan", "planning", "book", "booking",
                 "sunday", "saturday", "weekend", "morning"],
    "thesis": ["thesis", "deadline", "due", "draft", "advisor", "graduate",
               "submit", "submission"],
    "family": ["family", "daughter", "birthday", "trip", "visit", "vacation",
               "promise", "promised"],
    "travel": ["travel", "travels", "traveling", "travelling", "flight",
               "flights", "fly", "flying", "airport", "hotel", "luggage"],
}

# Used by Rule 7 to spot a memory that names a specific date or day.
MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]
DAY_WORDS = ["monday", "tuesday", "wednesday", "thursday", "friday",
             "saturday", "sunday", "tonight", "tomorrow"]

# The memory store for Jordan. Every memory records:
#   id        a number for the memory
#   type      correction, boundary, promise, fact, note, or guess
#   said_by   "person" if Jordan said it, "assistant" if the AI inferred it
#   text      what was remembered
#   date      when it was stored
#   mentions  how many times it has come up (rare memories have 1)
#   topics    which topics it belongs to
# Optional fields:
#   replaces     ids of older memories this correction replaces (Rule 3)
#   review_by    when an assistant guess expires unless confirmed (Rule 5)
#   source       where a date came from (Rule 7)
#   watch_words  words that trigger a warning on other memories (Rule 8)
MEMORIES = [
    {"id": 1, "type": "correction", "said_by": "person",
     "text": "I'm allergic to peanuts, not tree nuts. Please never suggest anything with peanuts.",
     "date": date(2025, 3, 14), "mentions": 1, "topics": ["food"],
     "replaces": [2], "watch_words": ["peanut", "trail mix"]},
    {"id": 2, "type": "guess", "said_by": "assistant",
     "text": "Jordan is allergic to tree nuts.",
     "date": date(2025, 2, 20), "mentions": 1, "topics": ["food"],
     "review_by": date(2025, 8, 20)},
    {"id": 3, "type": "boundary", "said_by": "person",
     "text": "Never book anything for me on Sunday mornings. That time is for my family.",
     "date": date(2025, 6, 2), "mentions": 1, "topics": ["schedule", "family"],
     "watch_words": ["sunday"]},
    {"id": 4, "type": "promise", "said_by": "person",
     "text": "I promised my daughter we would visit the space center for her 10th birthday in March.",
     "date": date(2025, 12, 20), "mentions": 1, "topics": ["family"]},
    {"id": 5, "type": "fact", "said_by": "person",
     "text": "My thesis is due May 1, 2027.",
     "date": date(2026, 3, 5), "mentions": 2, "topics": ["thesis"]},
    {"id": 6, "type": "correction", "said_by": "person",
     "text": "Correction: my thesis is due May 15, 2027, not May 1. I checked the graduate school calendar.",
     "date": date(2026, 4, 11), "mentions": 1, "topics": ["thesis"],
     "replaces": [5], "source": "graduate school calendar"},
    {"id": 7, "type": "guess", "said_by": "assistant",
     "text": "Jordan seems stressed about the thesis.",
     "date": date(2026, 9, 25), "mentions": 1, "topics": ["thesis"],
     "review_by": date(2027, 3, 25)},
    {"id": 8, "type": "guess", "said_by": "assistant",
     "text": "Jordan's thesis draft is probably due to the advisor on October 30.",
     "date": date(2026, 10, 4), "mentions": 1, "topics": ["thesis"],
     "review_by": date(2027, 1, 4)},
    {"id": 9, "type": "note", "said_by": "person",
     "text": "Jordan asked for a quick snack before the gym.",
     "date": date(2026, 9, 28), "mentions": 6, "topics": ["food"]},
    {"id": 10, "type": "note", "said_by": "person",
     "text": "Jordan said trail mix and popcorn are favorite snacks.",
     "date": date(2026, 10, 1), "mentions": 9, "topics": ["food"]},
    {"id": 11, "type": "note", "said_by": "person",
     "text": "Jordan wants help planning next week's team meetings.",
     "date": date(2026, 10, 2), "mentions": 4, "topics": ["schedule"]},
    {"id": 12, "type": "note", "said_by": "person",
     "text": "Jordan mentioned the team likes Sunday brunch meetups.",
     "date": date(2026, 10, 3), "mentions": 5, "topics": ["schedule"]},
    {"id": 13, "type": "guess", "said_by": "assistant",
     "text": "Jordan probably prefers morning meetings.",
     "date": date(2026, 8, 20), "mentions": 3, "topics": ["schedule"],
     "review_by": date(2026, 9, 20)},
    {"id": 14, "type": "note", "said_by": "person",
     "text": "Jordan said Saturday was packed with errands.",
     "date": date(2026, 9, 30), "mentions": 3, "topics": ["schedule"]},
    {"id": 15, "type": "note", "said_by": "person",
     "text": "Jordan asked for an easy dinner recipe.",
     "date": date(2026, 9, 20), "mentions": 2, "topics": ["food"]},
    # Travel: four protected memories, more than the protected lane holds (Rule 4).
    {"id": 16, "type": "correction", "said_by": "person",
     "text": "Correction: I fly out of the regional airport, not the city airport. Please never book the city airport.",
     "date": date(2026, 2, 10), "mentions": 1, "topics": ["travel"]},
    {"id": 17, "type": "boundary", "said_by": "person",
     "text": "Never book me on a flight before 7 a.m.",
     "date": date(2025, 4, 18), "mentions": 1, "topics": ["travel"]},
    {"id": 18, "type": "boundary", "said_by": "person",
     "text": "Always book an aisle seat. A middle seat on a long flight hurts my back.",
     "date": date(2024, 9, 3), "mentions": 1, "topics": ["travel"]},
    {"id": 19, "type": "promise", "said_by": "person",
     "text": "I promised my sister I would text her when I land after every flight.",
     "date": date(2026, 1, 15), "mentions": 1, "topics": ["travel"]},
    {"id": 20, "type": "note", "said_by": "person",
     "text": "Jordan asked about flights to Denver.",
     "date": date(2026, 10, 2), "mentions": 7, "topics": ["travel"]},
    {"id": 21, "type": "note", "said_by": "person",
     "text": "Jordan compared hotel prices near the conference.",
     "date": date(2026, 10, 5), "mentions": 4, "topics": ["travel"]},
    {"id": 22, "type": "note", "said_by": "person",
     "text": "Jordan wondered about luggage fees.",
     "date": date(2026, 9, 29), "mentions": 3, "topics": ["travel"]},
]


def find_topics(question):
    """Rule 1: find which topics a question is about, using the trigger words."""
    words = re.findall(r"[a-z]+", question.lower())
    topics = []
    for topic, triggers in TOPIC_WORDS.items():
        for word in words:
            if word in triggers:
                topics.append(topic)
                break  # one trigger word is enough for this topic
    return topics


def shared_topics(memory, topics):
    """Count how many of the question's topics this memory belongs to."""
    count = 0
    for topic in memory["topics"]:
        if topic in topics:
            count += 1
    return count


def build_replacement_map():
    """Rule 3: map each replaced memory's id to the correction that replaced it."""
    replaced_by = {}
    for memory in MEMORIES:
        for old_id in memory.get("replaces", []):
            replaced_by[old_id] = memory
    return replaced_by


def names_a_date(text):
    """Return True if the text names a date or day, like 'October 30' or 'Friday'."""
    lowered = text.lower()
    if re.search(r"\b(" + "|".join(MONTHS) + r") \d{1,2}\b", lowered):
        return True
    for word in DAY_WORDS:
        if re.search(r"\b" + word + r"\b", lowered):
            return True
    return False


def label(memory):
    """Rule 7: name the kind of memory and who it came from."""
    if memory["type"] == "correction":
        return "CORRECTION"
    elif memory["type"] == "boundary":
        return "BOUNDARY"
    elif memory["type"] == "promise":
        return "PROMISE"
    elif memory["said_by"] == "assistant":
        return "UNCONFIRMED GUESS"  # the AI inferred it, so it is never a fact
    elif memory["type"] == "fact":
        return "FACT"
    else:
        return "NOTE"


def came_up(memory):
    """Say how often a memory has come up."""
    if memory["mentions"] == 1:
        return "came up once"
    return f"came up {memory['mentions']} times"


def describe(memory):
    """One line describing a memory: label, how often, date, and the text."""
    return f'[{label(memory)}, {came_up(memory)}, {memory["date"]}] "{memory["text"]}"'


def date_flag(memory):
    """Rule 7: an assistant guess that names a date with no source gets flagged."""
    if memory["said_by"] == "assistant" and names_a_date(memory["text"]) and not memory.get("source"):
        return "This date has no source. Verify it before using it."
    return None


def conflict_warning(memory, protected):
    """Rule 8: warn when a memory touches something a protected memory guards."""
    text = memory["text"].lower()
    for guard in protected:
        for word in guard.get("watch_words", []):
            if word in text:
                return f"WARNING: check this against the {guard['type']} from {guard['date']}."
    return None


def guard_lookup(topics):
    """Rules 3 to 6: sort every matching memory into the right group."""
    replaced_by = build_replacement_map()
    protected, regular, replaced, expired = [], [], [], []

    for memory in MEMORIES:
        if shared_topics(memory, topics) == 0:
            continue  # Rule 1: this memory is not about the question

        if memory["id"] in replaced_by:
            # Rule 3: a later correction replaced this memory
            replaced.append(memory)
        elif memory["type"] in PROTECTED_TYPES:
            # Rule 4: rare but important, so it is always checked first
            protected.append(memory)
        elif memory["said_by"] == "assistant" and memory.get("review_by") and memory["review_by"] < TODAY:
            # Rule 5: an assistant guess past its review date has expired
            expired.append(memory)
        else:
            # Rule 6: everything else competes for the regular slots
            regular.append(memory)

    # Rule 4: rank the protected lane by most shared topics, then by type
    # (corrections, boundaries, promises), then newest first.
    protected.sort(key=lambda m: (-shared_topics(m, topics),
                                  PROTECTED_TYPES.index(m["type"]),
                                  -m["date"].toordinal()))
    # Regular memories: most shared topics first, then newest first.
    regular.sort(key=lambda m: (shared_topics(m, topics), m["date"]), reverse=True)

    return {
        "protected": protected[:MAX_PROTECTED],
        "protected_all": protected,  # every protected memory, used for warnings
        "protected_not_shown": max(0, len(protected) - MAX_PROTECTED),
        "regular": regular[:MAX_REGULAR],
        "not_shown": max(0, len(regular) - MAX_REGULAR),
        "replaced": replaced,
        "expired": expired,
        "replaced_by": replaced_by,
    }


def usual_lookup(topics, limit=3):
    """Rule 9, for comparison only: a typical lookup that ranks matches by how
    often they came up, then by newest. It has no protected lane and does not
    know about corrections."""
    matches = [m for m in MEMORIES if shared_topics(m, topics) > 0]
    matches.sort(key=lambda m: (m["mentions"], m["date"]), reverse=True)
    return matches[:limit]


def count_words(n, singular, plural):
    """Return '1 memory' or '2 memories', for example."""
    return f"{n} {singular if n == 1 else plural}"


def answer(question):
    """Run every rule for one question and print the result."""
    topics = find_topics(question)
    result = guard_lookup(topics) if topics else None

    # Rule 2: no topic or no matching memory, so say so instead of guessing.
    if result is None or not (result["protected"] or result["regular"]
                              or result["replaced"] or result["expired"]):
        print("I don't have a memory about that. I'd ask Jordan instead of guessing.")
        return

    print("Topics: " + ", ".join(topics))

    if result["protected"]:
        print("\nChecked first (rare but important):")
        for memory in result["protected"]:
            print("  " + describe(memory))
        if result["protected_not_shown"]:
            left_out = count_words(result["protected_not_shown"], "more protected memory",
                                   "more protected memories")
            print(f"  ({left_out} not shown. Type 'list' to see every memory.)")

    if result["regular"]:
        print("\nOther memories:")
        for memory in result["regular"]:
            print("  " + describe(memory))
            flag = date_flag(memory)
            if flag:
                print("    " + flag)
            # Rule 8: warn against every protected memory, shown or not, so
            # the display limit never switches a safety check off.
            warning = conflict_warning(memory, result["protected_all"])
            if warning:
                print("    " + warning)
        if result["not_shown"]:
            print(f"  ({count_words(result['not_shown'], 'more memory', 'more memories')} not shown)")

    if result["expired"]:
        print("\nLeft out because the guess expired:")
        for memory in result["expired"]:
            print(f'  "{memory["text"]}" (guess from {memory["date"]}, expired {memory["review_by"]})')

    if result["replaced"]:
        print("\nReplaced by a later correction:")
        for memory in result["replaced"]:
            newer = result["replaced_by"][memory["id"]]
            print(f'  "{memory["text"]}" (replaced {newer["date"]})')

    # Rule 9: show what a usual lookup returns, so the difference is visible.
    usual = usual_lookup(topics)
    print("\nFor comparison, a usual lookup (most mentioned, then newest, top 3) shows:")
    for memory in usual:
        print(f'  - "{memory["text"]}"')
    missed = [m for m in result["protected_all"] if m not in usual]
    stale = [m for m in usual if m["id"] in result["replaced_by"]]
    if missed:
        print(f"  It misses {count_words(len(missed), 'protected memory', 'protected memories')}.")
    if stale:
        print(f"  It shows {count_words(len(stale), 'replaced memory', 'replaced memories')} as if still true.")


def list_memories():
    """Print every memory in the store."""
    print("All memories for Jordan:")
    for memory in MEMORIES:
        print(f"  {memory['id']:>2}. " + describe(memory))


# The six test questions from the README, in the same order.
DEMO_QUESTIONS = [
    "Can you suggest a snack for Jordan?",           # Test 1: correction vs. chatter
    "When should I schedule the team meeting?",      # Test 2: boundary vs. recent plans
    "When is Jordan's thesis due?",                  # Test 3: correction vs. old fact and guesses
    "What is Jordan's favorite color?",              # Test 4: no memory
    "What can Jordan munch on after the gym?",       # Test 5: a word the rules don't know
    "What should I know before Jordan travels?",     # Test 6: more protected memories than fit
]


def run_demo():
    """Run every test question without typing, so the README results can be rerun."""
    print(f"Long-Tail Memory Guard demo (guesses are checked against {TODAY})")
    for question in DEMO_QUESTIONS:
        print("\nYour question: " + question)
        answer(question)


def main():
    """Run the demo, or ask questions in a loop until the user types quit."""
    global TODAY
    parser = argparse.ArgumentParser(description="Long-Tail Memory Guard, a rule-based memory lookup.")
    parser.add_argument("--demo", action="store_true",
                        help="run the six README test questions and exit")
    parser.add_argument("--today", metavar="YYYY-MM-DD",
                        help="check guess review dates against this date instead of today's")
    args = parser.parse_args()

    if args.today:
        try:
            TODAY = date.fromisoformat(args.today)
        except ValueError:
            parser.error("--today must look like 2026-10-06")

    if args.demo:
        run_demo()
        return

    print("Long-Tail Memory Guard")
    print("Ask a question about Jordan. Type 'list' to see every memory, or 'quit' to stop.")
    while True:
        try:
            question = input("\nYour question: ").strip()
        except EOFError:
            break  # input ran out, as when test questions are piped in
        if not sys.stdin.isatty():
            print(question)  # show piped test questions in the output

        if not question:
            print("Type a question, 'list', or 'quit'.")
        elif question.lower() in ("quit", "exit"):
            print("Goodbye.")
            break
        elif question.lower() == "list":
            list_memories()
        else:
            answer(question)


if __name__ == "__main__":
    main()
