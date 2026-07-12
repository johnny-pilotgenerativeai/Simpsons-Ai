"""
SceneDirector.py  —  AI-powered scene manager for Springfield Chat.

Runs after EVERY message. Aggressively updates ALL character locations.

DUAL-TERMINAL SETUP:
  Terminal 1:  python3 SpringfieldChat.py
  Terminal 2:  python3 SceneDirector.py        ← live feed via named pipe

The two processes communicate through a FIFO at /tmp/springfield_director.fifo.
No log file. Output streams in real-time including AI token-by-token generation.
"""

import json
import re
import ollama
from character_base import MODEL, ALL_CHARS_REF, get_scene
import bridge
from bridge import (
    send as _send, send_raw as _send_raw, Stream,
    scene_line, narrator_line, location_update, pause,
    WHITE, BOLD, DIM, RESET, ITALIC, GREEN, YELLOW, CYAN,
    RED, MAGENTA, GOLD,
)

# ── Default starting locations ────────────────────────────────────────────────
DEFAULT_LOCATIONS = {
    "homer":                   "at home, 742 Evergreen Terrace — on the couch watching TV",
    "marge":                   "at home, 742 Evergreen Terrace — in the kitchen",
    "bart":                    "at home, 742 Evergreen Terrace — on the couch watching TV",
    "lisa":                    "at home, 742 Evergreen Terrace — in her room playing saxophone",
    "maggie":                  "at home, 742 Evergreen Terrace — in the living room",
    "moe":                     "at Moe's Tavern — behind the bar",
    "nelson":                  "outside Springfield Elementary — loitering near the fence",
    "bumblebeeman":            "at Channel Ocho studios — on set",
    "lenny":                   "at Springfield Nuclear Power Plant — Sector 7-G",
    "carl":                    "at Springfield Nuclear Power Plant — Sector 7-G",
    "montyburns":              "at Springfield Nuclear Power Plant — in his office",
    "comicbookguy":            "at The Android's Dungeon — behind the counter",
    "mayorquimby":             "at Springfield Town Hall — in his office",
    "ned":                     "at home, 744 Evergreen Terrace — in the garden",
    "rod":                     "at home, 744 Evergreen Terrace — in his room praying",
    "todd":                    "at home, 744 Evergreen Terrace — with Rod",
    "skinner":                 "at Springfield Elementary — in his office",
    "willie":                  "at Springfield Elementary — tending the grounds",
    "lunchladydoris":          "at Springfield Elementary — in the cafeteria",
    "superintendentchalmers":  "driving around Springfield",
    "mrskrabappel":            "at Springfield Elementary — in classroom 4",
    "mrlargo":                 "at Springfield Elementary — in the music room",
    "milhouse":                "at Springfield Elementary — in classroom 4",
    "ralph":                   "at Springfield Elementary — in classroom 4",
    "martin":                  "at Springfield Elementary — in classroom 4",
    "apu":                     "at the Kwik-E-Mart — behind the counter",
    "sanjay":                  "at the Kwik-E-Mart — restocking shelves",
    "barney":                  "at Moe's Tavern — on his usual stool",
    "patty":                   "at the Springfield DMV — behind the counter",
    "selma":                   "at the Springfield DMV — behind the counter",
    "hansmoleman":             "somewhere in Springfield — something has just happened to him",
    "krusty":                  "at Channel 6 Studios — in the dressing room",
    "sideshowbob":             "in a prison cell at Springfield Penitentiary",
    "kentbrockman":            "at Channel 6 News studio — at the anchor desk",
}

# ── Quick keyword location map ────────────────────────────────────────────────
LOCATION_KEYWORDS = {
    "moe's tavern":        "at Moe's Tavern — at the bar",
    "moe's":               "at Moe's Tavern — at the bar",
    "tavern":              "at Moe's Tavern — at the bar",
    "nuclear plant":       "at Springfield Nuclear Power Plant",
    "power plant":         "at Springfield Nuclear Power Plant",
    "sector 7":            "at Springfield Nuclear Power Plant — Sector 7-G",
    "springfield elementary": "at Springfield Elementary",
    "classroom":           "at Springfield Elementary — in the classroom",
    "cafeteria":           "at Springfield Elementary — in the cafeteria",
    "kwik-e-mart":         "at the Kwik-E-Mart",
    "android's dungeon":   "at The Android's Dungeon",
    "town hall":           "at Springfield Town Hall",
    "church":              "at the First Church of Springfield",
    "hospital":            "at Springfield General Hospital",
    "couch":               "at home, 742 Evergreen Terrace — on the couch",
    "kitchen":             "at home, 742 Evergreen Terrace — in the kitchen",
    "dinner table":        "at home, 742 Evergreen Terrace — at the dinner table",
    "living room":         "at home, 742 Evergreen Terrace — in the living room",
    "backyard":            "at home, 742 Evergreen Terrace — in the backyard",
    "front yard":          "at home, 742 Evergreen Terrace — in the front yard",
    "yard":                "at home, 742 Evergreen Terrace — in the yard",
    "garden":              "at home, 742 Evergreen Terrace — in the garden",
    "roof":                "on the roof of Springfield Elementary",
    "park":                "at Springfield Park",
    "mall":                "at the Springfield Mall",
    "krusty burger":       "at Krusty Burger",
    "lard lad":            "at Lard Lad Donuts",
    "bowling":             "at Barney's Bowl-A-Rama",
    "outside":             "outside, 742 Evergreen Terrace",
    "street":              "on the street, Springfield",
    "upstairs":            "at home, 742 Evergreen Terrace — upstairs",
    "downstairs":          "at home, 742 Evergreen Terrace — downstairs",
    "basement":            "at home, 742 Evergreen Terrace — in the basement",
    "garage":              "at home, 742 Evergreen Terrace — in the garage",
    "school":              "at Springfield Elementary",
    "prison":              "in Springfield Penitentiary",
    "dmv":                 "at the Springfield DMV",
}

ACTIVITY_KEYWORDS = {
    "yard work":       "doing yard work",
    "mowing":          "mowing the lawn",
    "mow the lawn":    "mowing the lawn",
    "raking":          "raking leaves",
    "gardening":       "gardening",
    "cooking":         "cooking",
    "eating":          "eating",
    "watching tv":     "watching TV",
    "watching the game": "watching the game",
    "sleeping":        "sleeping",
    "drinking":        "drinking Duff Beer",
    "skateboarding":   "skateboarding",
    "playing saxophone": "playing saxophone",
    "reading":         "reading",
    "praying":         "praying",
    "serving":         "serving customers",
    "driving":         "driving",
    "overalls":        "wearing overalls, doing yard work",
}

GROUP_MOVES = [
    (re.compile(r"\b(yard\s*work|mow|rake|garden|outside|overalls)\b", re.IGNORECASE),
     ["bart", "lisa", "maggie", "homer"], "yard"),
    (re.compile(r"\b(dinner.{0,15}ready|supper.{0,15}ready|sit.{0,10}table|come.{0,10}eat)\b", re.IGNORECASE),
     ["bart", "lisa", "maggie", "homer", "marge"], "dinner table"),
    (re.compile(r"\b(come inside|get inside|inside now|come in)\b", re.IGNORECASE),
     ["bart", "lisa", "maggie"], "living room"),
    (re.compile(r"\b(bed\s*time|go to bed|time for bed|off to bed)\b", re.IGNORECASE),
     ["bart", "lisa", "maggie"], "bedroom"),
    (re.compile(r"\b(time for school|get to school|school bus|late for school)\b", re.IGNORECASE),
     ["bart", "lisa"], "school"),
]

_CALL_RE = re.compile(
    r"\b(kids?|children|boys?|girls?|bart|lisa|maggie|homer|ned|rod|todd|everyone|all of you)\b"
    r".{0,40}"
    r"\b(come|get|head|go|sit|come down|come inside|come to|go to|sit at)\b"
    r".{0,30}"
    r"\b(kitchen|table|dinner|yard|outside|upstairs|downstairs|living room|"
    r"couch|basement|garage|front|backyard|garden)\b",
    re.IGNORECASE
)

_MOVEMENT_RE = re.compile(
    r"\b(?:going to|heading to|on my way to|walking to|running to|"
    r"drove to|driving to|arrived at|just got to|i'm at|now at|"
    r"leaving for|heading over to|just arrived at|came to|"
    r"went to|going over to|going outside|heading outside|"
    r"coming inside|going inside|going upstairs|going downstairs)\s*"
    r"([a-z][a-z\s'\-]{1,30})?",
    re.IGNORECASE
)


class SceneDirector:
    """
    Full-authority AI scene director with live pipe streaming.
    """

    SYSTEM_PROMPT = """
You are the omniscient scene director for the Simpsons. You have FULL AUTHORITY
over all character locations and activities. You run after EVERY message.

You receive:
- Complete current location of every character
- Last 15 lines of conversation
- The latest message

Return ONLY a valid JSON object. No prose. No markdown.

JSON schema:
{
  "locations": {
    "bart": "at home, 742 Evergreen Terrace — in the backyard doing yard work",
    "lisa": "at home, 742 Evergreen Terrace — in the backyard doing yard work"
  },
  "event": "optional scene event to fire",
  "event_targets": ["key1", "key2"],
  "narrator": "optional dry one-liner max 12 words",
  "mood": "calm|tense|chaos|heartwarming|funny"
}

LOCATION UPDATE RULES — BE AGGRESSIVE, BE THOROUGH:
1. GROUP MOVEMENTS: If the conversation implies a group activity, update ALL.
2. IMPLIED MOVEMENT: Talking about doing something = already doing it.
3. AUTHORITY CALLS: "kids come inside" = move all kids inside.
4. ACTIVITY UPDATES: Update the activity part (after —) freely.
5. CONTEXT: Use the FULL conversation — not just the last message.
6. WHEN IN DOUBT UPDATE: Better to update too many than too few.
7. ONLY MOVE SCENE-RELEVANT characters.

Return "locations": {} ONLY if truly nothing changed.
Return ONLY the JSON.
"""

    def __init__(self, all_chars: dict):
        self.all_chars = all_chars
        self.log: list[str] = []
        self.mood = "calm"
        self._initialise_locations()

    def _initialise_locations(self):
        for key, char in self.all_chars.items():
            loc = DEFAULT_LOCATIONS.get(key, "somewhere in Springfield")
            char.set_location(loc)
        msg = f"INIT  All {len(self.all_chars)} character locations set"
        print(f"{DIM}{WHITE}[SceneDirector] All {len(self.all_chars)} "
              f"character locations initialised.{RESET}")
        _send(msg)

    # ── Scene helpers ─────────────────────────────────────────────────────────

    def get_characters_at_scene(self, scene_tag: str) -> dict:
        return {k: c for k, c in self.all_chars.items()
                if get_scene(c.location) == scene_tag}

    def get_scene_of(self, char_key: str) -> str:
        char = self.all_chars.get(char_key)
        return get_scene(char.location) if char else ""

    def characters_by_scene(self) -> dict[str, dict]:
        scenes: dict[str, dict] = {}
        for key, char in self.all_chars.items():
            tag = get_scene(char.location)
            scenes.setdefault(tag, {})[key] = char
        return scenes

    # ── Fast layer 1: keyword self-movement ───────────────────────────────────

    def _quick_infer(self, speaker_key: str, text: str):
        m = _MOVEMENT_RE.search(text)
        if not m:
            return
        dest_raw = (m.group(1) or "").strip().rstrip(".,!?").lower()
        for keyword, location in LOCATION_KEYWORDS.items():
            if keyword in dest_raw or dest_raw in keyword:
                char = self.all_chars.get(speaker_key)
                if char:
                    char.set_location(location)
                    msg = f"MOVE  {char.name} → {location}"
                    print(f"{DIM}{WHITE}  ↳ {msg}{RESET}")
                    _send(msg)
                return

    # ── Fast layer 2: activity update ─────────────────────────────────────────

    def _update_activity(self, speaker_key: str, text: str):
        text_lo = text.lower()
        for keyword, activity in ACTIVITY_KEYWORDS.items():
            if keyword in text_lo:
                char = self.all_chars.get(speaker_key)
                if char:
                    base = char.location.split("—")[0].strip()
                    new_loc = f"{base} — {activity}"
                    char.set_location(new_loc, activity)
                return

    # ── Fast layer 3: group movement ──────────────────────────────────────────

    def _check_group_moves(self, speaker_key: str, text: str):
        text_lo = text.lower()
        speaker_char = self.all_chars.get(speaker_key)
        speaker_loc  = speaker_char.location if speaker_char else ""

        m = _CALL_RE.search(text_lo)
        if m:
            called_word = m.group(1).lower()
            dest_word   = m.group(3).lower() if m.lastindex and m.lastindex >= 3 else ""
            dest        = LOCATION_KEYWORDS.get(dest_word, "")
            if not dest and dest_word:
                for kw, loc in LOCATION_KEYWORDS.items():
                    if dest_word in kw:
                        dest = loc
                        break
            if dest:
                if any(w in called_word for w in ("kid", "child", "everyone", "all")):
                    targets = ["bart", "lisa", "maggie", "homer"]
                elif "homer" in called_word:
                    targets = ["homer"]
                elif "ned" in called_word:
                    targets = ["ned"]
                elif "rod" in called_word or "todd" in called_word:
                    targets = ["rod", "todd"]
                else:
                    targets = [k for k in self.all_chars if k in called_word]
                moved = []
                for key in targets:
                    char = self.all_chars.get(key)
                    if char and key != speaker_key:
                        char.set_location(dest)
                        moved.append(char.name)
                if moved and speaker_char:
                    msg = f"CALL  {speaker_char.name} → {', '.join(moved)} → {dest}"
                    print(f"{DIM}{WHITE}  ↳ {msg}{RESET}")
                    _send(msg)
            return

        for pattern, target_keys, dest_keyword in GROUP_MOVES:
            if pattern.search(text_lo):
                dest = LOCATION_KEYWORDS.get(dest_keyword, "")
                if not dest:
                    continue
                speaker_scene = get_scene(speaker_loc)
                moved = []
                for key in target_keys:
                    char = self.all_chars.get(key)
                    if not char:
                        continue
                    if key == speaker_key or get_scene(char.location) == speaker_scene:
                        char.set_location(dest)
                        moved.append(char.name)
                if moved:
                    msg = f"GROUP  {', '.join(moved)} → {dest}"
                    print(f"{DIM}{WHITE}  ↳ {msg}{RESET}")
                    _send(msg)
                break

    # ── AI layer: streaming analysis ──────────────────────────────────────────

    def analyse(self, speaker_key: str, speaker_name: str,
                text: str, context: str = "") -> dict:
        """
        Run fast layers then stream AI director response.
        Each token is written to the FIFO as it arrives.
        """
        self._quick_infer(speaker_key, text)
        self._update_activity(speaker_key, text)
        self._check_group_moves(speaker_key, text)

        state_lines = []
        for key, char in self.all_chars.items():
            state_lines.append(f"  {char.name} ({key}): {char.location}")
        state = "\n".join(state_lines)

        self.log.append(f"{speaker_name}: {text[:200]}")
        if len(self.log) > 15:
            self.log = self.log[-15:]
        log_text = "\n".join(self.log)

        # Signal the monitor that analysis is starting
        _send(f"━━━ ANALYSE  {speaker_name}: {text[:60]!r}")

        prompt = (
            f"FULL CHARACTER STATE:\n{state}\n\n"
            f"CONVERSATION (last 15 lines):\n{log_text}\n\n"
            f"LATEST — {speaker_name} says:\n\"{text[:400]}\"\n"
            f"{('CONTEXT: ' + context) if context else ''}\n\n"
            f"Update ALL locations that need changing. Be thorough. Return JSON only."
        )

        try:
            # ── Stream tokens live through bridge ──────────────────────
            with Stream() as st:
                st.writeline("━━━ AI >>> ")
                ollama_stream = ollama.chat(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user",   "content": prompt},
                    ],
                    stream=True,
                )
                raw = ""
                for chunk in ollama_stream:
                    part = chunk["message"]["content"]
                    raw += part
                    st.write(part)   # token streams live to monitor
                st.write("\n")

            raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
            result = json.loads(raw)

            # Pretty-print result to pipe
            locs = result.get("locations", {})
            if locs:
                _send(f"── LOCATIONS ({len(locs)} changes):")
                for k, v in locs.items():
                    _send(f"   {k} → {v}")
            if result.get("narrator"):
                _send(f"── NARRATOR: {result['narrator']}")
            if result.get("event"):
                _send(f"── EVENT: {result['event']}")
            if result.get("mood"):
                _send(f"── MOOD: {result['mood']}")

            return result
        except Exception as e:
            _send(f"── ERROR: {e}")
            return {"locations": {}}

    # ── Apply director result ─────────────────────────────────────────────────

    def apply(self, result: dict, react_fn=None):
        if not result:
            return

        updated = []
        for key, new_loc in result.get("locations", {}).items():
            char = self.all_chars.get(key.lower())
            if char and new_loc and char.location != new_loc:
                char.set_location(new_loc)
                updated.append(f"{char.name} → {new_loc}")

        if updated:
            print(f"\n{DIM}{WHITE}[Director] Location updates:{RESET}")
            for u in updated:
                print(f"{DIM}{WHITE}  ↳ {u}{RESET}")
                _send(f"APPLY  {u}")

        narrator = result.get("narrator", "")
        if narrator:
            print(f"\n{ITALIC}{WHITE}  📺 {narrator}{RESET}")

        if result.get("mood"):
            self.mood = result["mood"]

        event   = result.get("event", "")
        targets = result.get("event_targets", [])
        if event and react_fn:
            react_fn(event, targets)

    # ── Manual location control ───────────────────────────────────────────────

    def set_location(self, char_keys: list[str], description: str):
        for key in char_keys:
            char = self.all_chars.get(key)
            if char:
                char.set_location(description)
                msg = f"MANUAL  {char.name} → {description}"
                print(f"{DIM}{WHITE}[Location] {char.name}: {description}{RESET}")
                _send(msg)

    # ── Display helpers ───────────────────────────────────────────────────────

    def _best_header(self, chars: dict) -> str:
        candidates = [c.location for c in chars.values()]
        indoor = [l for l in candidates
                  if not l.lower().startswith("outside")
                  and "loitering" not in l.lower()]
        pool = indoor if indoor else candidates
        best = max(pool, key=lambda l: len(l.split("—")[0]))
        return best.split("—")[0].strip()

    def show_locations(self):
        scenes = self.characters_by_scene()
        print(f"\n{BOLD}{WHITE}{'─'*62}{RESET}")
        print(f"{BOLD}{WHITE}  📍 SPRINGFIELD — CURRENT LOCATIONS{RESET}")
        print(f"{BOLD}{WHITE}{'─'*62}{RESET}")
        for scene_tag, chars in sorted(scenes.items()):
            header = self._best_header(chars)
            print(f"\n{WHITE}  📌 {header}{RESET}")
            for key, char in chars.items():
                activity = (f"  — {char.location.split('—')[1].strip()}"
                            if "—" in char.location else "")
                print(f"     {char.color}{char.name:<24}{RESET}"
                      f"{DIM}{WHITE}{activity}{RESET}")
        print(f"\n{BOLD}{WHITE}{'─'*62}{RESET}\n")

    def show_scene(self, scene_tag: str):
        chars = self.get_characters_at_scene(scene_tag)
        if not chars:
            print(f"[No characters in scene: {scene_tag}]")
            return
        print(f"\n{BOLD}{WHITE}Scene '{scene_tag}':{RESET}")
        for key, char in chars.items():
            print(f"  {char.color}{char.name}{RESET}: {char.location}")


# ── Standalone monitor — python3 SceneDirector.py ────────────────────────────

if __name__ == "__main__":
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    MAGENTA = "\033[95m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    WHITE  = "\033[97m"
    RESET  = "\033[0m"

    _ensure_fifo()

    print(f"{BOLD}{WHITE}╔══════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{WHITE}║   🎬  SCENE DIRECTOR — LIVE MONITOR                  ║{RESET}")
    print(f"{BOLD}{WHITE}║   Pipe: {FIFO_PATH:<44}║{RESET}")
    print(f"{BOLD}{WHITE}║   Run SpringfieldChat.py in another terminal          ║{RESET}")
    print(f"{BOLD}{WHITE}║   Ctrl+C to exit                                      ║{RESET}")
    print(f"{BOLD}{WHITE}╚══════════════════════════════════════════════════════╝{RESET}\n")
    print(f"{DIM}Waiting for Springfield activity...{RESET}\n")

    def colour_line(line: str) -> str:
        if line.startswith("━━━ ANALYSE"):
            return f"\n{BOLD}{CYAN}{line}{RESET}"
        elif line.startswith("── AI thinking:"):
            return f"{DIM}{WHITE}{line}{RESET}"
        elif line.startswith("── LOCATIONS"):
            return f"\n{BOLD}{GREEN}{line}{RESET}"
        elif line.strip().startswith("   ") and "→" in line:
            k, _, v = line.strip().partition("→")
            return f"   {YELLOW}{k.strip()}{RESET} → {GREEN}{v.strip()}{RESET}"
        elif line.startswith("── NARRATOR"):
            return f"{CYAN}{line}{RESET}"
        elif line.startswith("── EVENT"):
            return f"{MAGENTA}{line}{RESET}"
        elif line.startswith("── MOOD"):
            return f"{DIM}{line}{RESET}"
        elif line.startswith("── ERROR"):
            return f"{RED}{line}{RESET}"
        elif "MOVE" in line or "CALL" in line or "GROUP" in line:
            return f"{YELLOW}{line}{RESET}"
        elif "APPLY" in line:
            return f"{GREEN}{line}{RESET}"
        elif "MANUAL" in line:
            return f"{WHITE}{line}{RESET}"
        elif "INIT" in line:
            return f"{DIM}{GREEN}{line}{RESET}"
        return f"{DIM}{line}{RESET}"

    # Open FIFO for reading — blocks here until a writer connects
    print(f"{DIM}Opening pipe (will unblock when SpringfieldChat starts)...{RESET}")
    try:
        with open(FIFO_PATH, "r", encoding="utf-8", errors="replace") as pipe:
            print(f"{GREEN}✓ Connected.{RESET}\n")
            for line in pipe:
                line = line.rstrip("\n")
                if line:
                    print(colour_line(line))
    except KeyboardInterrupt:
        print(f"\n{DIM}Monitor closed.{RESET}")
    except Exception as e:
        print(f"{RED}Pipe error: {e}{RESET}")