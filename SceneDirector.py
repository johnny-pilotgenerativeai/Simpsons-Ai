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
import Bridge

# ── Load simulation intensity setting ─────────────────────────────────────────
try:
    import settings as _cfg
    SIMULATION_INTENSITY = getattr(_cfg, 'SIMULATION_INTENSITY', "medium")
except ImportError:
    SIMULATION_INTENSITY = "medium"
from Bridge import (
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
    # Springfield Services
    "seacaptain":              "at Springfield Marina — on his boat",
    # Medical
    "drhibbert":               "at Springfield General Hospital — in his office",
    "drnick":                  "at his office — waiting for patients",
    # Police
    "chiefwiggum":             "at Springfield Police Station — eating donuts",
    "eddie":                   "at Springfield Police Station — at his desk",
    "lou":                     "at Springfield Police Station — at his desk",
    # Springfield Mafia
    "fattony":                 "at the Springfield Docks — in his office",
    "legs":                   "at the Springfield Docks — standing guard",
    "louie":                  "at the Springfield Docks — handling the books",
    "johnnytightlips":         "at the Springfield Docks — behind the wheel of the black car",
    # Retirement Castle
    "grampa":                  "at Springfield Retirement Castle — in his room",
    "jasper":                  "at Springfield Retirement Castle — in the common room",
    "oldjewishman":            "at Springfield Retirement Castle — playing cards",
    # Springfield Recurring
    "squeakyvoicedteen":       "at Springfield Mall — loitering",
    "yesguy":                  "at Springfield Town Hall — saying yes to everything",
    "smithers":                "at Springfield Nuclear Power Plant — at Mr. Burns' side",
    # Slideshow Mel
    "slideshowmel":            "at Springfield Penitentiary — visiting Sideshow Bob",
    # Sports & Entertainment
    "dredricktatum":           "at Springfield Boxing Gym — training",
    "rainierwolfcastle":      "at Channel Ocho studios — on the McBain set",
    # Business & Administration
    "lindsaynaegle":           "at Springfield Nuclear Power Plant — at Mr. Burns' side",
    # Law & Order
    "judgeconstableharm":      "at Springfield Courthouse — on the bench",
    "judgeconstablesnyder":   "at Springfield Courthouse — in chambers",
    # Springfield Elementary Kids
    "jimbo":                   "at Springfield Elementary — outside causing trouble",
    "dolph":                   "at Springfield Elementary — with Jimbo",
    "kearny":                  "at Springfield Elementary — with Jimbo and Dolph",
    "nina":                    "at Springfield Elementary — gossiping with Sherri and Terri",
    "sherri":                  "at Springfield Elementary — leading the popular girls",
    "terri":                   "at Springfield Elementary — strategizing with Sherri and Nina",
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
You are the omniscient scene director for Springfield. You run after EVERY
single message — including user commands. You have FULL AUTHORITY over ALL
character locations and activities.

Return ONLY a valid JSON object. No prose. No markdown. No fences.

EXACT FORMAT:
{
  "locations": {"char_key": "location description", ...},
  "event": "event description text only - no prefixes like 'narrator:'",
  "event_targets": ["char1", "char2"],
  "narrator": "brief commentary text only - no labels or prefixes",
  "mood": "calm|tense|chaos|heartwarming|funny"
}

EXAMPLE:
{
  "locations": {
    "bart": "at home, 742 Evergreen Terrace - in the backyard doing yard work",
    "homer": "at home, 742 Evergreen Terrace - in the backyard"
  },
  "event": "A little chaos in the morning",
  "event_targets": ["bart", "homer"],
  "narrator": "Typical morning at the Simpson household",
  "mood": "calm|tense|chaos|heartwarming|funny"
}

═══════════════════════════════════════════════════════════════
RULES - READ ALL OF THESE. APPLY ALL OF THESE. EVERY TIME.
═══════════════════════════════════════════════════════════════

RULE 1 - USER COMMANDS ARE MOVEMENT ORDERS:
If the sender is "User" and the message contains group tags or location words,
treat it as a DIRECT ORDER to move those characters immediately.
Examples:
  "@all let's go to Moe's"              -> move EVERYONE to Moe's Tavern
  "@family come to the kitchen"         -> move all family to kitchen
  "@school fire drill outside"          -> move all school chars outside
  "everyone outside for yard work"      -> move all present chars to yard
  "@bart go to school"                  -> move bart to Springfield Elementary
You MUST update every character the command applies to.

RULE 2 - GROUP MOVEMENTS - UPDATE ALL:
If ANY message implies a group is going somewhere or doing something together,
update EVERY member of that group. Never update just one when they move together.
Wrong: only moving homer when message says "family goes to Moe's"
Right: moving homer, marge, bart, lisa, maggie all to Moe's

RULE 3 - IMPLIED PRESENCE:
If a character is talking ABOUT being somewhere, they ARE there.
If Homer talks about sitting at the bar, he is at the bar.
If Bart talks about being in class, he is in class.
Update their location to reflect this immediately.

RULE 4 - ACTIVITY TRACKING:
Update the activity (after the -) on every response.
If Marge is cooking, write "at home, 742 Evergreen Terrace - cooking dinner"
If Bart is skateboarding, write "outside 742 Evergreen Terrace - skateboarding"
Never leave the activity blank if you know what they are doing.

RULE 5 - FULL CONTEXT:
Look at all 15 lines of conversation history. If 5 messages ago the family
agreed to go to Moe's, they are STILL at Moe's unless something changed.
Do NOT reset locations just because they weren't mentioned recently.

RULE 6 - WHEN IN DOUBT, UPDATE:
It is ALWAYS better to update too many locations than too few.
If there is any reasonable inference a character moved, update them.

RULE 7 - AUTHORITY CALLS MOVE EVERYONE:
"Marge calls kids to dinner"   -> move bart, lisa, maggie, homer to dinner table
"Skinner calls students in"    -> move all school kids inside
"Homer says come to Moe's"     -> move lenny, carl, barney to Moe's if mentioned
"come inside everyone"         -> move all outdoor characters inside

RULE 8 - EVERY RESPONSE SHOULD HAVE LOCATIONS:
Unless this is pure dialogue with zero movement or activity change,
your "locations" object should contain UPDATES. Empty {} should be rare.

Return ONLY the JSON. Nothing else.

{intensity_rules}
"""

    def __init__(self, all_chars: dict):
        self.all_chars = all_chars
        self.log: list[str] = []
        self.mood = "calm"
        self._initialise_locations()
        
        # Set intensity-based rules for the system prompt
        self._set_intensity_rules()

    def _initialise_locations(self):
        for key, char in self.all_chars.items():
            loc = DEFAULT_LOCATIONS.get(key, "somewhere in Springfield")
            char.set_location(loc)
        msg = f"INIT  All {len(self.all_chars)} character locations set"
        print(f"{DIM}{WHITE}[SceneDirector] All {len(self.all_chars)} "
              f"character locations initialised.{RESET}")
        _send(msg)

    def _set_intensity_rules(self):
        """Set the intensity-based event rules for the AI director."""
        if SIMULATION_INTENSITY == "high":
            intensity_rules = """
RULE 9 - DRAMATIC EVENT INTENSITY (HIGH):
You are encouraged to generate dramatic, high-stakes events that create
significant story developments. This includes:
- Major disasters (meltdowns, fires, accidents)
- Political events (elections, scandals, protests)
- Criminal activity (robberies, prison breaks, mafia operations)
- Natural disasters (tornadoes, storms)
- Major personal events (retirements, announcements, confrontations)
Generate events that feel like major plot points in a Springfield episode.
"""
        elif SIMULATION_INTENSITY == "low":
            intensity_rules = """
RULE 9 - EVENT INTENSITY (LOW):
Keep events minimal and low-key. Focus on:
- Everyday occurrences (squirrels, minor mishaps)
- Small character interactions
- Routine activities
- Subtle location changes
Avoid dramatic, high-stakes, or chaotic events. Keep the simulation calm.
"""
        else:  # medium
            intensity_rules = """
RULE 9 - EVENT INTENSITY (MEDIUM):
Generate a balanced mix of events:
- Common everyday occurrences
- Notable but not extreme situations
- Moderate character interactions
- Occasional small conflicts or surprises
Maintain a normal, varied Springfield atmosphere.
"""
        
        # Replace the placeholder in the class's SYSTEM_PROMPT
        self.SYSTEM_PROMPT = self.SYSTEM_PROMPT.format(intensity_rules=intensity_rules)
        
        # Print which intensity is active
        print(f"{DIM}{WHITE}[SceneDirector] Simulation intensity: {SIMULATION_INTENSITY}{RESET}")
        _send(f"INTENSITY  Simulation intensity set to {SIMULATION_INTENSITY}")

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

            # Clean up markdown fences and extract JSON
            raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
            
            # Try to extract JSON object - match balanced braces
            # Start from the end and work backwards to find the outermost JSON
            brace_count = 0
            json_start = -1
            json_end = -1
            # First pass: find all potential JSON objects
            candidates = []
            current_start = -1
            for i, c in enumerate(raw):
                if c == '{':
                    if current_start == -1:
                        current_start = i
                    brace_count += 1
                elif c == '}':
                    brace_count -= 1
                    if brace_count == 0 and current_start != -1:
                        candidates.append((current_start, i + 1))
                        current_start = -1
                    elif brace_count < 0:
                        # Unbalanced, reset
                        brace_count = 0
                        current_start = -1
            
            # Use the last/largest candidate (most likely the intended JSON)
            if candidates:
                json_start, json_end = candidates[-1]
                raw = raw[json_start:json_end]
            
            # Try to parse JSON - if it fails, return empty result instead of crashing
            try:
                result = json.loads(raw)
            except json.JSONDecodeError as e:
                _send(f"── JSON ERROR: {e}")
                _send(f"── RAW: {raw[:400]}")
                # Return empty result instead of crashing
                result = {"locations": {}}

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


# ── Standalone — python3 SceneDirector.py ───────────────────────────────────
# Redirects to bridge.py monitor (the socket-based live viewer)

if __name__ == "__main__":
    from Bridge import run_monitor
    run_monitor()