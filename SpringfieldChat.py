"""
SpringfieldChat.py  —  Springfield Town Group Chat
Every Springfield character in one chaotic conversation.
Nelson will automatically HA-HA at any misfortune he detects.

Run:  python SpringfieldChat.py
"""

# ── Imports — must exactly match filenames on disk (Linux is case-sensitive) ──
import Homer, Lisa, Bart, Marge, Maggie
import moe, nelson, BumbleBeeMan
import Lenny, Carl
import Comicbookguy, Montyburns, Mayorquimby
import Ned, Rod, Todd
import Skinner, Willie, LunchLadyDoris
import SuperintendentChalmers, MrsKrabappel, MrLargo
# Milhouse — user saved as Millhouse.py (double L)
try:
    import Milhouse
except ModuleNotFoundError:
    import Millhouse as Milhouse

import Ralph, Martin
import Apu, Sanjay
import Barney, Patty, Selma

# These three have mixed-case filenames across different systems
# — try both and alias to a consistent name
try:
    import HansMoleman
except ModuleNotFoundError:
    import Hansmoleman as HansMoleman   # user saved as Hansmoleman.py

try:
    import SideshowBob
except ModuleNotFoundError:
    import Slideshowbob as SideshowBob  # user saved as Slideshowbob.py

try:
    import KentBrockman
except ModuleNotFoundError:
    import Kentbrockman as KentBrockman  # user saved as Kentbrockman.py

import Krusty
from nelson import haw_haw_check
import character_base as _cb
from SceneView import ConversationLog, venue_name, sub_location
from StranglingSequence import should_strangle, run_strangling_sequence, homer_said_why_you_little
from Actions import run_action
from NelsonSequence import run_nelson_sequence

# ── Load settings ────────────────────────────────────────────────────────────
try:
    import Settings as _cfg
    _ENABLED      = _cfg.CHARACTERS
    _NELSON_SENS  = _cfg.NELSON_SENSITIVITY
except ImportError:
    _ENABLED      = {}
    _NELSON_SENS  = "medium"

def _active(module_name: str) -> bool:
    """Return True if this character is enabled in settings."""
    return _ENABLED.get(module_name, True)

# ── Character rosters ─────────────────────────────────────────────────────────

def _r(key, module, char):
    """Include character in roster only if enabled in settings."""
    return {key: char} if _active(module) else {}

FAMILY = {
    **_r("homer",   "Homer",   Homer.character),
    **_r("lisa",    "Lisa",    Lisa.character),
    **_r("bart",    "Bart",    Bart.character),
    **_r("marge",   "Marge",   Marge.character),
    **_r("maggie",  "Maggie",  Maggie.character),
}

SPRINGFIELD = {
    **_r("moe",          "moe",         moe.character),
    **_r("nelson",       "nelson",      nelson.character),
    **_r("bumblebeeman", "BumbleBeeMan",BumbleBeeMan.character),
}

PLANT_WORKERS = {
    **_r("lenny",      "Lenny",      Lenny.character),
    **_r("carl",       "Carl",       Carl.character),
    **_r("montyburns", "Montyburns", Montyburns.character),
}

NOTABLES = {
    **_r("comicbookguy", "Comicbookguy", Comicbookguy.character),
    **_r("mayorquimby",  "Mayorquimby",  Mayorquimby.character),
}

FLANDERS = {
    **_r("ned",  "Ned",  Ned.character),
    **_r("rod",  "Rod",  Rod.character),
    **_r("todd", "Todd", Todd.character),
}

SCHOOL = {
    **_r("skinner",                "Skinner",                Skinner.character),
    **_r("willie",                 "Willie",                 Willie.character),
    **_r("lunchladydoris",         "LunchLadyDoris",         LunchLadyDoris.character),
    **_r("superintendentchalmers", "SuperintendentChalmers", SuperintendentChalmers.character),
    **_r("mrskrabappel",           "MrsKrabappel",           MrsKrabappel.character),
    **_r("mrlargo",                "MrLargo",                MrLargo.character),
}

KIDS = {
    **_r("milhouse",   "Milhouse",  Milhouse.character),
    **_r("ralph",      "Ralph",     Ralph.character),
    **_r("martin",     "Martin",    Martin.character),
}

KWIKMART = {
    **_r("apu",    "Apu",    Apu.character),
    **_r("sanjay", "Sanjay", Sanjay.character),
}

ADULTS = {
    **_r("barney",       "Barney",       Barney.character),
    **_r("patty",        "Patty",        Patty.character),
    **_r("selma",        "Selma",        Selma.character),
    **_r("hansmoleman",  "HansMoleman",  HansMoleman.character),
}

MEDIA = {
    **_r("krusty",       "Krusty",       Krusty.character),
    **_r("sideshowbob",  "SideshowBob",  SideshowBob.character),
    **_r("kentbrockman", "KentBrockman", KentBrockman.character),
}

ALL_CHARS = {**FAMILY, **SPRINGFIELD, **PLANT_WORKERS,
             **NOTABLES, **FLANDERS, **SCHOOL,
             **KIDS, **KWIKMART, **ADULTS, **MEDIA}

NELSON_CHAR = nelson.character if _active("nelson") else None

# ── Conversation log ──────────────────────────────────────────────────────────
from character_base import get_scene
CONV_LOG = ConversationLog()

# ── Populate shared reference so SceneDirector can import it ─────────────────
_cb.ALL_CHARS_REF.update(ALL_CHARS)

# ── Initialise the AI Scene Director ─────────────────────────────────────────
try:
    from SceneDirector import SceneDirector
    DIRECTOR = SceneDirector(ALL_CHARS)
    DIRECTOR_ENABLED = True
except Exception as _e:
    print(f"[SceneDirector] Could not load: {_e}")
    DIRECTOR = None
    DIRECTOR_ENABLED = False

# ── Register director callback so name-triggers also update locations ─────────
def _director_cb(char_key: str, char_name: str, response: str):
    """Called by character_base after every response including name-triggers."""
    if not DIRECTOR_ENABLED or DIRECTOR is None or not response:
        return
    result = DIRECTOR.analyse(char_key, char_name, response)
    DIRECTOR.apply(result, react_fn=director_react)

_cb.SimpsonsCharacter._director_callback = _director_cb

# ── Banner ────────────────────────────────────────────────────────────────────

def _make_banner():
    count = len(ALL_CHARS)
    count_str = f"{count} characters. 0 chill. Nelson is watching."
    # pad to fit the box (content width = 60 chars)
    padded = f"║  {count_str:<58}║"
    return f"""
╔══════════════════════════════════════════════════════════════╗
║        🏙️   SPRINGFIELD TOWN CHAT   🏙️                       ║
╠══════════════════════════════════════════════════════════════╣
{padded}
╠══════════════════════════════════════════════════════════════╣
║  @homer / @lisa / @bart / @marge / @maggie                   ║
║  @moe / @nelson / @bumblebeeman                              ║
║  @lenny / @carl / @montyburns                                ║
║  @comicbookguy / @mayorquimby                                ║
║  @ned / @rod / @todd                                         ║
║  @skinner / @willie / @lunchladydoris                        ║
║  @superintendentchalmers / @mrskrabappel / @mrlargo          ║
╠══════════════════════════════════════════════════════════════╣
║  GROUP COMMANDS                                              ║
║  @all        — everyone replies                              ║
║  @family     — Homer, Lisa, Bart, Marge, Maggie              ║
║  @locals     — Moe, Nelson, BumbleBeeMan                     ║
║  @plant      — Lenny, Carl, MontyBurns                       ║
║  @notables   — ComicBookGuy, MayorQuimby                     ║
║  @flanders   — Ned, Rod, Todd                                ║
║  @school     — Skinner, Willie, Doris, Chalmers,             ║
║                MrsKrabappel, MrLargo                         ║
║  @kids       — Milhouse, Ralph, Martin                       ║
║  @kwikmart   — Apu, Sanjay                                   ║
║  @adults     — Barney, Patty, Selma, HansMoleman             ║
║  @media      — Krusty, SideshowBob, KentBrockman             ║
╠══════════════════════════════════════════════════════════════╣
║  /<speaker>:<listener> <msg>       — character to character  ║
║  /event <desc>                     — show event (white)      ║
║  /event:<group> <desc>             — event + group reacts    ║
║  [Location: char@char: desc]       — set location/activity   ║
║  /locate char@char: desc           — same as above           ║
║  /scene  (then /endscene)          — run a scene script      ║
║  /thoughts:<char> <prompt>         — private thoughts        ║
║  exit  — leave Springfield                                   ║
╚══════════════════════════════════════════════════════════════╝
"""

# ── Aliases so you don't have to type the full key every time ─────────────────

ALIASES = {
    "bumblebee":    "bumblebeeman",
    "burns":        "montyburns",
    "mrburns":      "montyburns",
    "cbg":          "comicbookguy",
    "comic":        "comicbookguy",
    "quimby":       "mayorquimby",
    "mayor":        "mayorquimby",
    "flanders":     "ned",
    "chalmers":     "superintendentchalmers",
    "superintendent": "superintendentchalmers",
    "krabappel":    "mrskrabappel",
    "edna":         "mrskrabappel",
    "largo":        "mrlargo",
    "doris":        "lunchladydoris",
    "lunchlady":    "lunchladydoris",
    "bob":          "sideshowbob",
    "sideshow":     "sideshowbob",
    "kent":         "kentbrockman",
    "brockman":     "kentbrockman",
    "moleman":      "hansmoleman",
    "hans":         "hansmoleman",
}

def resolve(name: str) -> str:
    """Resolve alias to canonical key."""
    return ALIASES.get(name, name)

# ── Nelson HA-HA interject ────────────────────────────────────────────────────

# Nelson sensitivity — extra patterns for "high", fewer for "low"
_NELSON_EXTRA = [
    r"\b(annoying|frustrating|boring|tired|upset|sad|crying|tears)\b",
    r"\b(wrong|mistake|messed up|messed it up|blew it|ruined it)\b",
    r"\b(lost|losing|loser|fail|failure)\b",
]

def nelson_interject(response: str, speaker_name: str):
    """
    Check if a response contains misfortune and run Nelson's full HA-HA
    sequence — walks over, points, delivers HA-HA, victim reacts, saunters off.
    """
    if NELSON_CHAR is None:
        return
    if _NELSON_SENS == "off":
        return
    if speaker_name.lower() == "nelson":
        return

    triggered = haw_haw_check(response, speaker_name)

    if not triggered and _NELSON_SENS == "high":
        import re as _re
        for pat in _NELSON_EXTRA:
            if _re.search(pat, response, re.IGNORECASE):
                triggered = True
                break

    if _NELSON_SENS == "low":
        import re as _re
        SEVERE = [r"\b(d'oh|doh)\b",
                  r"\b(fired|exploded|blew up|arrested|hospitalised)\b"]
        triggered = any(_re.search(p, response, re.IGNORECASE) for p in SEVERE)

    if not triggered:
        return

    # Find the victim's character key
    victim_key = None
    for key, char in ALL_CHARS.items():
        if char.name.lower() == speaker_name.lower():
            victim_key = key
            break

    if victim_key is None:
        return

    # Build a short misfortune description from the response
    words = response.strip().split()
    misfortune_desc = " ".join(words[:25]) + ("..." if len(words) > 25 else "")

    run_nelson_sequence(
        ALL_CHARS,
        victim_key=victim_key,
        misfortune_desc=misfortune_desc,
        conv_log=CONV_LOG,
    )

# ── Discussion helper ─────────────────────────────────────────────────────────

def director_react(event: str, targets: list):
    """Called by SceneDirector to fire an auto-event to specific characters."""
    WHITE = "\033[97m"
    BOLD  = "\033[1m"
    RESET = "\033[0m"
    print(f"\n{BOLD}{WHITE}{'─'*60}{RESET}")
    print(f"{BOLD}{WHITE}  [Auto-Event] {event}{RESET}")
    print(f"{BOLD}{WHITE}{'─'*60}{RESET}")
    for key in targets:
        char = ALL_CHARS.get(key.lower())
        if char:
            print(f"\n{char.color}[{char.name.upper()}]:{char.reset} ", end="")
            response = char.get_response(
                f"The following just happened: \"{event}\". React in character.",
                sender="[Auto-Event]"
            )
            nelson_interject(response, char.name)


def record_speech(speaker_key: str, char, response: str):
    """Record a speech entry into the conversation log."""
    scene_tag = get_scene(char.location)
    CONV_LOG.record("speech", char.name, scene_tag,
                    char.location, response, char.color)


def run_director(speaker_key: str, speaker_name: str, response: str, context: str = ""):
    """Run director analysis after a character speaks."""
    char = ALL_CHARS.get(speaker_key)
    if char:
        record_speech(speaker_key, char, response)
    # Check if Homer said WHY YOU LITTLE → trigger strangling sequence
    check_strangling(speaker_key, response)
    if not DIRECTOR_ENABLED or DIRECTOR is None:
        return
    result = DIRECTOR.analyse(speaker_key, speaker_name, response, context)
    DIRECTOR.apply(result, react_fn=director_react)


def check_strangling(speaker_key: str, text: str):
    """
    Fires the strangling sequence when HOMER says WHY YOU LITTLE.
    Homer's rage response is already printed — we skip steps 1-2
    and jump straight to the physical sequence.
    """
    if speaker_key != "homer":
        return
    if not homer_said_why_you_little(text):
        return
    homer = ALL_CHARS.get("homer")
    bart  = ALL_CHARS.get("bart")
    if not homer or not bart:
        return
    from character_base import get_scene as _gs
    if _gs(homer.location) != _gs(bart.location):
        return
    # Homer already said WHY YOU LITTLE — skip to physical sequence
    run_strangling_sequence(ALL_CHARS, conv_log=CONV_LOG,
                            skip_homer_rage=True)


def group_discussion(message: str, roster: dict, label: str):
    print(f"\n{'─'*60}")
    print(f"  {label}")
    print(f"{'─'*60}")
    for name, char in roster.items():
        print(f"\n{char.color}[{char.name.upper()}]:{char.reset} ", end="")
        response = char.get_response(message, sender="User")
        nelson_interject(response, char.name)
        run_director(name, char.name, response)  # records to CONV_LOG
        check_strangling(name, response)

# ── Group command table ───────────────────────────────────────────────────────

GROUP_COMMANDS = {
    "@all ":       (ALL_CHARS,    "🏙️  ALL OF SPRINGFIELD",       5),
    "@family ":    (FAMILY,       "🏠  SIMPSON FAMILY",            8),
    "@locals ":    (SPRINGFIELD,  "🍺  SPRINGFIELD LOCALS",        8),
    "@plant ":     (PLANT_WORKERS,"☢️   NUCLEAR PLANT",             7),
    "@notables ":  (NOTABLES,     "🎩  SPRINGFIELD NOTABLES",      10),
    "@flanders ":  (FLANDERS,     "🙏  THE FLANDERS FAMILY",       10),
    "@school ":    (SCHOOL,       "🏫  SPRINGFIELD ELEMENTARY",    8),
}

# ── Main REPL ─────────────────────────────────────────────────────────────────

def main():
    global DIRECTOR_ENABLED
    print(_make_banner())

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSo long, Springfield!")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower == "exit":
            print("D'oh! Leaving Springfield...")
            break

        # ── Analyse user input first — update ALL locations before responding ──
        _raw_input = user_input
        for _pfx in ("@all ","@family ","@school ","@plant ","@locals ",
                     "@flanders ","@kids ","@adults ","@media ","@notables ","@kwikmart "):
            if lower.startswith(_pfx):
                _raw_input = user_input[len(_pfx):]
                break
        if _raw_input and not _raw_input.startswith("/") and DIRECTOR_ENABLED and DIRECTOR:
            _result = DIRECTOR.analyse("user", "User", _raw_input,
                                       context="This is a USER command/message — "
                                       "update ALL character locations that this implies.")
            DIRECTOR.apply(_result)

        # Group commands
        matched = False
        for prefix, (roster, label, trim) in GROUP_COMMANDS.items():
            if lower.startswith(prefix):
                msg = user_input[trim:].strip()
                if msg:
                    group_discussion(msg, roster, label)
                matched = True
                break
        if matched:
            continue

        # @character <message>
        if user_input.startswith("@"):
            parts = user_input[1:].split(" ", 1)
            if len(parts) < 2:
                print("Usage: @<character> <message>")
                continue
            name_key = resolve(parts[0].lower())
            message  = parts[1]
            char = ALL_CHARS.get(name_key)
            if not char:
                print(f"Unknown character '{name_key}'.")
                print(f"Available: {', '.join(list(ALL_CHARS.keys())[:8])}... (see banner for full list)")
                continue
            print(f"\n{char.color}[{char.name.upper()}]:{char.reset} ", end="")
            response = char.get_response(message, sender="User")
            nelson_interject(response, char.name)
            run_director(name_key, char.name, response)  # also records to CONV_LOG
            check_strangling(name_key, response)
            continue

        # [Location: char1@char2: description]  — set location/activity
        # Also accepts /locate char1@char2: description
        if lower.startswith("[location:") or lower.startswith("/locate "):
            WHITE = "\033[97m"
            RESET = "\033[0m"
            DIM   = "\033[2m"

            # normalise both syntaxes to "char(s): description"
            if lower.startswith("[location:"):
                inner = user_input[len("[location:"):].rstrip("]").strip()
            else:
                inner = user_input[len("/locate "):].strip()

            if ":" not in inner:
                print("Usage: [Location: char1@char2: description]")
                print("       /locate char1@char2: description")
                continue

            char_part, _, desc = inner.partition(":")
            desc = desc.strip()
            names = [n.strip().lower() for n in char_part.split("@") if n.strip()]
            resolved_names = [resolve(n) for n in names]

            updated = []
            for key in resolved_names:
                char = ALL_CHARS.get(key)
                if char:
                    # split desc into location vs activity at first comma or "doing"
                    import re as _re
                    m = _re.match(r"^(.*?)\s+(?:doing|wearing|drinking|eating|sitting|standing|working|playing|watching|holding|carrying|lying)\s+(.*)$", desc, _re.IGNORECASE)
                    if m:
                        loc, act = m.group(1).strip(), desc
                    else:
                        loc, act = desc, ""
                    char.set_location(loc, act)
                    updated.append(char.name)

            if updated:
                print(f"{DIM}{WHITE}[Location set] {', '.join(updated)}: {desc}{RESET}")
            else:
                print(f"No matching characters found in: {char_part}")
            continue

        # /scene  — run a multi-line script automatically
        # Type /scene then hit enter, paste your script, end with /endscene
        if lower.strip() == "/scene":
            WHITE = "\033[97m"
            RESET = "\033[0m"
            BOLD  = "\033[1m"
            DIM   = "\033[2m"
            print(f"{DIM}Enter scene script. End with /endscene on its own line.{RESET}")
            print(f"{DIM}Supported lines:{RESET}")
            print(f"{DIM}  [Location: char@char: description]{RESET}")
            print(f"{DIM}  [Event] description{RESET}")
            print(f"{DIM}  [Event:group] description{RESET}")
            print(f"{DIM}  CharName: what they say (narrated line){RESET}")
            print(f"{DIM}  # comment lines are ignored{RESET}")
            lines = []
            while True:
                try:
                    line = input("  scene> ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if line.lower() == "/endscene":
                    break
                lines.append(line)

            print(f"\n{BOLD}{WHITE}{'═'*60}{RESET}")
            print(f"{BOLD}{WHITE}  🎬  SCENE START{RESET}")
            print(f"{BOLD}{WHITE}{'═'*60}{RESET}")

            import time as _time

            for line in lines:
                if not line or line.startswith("#"):
                    continue
                lo = line.lower()

                # ── [Location: ...] ───────────────────────────────────────
                if lo.startswith("[location:"):
                    inner = line[len("[location:"):].rstrip("]").strip()
                    if ":" in inner:
                        char_part, _, desc = inner.partition(":")
                        desc = desc.strip()
                        names = [resolve(n.strip().lower()) for n in char_part.split("@")]
                        updated = []
                        for key in names:
                            char = ALL_CHARS.get(key)
                            if char:
                                char.set_location(desc, desc)
                                updated.append(char.name)
                        print(f"\n{DIM}{WHITE}[Location] {', '.join(updated)}: {desc}{RESET}")
                    continue

                # ── [Event] or [Event:group] ──────────────────────────────
                if lo.startswith("[event"):
                    # parse [Event] or [Event:family] etc.
                    import re as _re
                    m = _re.match(r"\[event(?::([a-z]+))?\]\s*(.*)", line, _re.IGNORECASE)
                    if m:
                        group_key   = (m.group(1) or "").lower()
                        description = m.group(2).strip()
                    else:
                        group_key, description = "", line

                    roster_map = {
                        "":         (ALL_CHARS,     ""),
                        "all":      (ALL_CHARS,     "Everyone"),
                        "family":   (FAMILY,        "Simpson Family"),
                        "school":   (SCHOOL,        "Springfield Elementary"),
                        "plant":    (PLANT_WORKERS, "Power Plant"),
                        "locals":   (SPRINGFIELD,   "Springfield Locals"),
                        "flanders": (FLANDERS,      "Flanders Family"),
                        "notables": (NOTABLES,      "Springfield Notables"),
                    }

                    # if no group, find characters whose location is relevant
                    # by checking if any ALL_CHARS key appears in the description
                    if group_key == "":
                        involved = {}
                        desc_lo = description.lower()
                        for key, char in ALL_CHARS.items():
                            if (char.name.lower() in desc_lo or
                                    key in desc_lo or
                                    # characters at the same location react
                                    any(word in char.location.lower()
                                        for word in desc_lo.split() if len(word) > 3)):
                                involved[key] = char
                        roster = involved if involved else {}
                    else:
                        roster, _ = roster_map.get(group_key, (ALL_CHARS, ""))

                    print(f"\n{BOLD}{WHITE}{'─'*60}{RESET}")
                    print(f"{BOLD}{WHITE}  [Event] {description}{RESET}")
                    print(f"{BOLD}{WHITE}{'─'*60}{RESET}")

                    if roster:
                        event_prompt = (
                            f"The following event just happened around you: \"{description}\". "
                            f"React naturally and in character. "
                            f"Remember where you are and what you were doing."
                        )
                        for name, char in roster.items():
                            print(f"\n{char.color}[{char.name.upper()}]:{char.reset} ", end="")
                            response = char.get_response(event_prompt, sender="[Event]")
                            nelson_interject(response, char.name)
                    continue

                # ── CharName: narrated line ───────────────────────────────
                if ":" in line:
                    char_name, _, narration = line.partition(":")
                    char_name = char_name.strip()
                    narration = narration.strip()
                    key = resolve(char_name.lower())
                    char = ALL_CHARS.get(key)
                    if char and narration:
                        print(f"\n{char.color}[{char.name.upper()}]:{char.reset} ", end="")
                        char.get_response(
                            f"Say this in your own voice and character: {narration}",
                            sender="[Scene]"
                        )
                        continue

                # ── Plain text — print as narration ──────────────────────
                print(f"\n{DIM}{WHITE}  {line}{RESET}")

            print(f"\n{BOLD}{WHITE}{'═'*60}{RESET}")
            print(f"{BOLD}{WHITE}  🎬  SCENE END{RESET}")
            print(f"{BOLD}{WHITE}{'═'*60}{RESET}\n")
            continue

        # /event <description>            — show event in white, no reactions
        # /event:<group> <description>    — show event, group reacts
        #   groups: all, family, school, plant, locals, flanders, notables
        if lower.startswith("/event"):
            WHITE = "\033[97m"
            RESET = "\033[0m"
            BOLD  = "\033[1m"

            rest = user_input[6:].strip()

            # work out if a group was specified e.g. /event:family
            group_roster = None
            if rest.startswith(":"):
                parts = rest[1:].split(" ", 1)
                if len(parts) < 2:
                    print("Usage: /event:<group> <description>")
                    print("       groups: all family school plant locals flanders notables")
                    continue
                group_key, description = parts[0].lower(), parts[1].strip()
                roster_map = {
                    "all":      (ALL_CHARS,     "Everyone"),
                    "family":   (FAMILY,        "Simpson Family"),
                    "school":   (SCHOOL,        "Springfield Elementary"),
                    "plant":    (PLANT_WORKERS, "Power Plant"),
                    "locals":   (SPRINGFIELD,   "Springfield Locals"),
                    "flanders": (FLANDERS,      "Flanders Family"),
                    "notables": (NOTABLES,      "Springfield Notables"),
                }
                if group_key not in roster_map:
                    print(f"Unknown group '{group_key}'.")
                    print("Available: all family school plant locals flanders notables")
                    continue
                group_roster, group_label = roster_map[group_key]
            else:
                description  = rest
                group_label  = ""

            if not description:
                print("Usage: /event <description>  or  /event:<group> <description>")
                continue

            # ── Print the event banner in white ───────────────────────────
            print(f"\n{BOLD}{WHITE}{'─'*60}{RESET}")
            print(f"{BOLD}{WHITE}  [Event] {description}{RESET}")
            if group_label:
                print(f"{BOLD}{WHITE}  Reacting: {group_label}{RESET}")
            print(f"{BOLD}{WHITE}{'─'*60}{RESET}")

            # Record event in log
            CONV_LOG.record_event(description)

            # ── Have each character in the group react ────────────────────
            if group_roster:
                event_prompt = (
                    f"The following event just happened: \"{description}\". "
                    f"React naturally as your character. Stay in character."
                )
                for name, char in group_roster.items():
                    print(f"\n{char.color}[{char.name.upper()}]:{char.reset} ", end="")
                    response = char.get_response(event_prompt, sender="[Event]")
                    record_speech(name, char, response)
                    nelson_interject(response, char.name)
            continue

        # /thoughts:character <prompt>  — private internal monologue, never spoken
        if lower.startswith("/thoughts:") or lower.startswith("/think:"):
            rest = user_input.split(":", 1)[1] if ":" in user_input else ""
            parts = rest.split(" ", 1)
            if len(parts) < 2:
                print("Usage: /thoughts:<character> <what are you thinking about>")
                continue
            char_key = resolve(parts[0].lower())
            thought_prompt = parts[1]
            char = ALL_CHARS.get(char_key)
            if not char:
                print(f"Unknown character '{char_key}'.")
                continue
            char.think(thought_prompt)
            continue

        # /speaker:target1@target2@target3 <message>
        # Supports one target:  /bart:moe  prank call
        # Supports many:        /marge:bart@lisa  clean your rooms
        if user_input.startswith("/") and ":" in user_input:
            arrow_part, _, message = user_input[1:].partition(" ")
            parts = arrow_part.split(":")
            if len(parts) != 2:
                print("Usage: /<speaker>:<listener> <msg>")
                print("       /<speaker>:<listener1>@<listener2> <msg>")
                continue
            speaker_key  = resolve(parts[0].lower())
            # listeners split by @
            listener_keys = [resolve(k.lower()) for k in parts[1].split("@") if k]

            speaker = ALL_CHARS.get(speaker_key)
            if not speaker:
                print(f"Unknown speaker '{speaker_key}'.")
                continue

            if len(listener_keys) == 1:
                # single target — original behaviour
                reply = speaker.talk_to(listener_keys[0], message)
                if reply:
                    nelson_interject(reply, speaker.name)
            else:
                # multiple targets — new group talk
                speaker.talk_to_many(listener_keys, message)
            continue

        # [CharName action description]  — character performs a physical action
        # Must start with [ and NOT be a [SCENE], [Event], or [Location] line
        if (user_input.startswith("[") and
                not lower.startswith("[scene") and
                not lower.startswith("[event") and
                not lower.startswith("[location")):
            consumed = run_action(
                user_input,
                ALL_CHARS,
                ALIASES,
                director=DIRECTOR if DIRECTOR_ENABLED else None,
                conv_log=CONV_LOG,
                nelson_interject_fn=nelson_interject,
                run_director_fn=run_director,
            )
            if consumed:
                continue
            # If not consumed (no character matched) fall through to other handlers

        # /log  — show conversation log in scene format
        if lower.strip() == "/log":
            CONV_LOG.show()
            continue

        # /log <n>  — show last n entries
        if lower.startswith("/log "):
            try:
                n = int(lower.split()[1])
                CONV_LOG.show(last_n=n)
            except (IndexError, ValueError):
                print("Usage: /log <number>  e.g. /log 20")
            continue

        # /scenes  — scene switcher showing all venues and occupants
        if lower.strip() in ("/scenes", "/scene switcher"):
            CONV_LOG.show_scenes(ALL_CHARS)
            continue

        # /clearlog  — clear the conversation log
        if lower.strip() == "/clearlog":
            CONV_LOG.clear()
            continue

        # /locations  — show where everyone is right now
        if lower.strip() == "/locations":
            if DIRECTOR:
                DIRECTOR.show_locations()
            else:
                print("[SceneDirector not loaded]")
            continue

        # /director on|off  — toggle director analysis
        if lower.startswith("/director"):
            parts = lower.split()
            if len(parts) > 1 and parts[1] == "off":
                DIRECTOR_ENABLED = False
                print("[SceneDirector] Director OFF — locations still tracked, AI analysis paused.")
            elif len(parts) > 1 and parts[1] == "on":
                DIRECTOR_ENABLED = True
                print("[SceneDirector] Director ON.")
            else:
                status = "ON" if DIRECTOR_ENABLED else "OFF"
                print(f"[SceneDirector] Currently {status}. Use /director on or /director off.")
            continue

        # Bare input — default to @all
        print("Tip: use @homer, @ned, @skinner, @all, @school, @flanders etc.")
        print("     Defaulting to @all...\n")
        group_discussion(user_input, ALL_CHARS, "🏙️  ALL OF SPRINGFIELD")


if __name__ == "__main__":
    main()