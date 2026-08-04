"""
character_base.py
Shared base for all Simpsons AI characters.
Handles messaging, inter-character communication, location awareness,
and the Ollama chat loop.
"""

import importlib
import re
import ollama

# ── Load settings ─────────────────────────────────────────────────────────────
try:
    import Settings as _cfg
    MODEL             = _cfg.MODEL
    MAX_TRIGGER_DEPTH = _cfg.TRIGGER_DEPTH
    _CHAR_ENABLED     = _cfg.CHARACTERS
    _NELSON_SENS      = _cfg.NELSON_SENSITIVITY
except ImportError:
    MODEL             = "llama3.2:latest"
    MAX_TRIGGER_DEPTH = 2
    _CHAR_ENABLED     = {}
    _NELSON_SENS      = "medium"

# ── Character module registry ─────────────────────────────────────────────────
CHARACTER_MODULES = {
    "homer":                   "Homer",
    "lisa":                    "Lisa",
    "bart":                    "Bart",
    "marge":                   "Marge",
    "maggie":                  "Maggie",
    "moe":                     "moe",
    "nelson":                  "nelson",
    "bumblebeeman":            "BumbleBeeMan",
    "lenny":                   "Lenny",
    "carl":                    "Carl",
    "montyburns":              "Montyburns",
    "comicbookguy":            "Comicbookguy",
    "mayorquimby":             "Mayorquimby",
    "ned":                     "Ned",
    "rod":                     "Rod",
    "todd":                    "Todd",
    "skinner":                 "Skinner",
    "willie":                  "Willie",
    "lunchladydoris":          "LunchLadyDoris",
    "superintendentchalmers":  "SuperintendentChalmers",
    "mrskrabappel":            "MrsKrabappel",
    "mrlargo":                 "MrLargo",
    # Springfield Elementary kids
    "milhouse":                "Milhouse",
    "ralph":                   "Ralph",
    "martin":                  "Martin",
    # Kwik-E-Mart
    "apu":                     "Apu",
    "sanjay":                  "Sanjay",
    # Springfield adults
    "barney":                  "Barney",
    "patty":                   "Patty",
    "selma":                   "Selma",
    "hansmoleman":             "HansMoleman",
    # Media & celebs
    "krusty":                  "Krusty",
    "sideshowbob":             "SideshowBob",
    "kentbrockman":            "KentBrockman",
    "gil":                     "Gil",
}

# ── Scene tags — normalise a location string to its main venue ────────────────
# Used to decide whether two characters are in the "same scene".
_SCENE_TAGS = [
    # ── Must check 744 BEFORE generic "evergreen terrace" ─────────────────
    ("744 evergreen",         "744evergreen"),
    ("flanders",              "744evergreen"),
    # ── 742 / Simpson house ───────────────────────────────────────────────
    ("742 evergreen",         "742evergreen"),
    ("742",                   "742evergreen"),
    ("simpson house",         "742evergreen"),
    # ── Only match "evergreen terrace" if not already caught above ────────
    # (handled by ordering — 744 is checked first)
    ("evergreen terrace",     "742evergreen"),
    # ── Moe's ─────────────────────────────────────────────────────────────
    ("moe's tavern",          "moes"),
    ("moe's",                 "moes"),
    ("moe tavern",            "moes"),
    ("tavern",                "moes"),
    # ── Power plant ───────────────────────────────────────────────────────
    ("nuclear power plant",   "powerplant"),
    ("power plant",           "powerplant"),
    ("sector 7",              "powerplant"),
    # ── Springfield Elementary — inside ───────────────────────────────────
    ("springfield elementary","elementary"),
    ("elementary school",     "elementary"),
    ("classroom",             "elementary"),
    ("cafeteria",             "elementary"),
    ("music room",            "elementary"),
    ("principal",             "elementary"),
    ("in his office",         "elementary"),   # Skinner's office
    # ── Outside the school is a SEPARATE scene ────────────────────────────
    ("outside springfield elementary", "elementary_outside"),
    ("outside elementary",    "elementary_outside"),
    ("school grounds",        "elementary_outside"),
    # ── Other venues ──────────────────────────────────────────────────────
    ("kwik-e-mart",           "kwikemart"),
    ("kwik e mart",           "kwikemart"),
    ("android's dungeon",     "androidsdungeon"),
    ("comic book",            "androidsdungeon"),
    ("town hall",             "townhall"),
    ("mayor",                 "townhall"),
    ("church",                "church"),
    ("hospital",              "hospital"),
    ("krusty burger",         "krustburger"),
    ("lard lad",              "lardlad"),
    ("springfield park",      "park"),
    ("springfield mall",      "mall"),
    ("leftorium",             "mall"),
    ("channel ocho",          "channelocho"),
    ("ocho studio",           "channelocho"),
]

def get_scene(location: str) -> str:
    """
    Normalise a location string to a short scene tag.
    Two characters with the same scene tag can hear each other.
    """
    lo = location.lower()
    for keyword, tag in _SCENE_TAGS:
        if keyword in lo:
            return tag
    # fallback: first 30 chars normalised
    return re.sub(r"[^a-z0-9]", "", lo[:30])


# ── Shared reference populated by SpringfieldChat ────────────────────────────
ALL_CHARS_REF: dict = {}


# ── Character helpers ─────────────────────────────────────────────────────────

def _get_character(name: str) -> "SimpsonsCharacter | None":
    """Lazily import and return a character instance by name (if enabled)."""
    key = name.lower()
    if key not in CHARACTER_MODULES:
        return None
    module_name = CHARACTER_MODULES[key]
    if not _CHAR_ENABLED.get(module_name, True):
        return None
    try:
        mod = importlib.import_module(module_name)
        return mod.character
    except ModuleNotFoundError:
        return None


def _is_enabled(module_name: str) -> bool:
    return _CHAR_ENABLED.get(module_name, True)


def _find_mentioned_names(text: str, exclude: list[str],
                          speaker_scene: str = "") -> list[str]:
    """
    Return character names mentioned in text who are in the SAME scene
    as the speaker. Characters in a different location cannot hear
    and will not trigger a reaction.

    If speaker_scene is empty, no location filtering is applied
    (used for /scene scripts and events).
    """
    found = []
    seen  = set(n.lower() for n in exclude)
    for name in CHARACTER_MODULES:
        if name in seen:
            continue
        if not re.search(rf"\b{name}\b", text, re.IGNORECASE):
            continue
        if speaker_scene:
            # only react if the mentioned character is in the same scene
            char = _get_character(name)
            if char is None:
                continue
            char_scene = get_scene(char.location)
            if char_scene != speaker_scene:
                continue   # different location — cannot hear
        found.append(name)
    return found


# ── Character base class ──────────────────────────────────────────────────────

class SimpsonsCharacter:
    """Base class for every Simpsons character AI."""

    # Director callback — set by SpringfieldChat after ALL_CHARS is built
    _director_callback = None   # callable(char_key, char_name, response)

    def __init__(self, name: str, system_prompt: str, color: str = "\033[0m"):
        self.name     = name
        self.color    = color
        self.reset    = "\033[0m"
        self.location = "Springfield"
        self.activity = ""
        # Inject universal first-person rule into every character
        full_prompt = system_prompt + """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UNIVERSAL RULES — APPLY TO EVERY SINGLE RESPONSE, NO EXCEPTIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. FIRST PERSON ALWAYS: Speak entirely in first person.
   Say "I think...", "I feel...", "I'm going to...", "I want..."
   NEVER narrate yourself: NOT "*Homer reaches for a donut*"
   NEVER use third person about yourself: NOT "Homer says..."
   NEVER describe your own actions in brackets, asterisks, or parentheses.
   RIGHT:  "Mmm... I could really go for a donut right now."
   WRONG:  "*Homer reaches for a donut* 'Mmm donut.'"

2. NO STAGE DIRECTIONS: Do not write your own physical actions as narration.
   If you want to convey an action, describe it through your words and tone.
   RIGHT:  "D'oh! I just knocked that over, didn't I."
   WRONG:  "*knocks thing over* D'oh!"

3. NO LOCATION NARRATION: Never state where you are in brackets.
   WRONG: "(Kitchen, 742 Evergreen Terrace) Well, I was just..."
   RIGHT: "Well, I was just cooking when..."

4. STAY IN CHARACTER: Every response should sound unmistakably like you.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        self.messages: list[dict] = [
            {"role": "system", "content": full_prompt}
        ]

    # ── Location ──────────────────────────────────────────────────────────────

    def set_location(self, location: str, activity: str = ""):
        self.location = location
        self.activity = activity if activity and activity != location else ""

    def get_scene(self) -> str:
        return get_scene(self.location)

    def is_colocated(self, other: "SimpsonsCharacter") -> bool:
        """True if both characters are in the same scene."""
        return self.get_scene() == other.get_scene()

    def get_state_context(self) -> str:
        """
        Returns a hidden internal context string injected before every prompt.
        Marked clearly as stage direction so characters never speak it aloud.
        """
        ctx = (
            f"[INTERNAL STAGE DIRECTION — DO NOT SAY THIS ALOUD, "
            f"DO NOT NARRATE YOUR LOCATION, this is just so you know "
            f"where you are: you are currently at {self.location}"
        )
        if self.activity:
            ctx += f", and you are {self.activity}"
        ctx += ". Never mention your location in brackets or parentheses "
        ctx += "in your response. Just speak naturally as your character.]"
        return ctx

    # ── Core chat ─────────────────────────────────────────────────────────────

    def get_response(self, message: str, sender: str = "User",
                     trigger_depth: int = 0,
                     ignore_location: bool = False) -> str:
        """
        Generate a response. Retries once on Ollama connection drop.
        Name-triggers only fire for co-located characters unless
        ignore_location=True (used by events and scene scripts).
        """
        context = self.get_state_context()
        self.messages.append({
            "role": "user",
            "content": f"{context} [{sender} says]: {message}"
        })

        MAX_RETRIES = 2
        response    = ""

        for attempt in range(MAX_RETRIES):
            try:
                stream = ollama.chat(
                    model=MODEL,
                    messages=self.messages,
                    stream=True,
                )
                response = ""
                for chunk in stream:
                    part = chunk["message"]["content"]
                    print(f"{self.color}{part}{self.reset}", end="", flush=True)
                    response += part
                break   # success

            except Exception as e:
                err = str(e)
                if attempt < MAX_RETRIES - 1:
                    import time as _t
                    print(f"\n{self.color}[{self.name}]\033[0m "
                          f"\033[2m connection lost, retrying...\033[0m",
                          flush=True)
                    _t.sleep(2)
                else:
                    if "disconnected" in err.lower() or "protocol" in err.lower():
                        hint = "Ollama disconnected — try: systemctl restart ollama"
                    elif "refused" in err.lower():
                        hint = "Ollama not running — try: ollama serve"
                    else:
                        hint = err[:80]
                    print(f"\n\033[91m[{self.name} — error: {hint}]\033[0m")
                    if self.messages and self.messages[-1]["role"] == "user":
                        self.messages.pop()
                    return ""

        self.messages.append({"role": "assistant", "content": response})
        print()

        # Name-triggers — only co-located characters react
        if trigger_depth < MAX_TRIGGER_DEPTH:
            my_scene = "" if ignore_location else self.get_scene()
            mentioned = _find_mentioned_names(
                response, exclude=[self.name], speaker_scene=my_scene
            )
            for name in mentioned:
                target = _get_character(name)
                if target is None:
                    continue
                trigger_msg = (
                    f"{self.name} just said: \"{response.strip()}\" "
                    f"— they mentioned your name. React naturally as {target.name}."
                )
                print(f"\n{target.color}[{target.name.upper()} — reacts]:{target.reset} ", end="")
                trigger_resp = target.get_response(trigger_msg, sender=self.name,
                                    trigger_depth=trigger_depth + 1)
                # Run director on triggered reactions too
                if SimpsonsCharacter._director_callback and trigger_resp:
                    key = target.name.lower()
                    SimpsonsCharacter._director_callback(key, target.name, trigger_resp)

        return response

    def send(self, message: str) -> str:
        print(f"\n{self.color}[{self.name.upper()}]:{self.reset} ", end="")
        return self.get_response(message, sender="User")

    # ── Inter-character talk ──────────────────────────────────────────────────

    def talk_to(self, character_name: str, message: str) -> str:
        """
        Two-step talk: speaker generates their line, target responds.
        Only works if both characters are in the same scene.
        """
        key = character_name.lower()
        if key not in CHARACTER_MODULES:
            print(f"[ERROR] Unknown character: '{character_name}'.")
            return ""
        if key == self.name.lower():
            print(f"[{self.name}] Can't talk to myself!")
            return ""

        target = _get_character(key)
        if target is None:
            print(f"[ERROR] Could not import '{CHARACTER_MODULES[key]}.py'.")
            return ""

        # ── Location check ────────────────────────────────────────────────
        if not self.is_colocated(target):
            DIM = "\033[2m"; RST = "\033[0m"
            print(f"{DIM}[{self.name} is at {self.location}]  "
                  f"[{target.name} is at {target.location}] — "
                  f"not in the same scene.{RST}")
            print(f"{DIM}Use /locate or [Location:] to move them first.{RST}")
            return ""

        # Step 1: Speaker generates their line
        print(f"\n{self.color}[{self.name.upper()}]:{self.reset} ", end="")
        spoken = self.get_response(
            f"You are about to talk to {target.name}. "
            f"Here is what you want to say: {message}. "
            f"Say it now in your own voice, directly to {target.name}.",
            sender="User", trigger_depth=MAX_TRIGGER_DEPTH
        )

        # Step 2: Target responds
        print(f"\n{target.color}[{target.name.upper()}]:{target.reset} ", end="")
        reply = target.get_response(spoken, sender=self.name)

        self.messages.append({
            "role": "user",
            "content": f"[{target.name} replied to you]: {reply}"
        })
        return reply

    # ── Multi-target talk ─────────────────────────────────────────────────────

    def talk_to_many(self, character_names: list[str], message: str):
        """
        Speak to multiple targets. Only co-located characters participate.
        """
        targets = []
        for name in character_names:
            key = name.lower()
            if key == self.name.lower():
                continue
            char = _get_character(key)
            if char is None:
                print(f"[ERROR] Unknown: '{key}'")
                continue
            if not self.is_colocated(char):
                DIM = "\033[2m"; RST = "\033[0m"
                print(f"{DIM}[Skipping {char.name} — different scene: {char.location}]{RST}")
                continue
            targets.append(char)

        if not targets:
            print("[No co-located targets found]")
            return

        target_names = ", ".join(t.name for t in targets)

        print(f"\n{self.color}[{self.name.upper()}]:{self.reset} ", end="")
        spoken = self.get_response(
            f"You are about to address {target_names} together. "
            f"Here is what you want to say: {message}. "
            f"Say it now in your own voice.",
            sender="User", trigger_depth=MAX_TRIGGER_DEPTH
        )

        conversation_so_far = self.name + ' said: "' + spoken.strip() + '"'
        for target in targets:
            print(f"\n{target.color}[{target.name.upper()}]:{target.reset} ", end="")
            reply = target.get_response(
                f"Conversation so far:\n{conversation_so_far}\nRespond as {target.name}.",
                sender=self.name
            )
            conversation_so_far += '\n' + target.name + ' replied: "' + reply.strip() + '"'

        self.messages.append({"role": "user",
                               "content": f"[You spoke to {target_names}]: {spoken.strip()}"})
        self.messages.append({"role": "assistant",
                               "content": f"[Conversation]: {conversation_so_far}"})

    # ── Private thoughts ──────────────────────────────────────────────────────

    def think(self, prompt: str) -> str:
        DIM = "\033[2m"; RST = "\033[0m"
        think_prompt = (
            f"Private internal thought — not spoken aloud. "
            f"Stay in character as {self.name}. Prompt: {prompt}"
        )
        thought_messages = [
            self.messages[0],
            {"role": "user", "content": think_prompt}
        ]
        print(f"\n{DIM}[{self.name.upper()} thinks]:{RST} ", end="")
        stream = ollama.chat(model=MODEL, messages=thought_messages, stream=True)
        thought = ""
        for chunk in stream:
            part = chunk["message"]["content"]
            print(f"{DIM}{part}{RST}", end="", flush=True)
            thought += part
        print()
        return thought

    # ── Standalone REPL ───────────────────────────────────────────────────────

    def run(self):
        others = [n for n in CHARACTER_MODULES if n != self.name.lower()]
        print(f"\n{'='*60}")
        print(f"  Chatting with {self.name}!")
        print(f"  Type 'exit' to quit.")
        print(f"  /talk <character> <message>  — speak to another character")
        print(f"  /thoughts <prompt>           — private internal monologue")
        print(f"  Available: {', '.join(others)}")
        print(f"{'='*60}\n")

        while True:
            user_input = input(f"You: {self.name}: ").strip()
            if not user_input:
                continue
            if user_input.lower() == "exit":
                print(f"\n{self.name}: Later!")
                break
            elif user_input.lower().startswith("/talk "):
                parts = user_input[6:].split(" ", 1)
                if len(parts) < 2:
                    print("Usage: /talk <character> <message>")
                    continue
                self.talk_to(parts[0], parts[1])
            elif user_input.lower().startswith("/thoughts "):
                self.think(user_input[10:].strip())
            else:
                self.send(user_input)