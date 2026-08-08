"""
Family_chat.py  —  Simpson Family Chat
A focused version of SpringfieldChat with only the 5 Simpsons.
All location tracking, SceneDirector, and co-location filtering active.

Run:  python Family_chat.py
"""

import Homer, Lisa, Bart, Marge, Maggie
import character_base as _cb
from character_base import get_scene

# ── Load settings ─────────────────────────────────────────────────────────────
try:
    import settings as _cfg
    _ENABLED = _cfg.CHARACTERS
except ImportError:
    _ENABLED = {}

def _active(module_name: str) -> bool:
    return _ENABLED.get(module_name, True)

# ── Family roster ─────────────────────────────────────────────────────────────
FAMILY = {}
if _active("Homer"):  FAMILY["homer"]  = Homer.character
if _active("Lisa"):   FAMILY["lisa"]   = Lisa.character
if _active("Bart"):   FAMILY["bart"]   = Bart.character
if _active("Marge"):  FAMILY["marge"]  = Marge.character
if _active("Maggie"): FAMILY["maggie"] = Maggie.character

# Populate shared reference so SceneDirector can access all characters
_cb.ALL_CHARS_REF.update(FAMILY)

# ── Initialise SceneDirector ──────────────────────────────────────────────────
try:
    from SceneDirector import SceneDirector
    DIRECTOR         = SceneDirector(FAMILY)
    DIRECTOR_ENABLED = True
except Exception as e:
    print(f"[SceneDirector] Could not load: {e}")
    DIRECTOR         = None
    DIRECTOR_ENABLED = False

# ── Nelson is not in this chat but import haw_haw_check just in case ─────────
try:
    from nelson import haw_haw_check as _haw
    def nelson_interject(response, speaker_name):
        pass   # Nelson not in family chat
except ImportError:
    def nelson_interject(response, speaker_name):
        pass

# ── Aliases ───────────────────────────────────────────────────────────────────
ALIASES = {}  # no aliases needed for 5 characters

def resolve(name: str) -> str:
    return ALIASES.get(name, name)

# ── Helpers ───────────────────────────────────────────────────────────────────

def run_director(speaker_key: str, speaker_name: str, response: str):
    if not DIRECTOR_ENABLED or DIRECTOR is None:
        return
    result = DIRECTOR.analyse(speaker_key, speaker_name, response)
    DIRECTOR.apply(result, react_fn=director_react)


def director_react(event: str, targets: list):
    WHITE = "\033[97m"; BOLD = "\033[1m"; RESET = "\033[0m"
    
    # Clean up event text - remove any narrator prefixes or formatting artifacts
    clean_event = event.strip()
    if clean_event.lower().startswith("narrator:"):
        clean_event = clean_event[10:].strip()  # Remove "narrator: " prefix
    if clean_event.startswith('"') and clean_event.endswith('"'):
        clean_event = clean_event[1:-1]  # Remove surrounding quotes
    if clean_event.startswith("'") and clean_event.endswith("'"):
        clean_event = clean_event[1:-1]  # Remove surrounding single quotes
    
    print(f"\n{BOLD}{WHITE}{'─'*60}{RESET}")
    print(f"{BOLD}{WHITE}  [Auto-Event] {clean_event}{RESET}")
    print(f"{BOLD}{WHITE}{'─'*60}{RESET}")
    for key in targets:
        char = FAMILY.get(key.lower())
        if char:
            print(f"\n{char.color}[{char.name.upper()}]:{char.reset} ", end="")
            response = char.get_response(
                f'The following just happened: "{event}". React in character.',
                sender="[Auto-Event]"
            )


def group_discussion(message: str, roster: dict, label: str):
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    for key, char in roster.items():
        print(f"\n{char.color}[{char.name.upper()}]:{char.reset} ", end="")
        response = char.get_response(message, sender="User")
        run_director(key, char.name, response)


# ── Banner ────────────────────────────────────────────────────────────────────
BANNER = """
╔══════════════════════════════════════════════════════════════╗
║           🍩  THE SIMPSONS FAMILY CHAT  🍩                   ║
╠══════════════════════════════════════════════════════════════╣
║  Location tracking and SceneDirector active.                 ║
╠══════════════════════════════════════════════════════════════╣
║  @homer / @lisa / @bart / @marge / @maggie                   ║
║  @all  <msg>         — whole family replies                  ║
║                                                              ║
║  /<speaker>:<listener> <msg>   — character to character      ║
║  /<speaker>:<l1>@<l2>  <msg>   — one to many                 ║
║  /thoughts:<char> <prompt>     — private thoughts            ║
║  /event <desc>                 — scene event (no reactions)  ║
║  /event:all <desc>             — event, family reacts        ║
║  [Location: char@char: desc]   — set location manually       ║
║  /locations                    — show where everyone is      ║
║  /director on|off              — toggle AI director          ║
║  exit                          — leave Springfield           ║
╚══════════════════════════════════════════════════════════════╝
"""

# ── Main REPL ─────────────────────────────────────────────────────────────────

def main():
    print(BANNER)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nD'oh! Bye!")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower == "exit":
            print("So long, Springfield!")
            break

        # ── /locations ────────────────────────────────────────────────────
        if lower.strip() == "/locations":
            if DIRECTOR:
                DIRECTOR.show_locations()
            continue

        # ── /director on|off ──────────────────────────────────────────────
        if lower.startswith("/director"):
            global DIRECTOR_ENABLED
            if "off" in lower:
                DIRECTOR_ENABLED = False
                print("[SceneDirector] OFF")
            elif "on" in lower:
                DIRECTOR_ENABLED = True
                print("[SceneDirector] ON")
            continue

        # ── [Location: char@char: desc] ───────────────────────────────────
        if lower.startswith("[location:") or lower.startswith("/locate "):
            WHITE = "\033[97m"; RESET = "\033[0m"; DIM = "\033[2m"
            inner = (user_input[len("[location:"):].rstrip("]").strip()
                     if lower.startswith("[location:")
                     else user_input[len("/locate "):].strip())
            if ":" not in inner:
                print("Usage: [Location: char@char: description]")
                continue
            char_part, _, desc = inner.partition(":")
            desc = desc.strip()
            keys = [n.strip().lower() for n in char_part.split("@")]
            if DIRECTOR:
                DIRECTOR.set_location(keys, desc)
            continue

        # ── /event ────────────────────────────────────────────────────────
        if lower.startswith("/event"):
            WHITE = "\033[97m"; BOLD = "\033[1m"; RESET = "\033[0m"
            rest = user_input[6:].strip()
            roster = None
            if rest.startswith(":"):
                parts = rest[1:].split(" ", 1)
                if len(parts) < 2:
                    print("Usage: /event:<group> <description>")
                    continue
                group_key, description = parts[0].lower(), parts[1].strip()
                roster = FAMILY if group_key in ("all", "family") else None
            else:
                description = rest

            print(f"\n{BOLD}{WHITE}{'─'*60}{RESET}")
            print(f"{BOLD}{WHITE}  [Event] {description}{RESET}")
            print(f"{BOLD}{WHITE}{'─'*60}{RESET}")

            if roster:
                for key, char in roster.items():
                    print(f"\n{char.color}[{char.name.upper()}]:{char.reset} ", end="")
                    response = char.get_response(
                        f'This just happened: "{description}". React in character.',
                        sender="[Event]", ignore_location=True
                    )
                    run_director(key, char.name, response)
            continue

        # ── /thoughts:<char> ─────────────────────────────────────────────
        if lower.startswith("/thoughts:") or lower.startswith("/think:"):
            rest = user_input.split(":", 1)[1] if ":" in user_input else ""
            parts = rest.split(" ", 1)
            if len(parts) < 2:
                print("Usage: /thoughts:<character> <prompt>")
                continue
            char = FAMILY.get(parts[0].lower())
            if not char:
                print(f"Unknown: '{parts[0]}'")
                continue
            char.think(parts[1])
            continue

        # ── @all ─────────────────────────────────────────────────────────
        if lower.startswith("@all "):
            group_discussion(user_input[5:].strip(), FAMILY, "🏠  SIMPSON FAMILY")
            continue

        # ── @character ───────────────────────────────────────────────────
        if user_input.startswith("@"):
            parts = user_input[1:].split(" ", 1)
            if len(parts) < 2:
                print("Usage: @<character> <message>")
                continue
            key, message = parts[0].lower(), parts[1]
            char = FAMILY.get(key)
            if not char:
                print(f"Unknown: '{key}'. Choose: {', '.join(FAMILY)}")
                continue
            print(f"\n{char.color}[{char.name.upper()}]:{char.reset} ", end="")
            response = char.get_response(message, sender="User")
            run_director(key, char.name, response)
            continue

        # ── /<speaker>:<listener(s)> <msg> ───────────────────────────────
        if user_input.startswith("/") and ":" in user_input:
            arrow_part, _, message = user_input[1:].partition(" ")
            parts = arrow_part.split(":")
            if len(parts) != 2 or not message:
                print("Usage: /<speaker>:<listener> <message>")
                continue
            speaker_key  = parts[0].lower()
            listener_keys = [k.lower() for k in parts[1].split("@") if k]
            speaker = FAMILY.get(speaker_key)
            if not speaker:
                print(f"Unknown speaker '{speaker_key}'.")
                continue
            if len(listener_keys) == 1:
                reply = speaker.talk_to(listener_keys[0], message)
                if reply:
                    run_director(speaker_key, speaker.name, reply)
            else:
                speaker.talk_to_many(listener_keys, message)
            continue

        # ── Fallback → @all ───────────────────────────────────────────────
        print("Tip: @homer, @all, /homer:bart, /thoughts:lisa, /locations")
        print("     Defaulting to @all...\n")
        group_discussion(user_input, FAMILY, "🏠  SIMPSON FAMILY")


if __name__ == "__main__":
    main()