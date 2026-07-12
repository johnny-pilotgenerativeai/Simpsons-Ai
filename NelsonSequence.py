"""
NelsonSequence.py  —  Nelson's HA-HA sequence.

When misfortune is detected Nelson doesn't just shout from offscreen.
He walks over, points, delivers the HA-HA to the victim's face,
the victim reacts, then Nelson saunters off.

Sequence:
  1. [SCENE] Nelson spots the misfortune, grins
  2. [SCENE] Nelson walks over / approaches the victim
  3. Nelson: points and delivers HA-HA directly to their face
  4. Victim reacts (receiving the HA-HA)
  5. [SCENE] Nelson turns and walks off (or runs if chased)
  6. Nelson: exit line over his shoulder
"""

import re
from character_base import get_scene
from bridge import (
    scene_line, pause, pipe_write,
    WHITE, BOLD, DIM, RESET, ITALIC,
)


# Nelson only travels if victim is close enough (same scene or adjacent)
ADJACENT_SCENES = {
    "742evergreen":   ["742evergreen", "744evergreen"],
    "744evergreen":   ["742evergreen", "744evergreen"],
    "elementary":     ["elementary", "elementary_outside"],
    "elementary_outside": ["elementary", "elementary_outside"],
}


def can_reach(nelson_scene: str, victim_scene: str) -> bool:
    """Return True if Nelson can walk to the victim's location."""
    if nelson_scene == victim_scene:
        return True
    adjacent = ADJACENT_SCENES.get(nelson_scene, [])
    return victim_scene in adjacent



def run_nelson_sequence(all_chars: dict, victim_key: str,
                        misfortune_desc: str, conv_log=None):
    """
    Run the full Nelson HA-HA sequence against a specific victim.

    all_chars:        ALL_CHARS dict
    victim_key:       the character key of the person being HA-HA'd
    misfortune_desc:  brief description of what went wrong (for context)
    conv_log:         optional ConversationLog
    """
    nelson = all_chars.get("nelson")
    victim = all_chars.get(victim_key)

    if not nelson or not victim:
        return

    nelson_scene = get_scene(nelson.location)
    victim_scene  = get_scene(victim.location)

    # Work out if Nelson walks to them or is already there
    already_there = (nelson_scene == victim_scene)
    reachable     = can_reach(nelson_scene, victim_scene)

    def record(char, text, etype="speech"):
        if conv_log:
            conv_log.record(etype, char.name,
                            get_scene(char.location), char.location,
                            text, char.color)

    def record_event(text):
        if conv_log:
            conv_log.record_event(text, victim_scene, victim.location)

    # ── Step 1: Nelson spots the misfortune ───────────────────────────────
    scene_line(f"Nelson spots {victim.name}'s misfortune from across Springfield. "
               f"His eyes light up.")
    record_event(f"Nelson spots {victim.name}'s misfortune. His eyes light up.")
    pause(0.6)

    # ── Step 2: Nelson approaches (if not already there) ──────────────────
    if not already_there and reachable:
        scene_line(f"Nelson jogs over to {victim.name}, hands in pockets, "
                   f"grinning the whole way.")
        record_event(f"Nelson jogs over to {victim.name}.")
        # Update Nelson's location to match victim's
        nelson.set_location(victim.location)
        pause(0.7)
    elif not reachable:
        # Too far — Nelson cups hands and shouts from afar
        scene_line(f"Nelson is too far away to walk over but cups his hands "
                   f"and shouts across Springfield.")
        record_event(f"Nelson shouts across Springfield at {victim.name}.")
        pause(0.4)

    # ── Step 3: Nelson delivers the HA-HA ────────────────────────────────
    print(f"\n{nelson.color}[NELSON]:{RESET} ", end="")
    nelson_response = nelson.get_response(
        f"{victim.name} just suffered this misfortune: {misfortune_desc}. "
        f"You are now standing right in front of them. Point directly at them "
        f"and deliver your iconic HA-HA to their face. Add a short specific "
        f"taunt about exactly what went wrong for them. Then describe yourself "
        f"pointing.",
        sender="[HA-HA Trigger]",
        trigger_depth=99,
        ignore_location=True,
    )
    record(nelson, nelson_response)
    pause(0.5)

    # ── Step 4: Victim reacts to the HA-HA ───────────────────────────────
    print(f"\n{victim.color}[{victim.name.upper()} — reacts to HA-HA]:{RESET} ", end="")
    victim_response = victim.get_response(
        f"Nelson Muntz is standing right in front of you, pointing at you "
        f"and doing his HA-HA laugh about: {misfortune_desc}. "
        f"React as {victim.name} would to being HA-HA'd directly to your face.",
        sender="[Nelson's HA-HA]",
        trigger_depth=1,
        ignore_location=True,
    )
    record(victim, victim_response)
    pause(0.5)

    # ── Step 5: Scene — Nelson exits ──────────────────────────────────────
    # Does the victim try to chase/retaliate?
    chase_words = re.search(
        r"\b(chase|get|grab|catch|kill|strangle|after|come here)\b",
        victim_response, re.IGNORECASE
    )

    if chase_words:
        scene_line(f"{victim.name} lunges at Nelson. Nelson bolts.")
        record_event(f"{victim.name} lunges. Nelson runs away laughing.")
    else:
        scene_line(f"Nelson turns and saunters off, still chuckling.")
        record_event(f"Nelson saunters off.")
    pause(0.4)

    # ── Step 6: Nelson's exit line ────────────────────────────────────────
    print(f"\n{nelson.color}[NELSON]:{RESET} ", end="")
    exit_line = nelson.get_response(
        f"You've just HA-HA'd {victim.name} to their face and now you're "
        f"{'running away because they chased you' if chase_words else 'walking away'}. "
        f"Deliver a short exit line over your shoulder — smug, brief, in character.",
        sender="[Exit]",
        trigger_depth=99,
        ignore_location=True,
    )
    record(nelson, exit_line)