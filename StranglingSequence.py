"""
StranglingSequence.py  —  Homer strangles Bart.

Triggered automatically when Bart:
  - Insults Homer's weight/size
  - Is generally rude/disrespectful to Homer

Sequence:
  1. [SCENE] Homer's eyes narrow...
  2. Homer: WHY YOU LITTLE— (in character, unhinged)
  3. [SCENE] Homer grabs Bart by the throat and begins strangling him
  4. Co-located characters react (Marge tries to stop it, others panic/laugh)
  5. Bart (strangled, gasping): reacts mid-strangle
  6. [SCENE] Homer releases Bart
  7. Bart (recovering, in pain): aftermath
  8. Homer (calming down, possibly guilty): winds down
"""

import re
from character_base import get_scene, ALL_CHARS_REF
from Bridge import (
    scene_line, pause, send as pipe_write,
    WHITE, BOLD, DIM, RESET, ITALIC, YELLOW, RED, GREEN,
)


# ── Trigger patterns ──────────────────────────────────────────────────────────

FAT_INSULTS = [
    r"\b(fat|fatty|fatso|chubby|tubby|blob|lard|wide|huge|enormous|massive)\b",
    r"\b(sell\s+shade|blocks?\s+(out\s+)?the\s+sun|own\s+a\s+zip\s+code)\b",
    r"\b(gut|belly|gut|stomach)\b.{0,20}\b(big|huge|enormous|massive|giant)\b",
    r"\b(big\s+as|size\s+of|weight\s+of).{0,30}\b(whale|planet|moon|sun|bus|truck)\b",
    r"mmm.{0,10}(donut|beer).{0,20}(you|homer)",   # mocking Homer's obsessions
]

RUDE_TO_HOMER = [
    r"\b(stupid|dumb|idiot|moron|dummy|loser|jerk|blockhead|nincompoop)\b",
    r"\byou\s+(are|'re).{0,15}\b(worst|terrible|awful|useless|pathetic)\b",
    r"\b(hate|can't\s+stand|embarrassed\s+by)\s+(you|homer)\b",
    r"\bhomer\b.{0,20}\b(sucks?|stinks?|smells?|is\s+the\s+worst)\b",
    r"\b(shut\s+up|drop\s+dead|get\s+lost|buzz\s+off)\b",
]

ALL_TRIGGERS = FAT_INSULTS + RUDE_TO_HOMER


def should_strangle(bart_text: str, homer_in_scene: bool) -> bool:
    """Return True if Bart said something that triggers Homer's strangling.
    Now used only as a secondary check — primary trigger is Homer saying
    WHY YOU LITTLE in his response."""
    if not homer_in_scene:
        return False
    text = bart_text.lower()
    for pattern in ALL_TRIGGERS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


# WHY YOU LITTLE trigger pattern — fires on Homer's response
_WHY_YOU_LITTLE = re.compile(
    r"why\s+you\s+little",
    re.IGNORECASE
)

def homer_said_why_you_little(homer_text: str) -> bool:
    """Return True if Homer's response contains WHY YOU LITTLE."""
    return bool(_WHY_YOU_LITTLE.search(homer_text))


# ── Scene printer ─────────────────────────────────────────────────────────────

def scene_line(text: str):
    """Print a white scene/action description line."""
    print(f"\n{BOLD}{WHITE}[SCENE] {text}{RESET}")


def pause(secs: float = 0.6):
    time.sleep(secs)


# ── The sequence ──────────────────────────────────────────────────────────────

def run_strangling_sequence(all_chars: dict, conv_log=None, skip_homer_rage: bool = False):
    """
    Execute the full Homer-strangles-Bart sequence.
    all_chars: the full ALL_CHARS dict from SpringfieldChat.
    conv_log: optional ConversationLog to record entries into.
    """
    homer = all_chars.get("homer")
    bart  = all_chars.get("bart")
    marge = all_chars.get("marge")

    if not homer or not bart:
        return

    # Verify Homer and Bart are in the same scene
    if get_scene(homer.location) != get_scene(bart.location):
        return

    # Find everyone else in the same scene
    bart_scene = get_scene(bart.location)
    bystanders = {
        key: char for key, char in all_chars.items()
        if key not in ("homer", "bart")
        and get_scene(char.location) == bart_scene
    }

    def record(char, text, entry_type="speech"):
        if conv_log:
            from character_base import get_scene as gs
            conv_log.record(entry_type, char.name if char else "",
                            get_scene(char.location) if char else bart_scene,
                            char.location if char else bart.location,
                            text,
                            char.color if char else "")

    def record_event(text):
        if conv_log:
            conv_log.record_event(text, bart_scene, bart.location)

    # ── Steps 1-2: Homer's rage — skip if he already said WHY YOU LITTLE ──
    if not skip_homer_rage:
        scene_line("Homer's eyes go wide. A vein appears on his forehead.")
        record_event("Homer's eyes go wide. A vein appears on his forehead.")
        pause(0.8)
        print(f"\n{homer.color}[HOMER]:{RESET} ", end="")
        homer_rage = homer.get_response(
            "Bart has just said something extremely rude and insulting to you. "
            "React with your absolute maximum fury. Start with WHY YOU LITTLE— "
            "and launch into a full strangling rage. Do NOT hold back.",
            sender="[Rage Trigger]",
            trigger_depth=99,
            ignore_location=True,
        )
        record(homer, homer_rage)
        pause(0.5)

    # ── Step 3: Scene — strangling begins ────────────────────────────────
    scene_line("Homer lunges at Bart and wraps his hands around his throat.")
    record_event("Homer lunges at Bart and wraps his hands around his throat.")
    pause(0.7)

    # ── Step 4: Bystanders react ──────────────────────────────────────────
    # Priority order: Marge first, then others
    priority = []
    if marge and "marge" in bystanders:
        priority.append(("marge", marge))
    for key, char in bystanders.items():
        if key != "marge":
            priority.append((key, char))

    # Limit to 3 bystanders reacting so it doesn't drag
    for key, char in priority[:3]:
        print(f"\n{char.color}[{char.name.upper()}]:{RESET} ", end="")
        if key == "marge":
            prompt = (
                "Homer has just grabbed Bart by the throat and is strangling him. "
                "React with your typical Marge energy — alarmed, trying to intervene, "
                "calling Homer's name, begging him to stop."
            )
        else:
            prompt = (
                f"Homer is strangling Bart right in front of you. "
                f"React as {char.name} would — in character, to this chaotic scene."
            )
        resp = char.get_response(prompt, sender="[Strangling Scene]",
                                 trigger_depth=99, ignore_location=True)
        record(char, resp)
        pause(0.3)

    # ── Step 5: Bart — strangled response ────────────────────────────────
    scene_line("Bart gasps and sputters, being strangled by Homer.")
    record_event("Bart gasps and sputters, being strangled by Homer.")
    pause(0.5)

    print(f"\n{bart.color}[BART — strangled]:{RESET} ", end="")
    bart_strangled = bart.get_response(
        "Homer is currently strangling you. You can barely breathe. "
        "React as Bart would — gasping, choking, maybe still being a little "
        "mouthy despite everything. Write your words as coming out strangled "
        "and broken — 'ghk—', 'ack—', 'come—on—man—'",
        sender="[Being Strangled]",
        trigger_depth=99,
        ignore_location=True,
    )
    record(bart, bart_strangled)
    pause(0.8)

    # ── Step 6: Scene — strangling stops ─────────────────────────────────
    # Check if Marge intervened — reference her if she did
    if marge and "marge" in bystanders:
        scene_line("Marge grabs Homer's arm. He releases Bart with a final shake.")
    else:
        scene_line("Homer releases Bart with a final shake, breathing heavily.")
    record_event("The strangling stops. Homer releases Bart.")
    pause(0.7)

    # ── Step 7: Bart — aftermath ──────────────────────────────────────────
    print(f"\n{bart.color}[BART — recovering]:{RESET} ", end="")
    bart_after = bart.get_response(
        "Homer just finished strangling you. You're rubbing your neck, "
        "catching your breath. React as Bart would after being strangled — "
        "shaken but still Bart, maybe a little subdued, maybe immediately "
        "considering whether you've learned anything (you haven't).",
        sender="[Post-Strangling]",
        trigger_depth=99,
        ignore_location=True,
    )
    record(bart, bart_after)
    pause(0.4)

    # ── Step 8: Homer — winds down ────────────────────────────────────────
    print(f"\n{homer.color}[HOMER]:{RESET} ", end="")
    homer_after = homer.get_response(
        "You've just finished strangling Bart. You're calming down now. "
        "You might feel a tiny bit guilty, or you might think he deserved it, "
        "or both. React as Homer would after a strangling — possibly "
        "immediately thinking about food or beer to calm down.",
        sender="[Post-Strangling]",
        trigger_depth=99,
        ignore_location=True,
    )
    record(homer, homer_after)