"""
Actions.py  —  Character action system for Springfield Chat.

Handles physical actions like:
  [Bart hops on his skateboard and runs away]
  [Homer reaches for another donut]
  [Marge sighs and goes back to the kitchen]

Actions:
  - Display in a distinctive gold/amber colour with character colour prefix
  - Are logged to the conversation log
  - Tell the SceneDirector what happened so locations update
  - Can trigger reactions from co-located characters
  - Update the acting character's activity automatically
"""

import re
from character_base import get_scene

# ── Colours ───────────────────────────────────────────────────────────────────
GOLD   = "\033[33m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
ITALIC = "\033[3m"
RESET  = "\033[0m"
WHITE  = "\033[97m"

# ── Action reaction probability keywords ─────────────────────────────────────
# If these appear in an action, nearby characters will react
REACTION_TRIGGERS = [
    r"\b(runs?|runs away|flees?|escapes?|bolts?)\b",
    r"\b(falls?|trips?|slips?|crashes?|stumbles?)\b",
    r"\b(throws?|hurls?|launches?|flings?)\b",
    r"\b(shouts?|yells?|screams?|cries?|wails?)\b",
    r"\b(breaks?|smashes?|destroys?|explodes?)\b",
    r"\b(strangles?|grabs?|pushes?|shoves?|hits?|punches?)\b",
    r"\b(jumps?|leaps?|dives?|lands?)\b",
    r"\b(laughs?|cries?|weeps?|sobs?)\b",
]

_REACTION_RE = re.compile("|".join(REACTION_TRIGGERS), re.IGNORECASE)


def parse_action(user_input: str, all_chars: dict, aliases: dict) -> tuple[str, str, str] | None:
    """
    Parse an action string like "[Bart hops on his skateboard and runs away]"

    Returns (char_key, char_name, action_description) or None if not matched.

    Supported formats:
      [Bart hops on his skateboard]         — specific character
      [Homer reaches for a donut]
      [SCENE] ...                           — already handled elsewhere, skip
    """
    text = user_input.strip()

    # Must start with [ and end with ] (or just start with [ for loose syntax)
    if not text.startswith("["):
        return None
    text = text.lstrip("[").rstrip("]").strip()

    # Skip [SCENE] and [Event] — handled by other systems
    lo = text.lower()
    if lo.startswith("scene") or lo.startswith("event") or lo.startswith("location"):
        return None

    # Try to match "CharacterName <action>"
    # Look for any known character name (or alias) at the start
    for key, char in all_chars.items():
        name = char.name.lower()
        if lo.startswith(name):
            action = text[len(char.name):].strip()
            # Strip leading verb connectors: "hops", "is hopping" etc.
            return (key, char.name, action)

    # Try aliases
    for alias, canonical in aliases.items():
        if lo.startswith(alias):
            char = all_chars.get(canonical)
            if char:
                action = text[len(alias):].strip()
                return (canonical, char.name, action)

    return None


def display_action(char_name: str, char_color: str, action: str):
    """Print the action in its distinctive style."""
    print(f"\n{char_color}{BOLD}[{char_name}]{RESET} "
          f"{ITALIC}{GOLD}{action}{RESET}")


def should_react(action: str) -> bool:
    """Return True if this action is dramatic enough to trigger reactions."""
    return bool(_REACTION_RE.search(action))


def run_action(user_input: str, all_chars: dict, aliases: dict,
               director=None, conv_log=None, nelson_interject_fn=None,
               run_director_fn=None) -> bool:
    """
    Parse and execute a character action.

    Returns True if the input was an action (consumed), False otherwise.
    """
    parsed = parse_action(user_input, all_chars, aliases)
    if parsed is None:
        return False

    char_key, char_name, action = parsed
    char = all_chars.get(char_key)
    if not char:
        return False

    # ── 1. Display the action ──────────────────────────────────────────────
    display_action(char_name, char.color, action)

    # ── 2. Log it ──────────────────────────────────────────────────────────
    if conv_log:
        scene_tag = get_scene(char.location)
        conv_log.record("action", char_name, scene_tag,
                        char.location, action, char.color)

    # ── 3. Tell the SceneDirector what happened ────────────────────────────
    if director:
        result = director.analyse(
            char_key, char_name,
            f"[ACTION] {char_name} {action}",
            context=f"Physical action by {char_name}: {action}"
        )
        director.apply(result)

    # ── 4. Have the character react to their own action ────────────────────
    print(f"\n{char.color}[{char_name.upper()}]:{RESET} ", end="")
    response = char.get_response(
        f"You just did this: {action}. "
        f"React naturally as {char_name} — say something in character about "
        f"what you just did or what happens next.",
        sender="[Action]",
        trigger_depth=1,
    )
    if conv_log:
        scene_tag = get_scene(char.location)
        conv_log.record("speech", char_name, scene_tag,
                        char.location, response, char.color)

    if run_director_fn:
        run_director_fn(char_key, char_name, response)

    # ── 5. Nearby characters react if action is dramatic ──────────────────
    if should_react(action):
        char_scene = get_scene(char.location)
        nearby = {
            k: c for k, c in all_chars.items()
            if k != char_key and get_scene(c.location) == char_scene
        }

        # Limit to 3 nearby reactions so it doesn't flood
        reacted = 0
        for key, bystander in nearby.items():
            if reacted >= 3:
                break
            print(f"\n{bystander.color}[{bystander.name.upper()} — reacts]:{RESET} ", end="")
            react_response = bystander.get_response(
                f"{char_name} just did this right in front of you: {action}. "
                f"React as {bystander.name} would.",
                sender="[Reacting to Action]",
                trigger_depth=1,
            )
            if conv_log:
                scene_tag = get_scene(bystander.location)
                conv_log.record("speech", bystander.name, scene_tag,
                                bystander.location, react_response, bystander.color)
            if nelson_interject_fn:
                nelson_interject_fn(react_response, bystander.name)
            if run_director_fn:
                run_director_fn(key, bystander.name, react_response)
            reacted += 1

    return True