"""
character_base.py
Shared base for all Simpsons AI characters.
Handles messaging, inter-character communication, location awareness,
and the Ollama chat loop.
"""

import importlib
import re
import ollama
from collections import deque

# ── Load settings ─────────────────────────────────────────────────────────────
try:
    import Settings as _cfg
    MODEL             = _cfg.MODEL
    MAX_TRIGGER_DEPTH = _cfg.TRIGGER_DEPTH
    _CHAR_ENABLED     = _cfg.CHARACTERS
    _NELSON_SENS      = _cfg.NELSON_SENSITIVITY
    _MEMORY_WINDOW    = _cfg.MEMORY_WINDOW if hasattr(_cfg, 'MEMORY_WINDOW') else 5
    _USE_CHROMA       = _cfg.USE_CHROMA if hasattr(_cfg, 'USE_CHROMA') else False
    _CHROMA_PERSIST   = _cfg.CHROMA_PERSIST if hasattr(_cfg, 'CHROMA_PERSIST') else False
    _CHROMA_PATH      = _cfg.CHROMA_PERSIST_PATH if hasattr(_cfg, 'CHROMA_PERSIST_PATH') else "./chroma_data"
except ImportError:
    MODEL             = "llama3.2:latest"
    MAX_TRIGGER_DEPTH = 2
    _CHAR_ENABLED     = {}
    _NELSON_SENS      = "medium"
    _MEMORY_WINDOW    = 5
    _USE_CHROMA       = False
    _CHROMA_PERSIST   = False
    _CHROMA_PATH      = "./chroma_data"

# ── Optional ChromaDB Memory ───────────────────────────────────────────────
# ChromaDB will only be used if USE_CHROMA is True in Settings AND chromadb is installed
CHROMA_AVAILABLE = False
try:
    if _USE_CHROMA:
        import chromadb
        from chromadb.utils import embedding_functions
        CHROMA_AVAILABLE = True
except ImportError:
    pass


# ── Memory Manager Classes ────────────────────────────────────────────────────

class ConversationMemory:
    """
    Simple sliding window memory that keeps the last N conversation exchanges.
    Each exchange = user message + assistant response.
    """
    def __init__(self, max_exchanges: int = 5, character_name: str = ""):
        self.max_exchanges = max_exchanges
        self.character_name = character_name
        self.exchanges: deque = deque(maxlen=max_exchanges)
    
    def add(self, user_message: str, assistant_response: str):
        """Add a new exchange to memory."""
        self.exchanges.append({
            "user": user_message,
            "assistant": assistant_response
        })
    
    def get_context(self, current_location: str = "") -> str:
        """Get formatted context string from recent exchanges."""
        if not self.exchanges:
            return ""
        
        context_parts = []
        for exchange in self.exchanges:
            context_parts.append(f"User: {exchange['user'][:200]}")
            context_parts.append(f"{self.character_name}: {exchange['assistant'][:200]}")
        
        context_str = "\n".join(context_parts[-6:])  # Last 6 lines (3 exchanges)
        
        if current_location:
            context_str += f"\n[Current location: {current_location}]"
        
        return context_str


class ChromaMemory:
    """
    Vector memory using ChromaDB for semantic search of past conversations.
    Only used if ChromaDB is available and USE_CHROMA is True.
    """
    def __init__(self, character_name: str, collection_name: str = "simpsons_memory"):
        self.character_name = character_name
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedding_function = None
        self._initialized = False
    
    def _init_client(self):
        """Lazy initialization of ChromaDB client."""
        if not CHROMA_AVAILABLE or self._initialized:
            return
        
        try:
            # Use persistent or in-memory client based on settings
            if _CHROMA_PERSIST:
                import os
                os.makedirs(_CHROMA_PATH, exist_ok=True)
                self.client = chromadb.PersistentClient(path=_CHROMA_PATH)
            else:
                self.client = chromadb.Client()
                
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            
            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name=f"{self.collection_name}_{self.character_name}",
                embedding_function=self.embedding_function
            )
            self._initialized = True
        except Exception as e:
            print(f"[ChromaDB] Failed to initialize for {self.character_name}: {e}")
            self._initialized = False
    
    def add(self, text: str, metadata: dict = None):
        """Add a memory entry."""
        if not CHROMA_AVAILABLE or not _USE_CHROMA:
            return
        
        self._init_client()
        if not self._initialized or not self.collection:
            return
        
        try:
            # Use text as both ID and document for simplicity
            # In production, use a proper ID scheme
            import hashlib
            doc_id = hashlib.md5(text.encode()).hexdigest()[:16]
            
            self.collection.add(
                documents=[text],
                metadatas=[metadata or {}],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"[ChromaDB] Failed to add memory for {self.character_name}: {e}")
    
    def query(self, query_text: str, n_results: int = 3) -> str:
        """Query relevant memories."""
        if not CHROMA_AVAILABLE or not _USE_CHROMA:
            return ""
        
        self._init_client()
        if not self._initialized or not self.collection:
            return ""
        
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            if results and results.get("documents") and results["documents"][0]:
                memories = results["documents"][0]
                return "\n".join(f"[Memory] {m[:300]}" for m in memories)
        except Exception as e:
            print(f"[ChromaDB] Failed to query memory for {self.character_name}: {e}")
        
        return ""


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
    "hansmoleman":             "Hansmoleman",
    # Media & celebs
    "krusty":                  "Krusty",
    "sideshowbob":             "Slideshowbob",
    "kentbrockman":            "Kentbrockman",
    "gil":                     "Gil",
    # Springfield Services
    "chiefwiggum":             "ChiefWiggum",
    "eddie":                   "Eddie",
    "lou":                     "Lou",
    "drnick":                  "DrNick",
    "drhibbert":               "DrHibbert",
    # Retirement Castle
    "grampa":                  "Grampa",
    "jasper":                  "Jasper",
    "oldjewishman":            "OldJewishMan",
    # Springfield Recurring
    "squeakyvoicedteen":       "SqueakyVoicedTeen",
    "yesguy":                  "YesGuy",
    "smithers":                "Smithers",
    "seacaptain":              "SeaCaptain",
    # Slideshow Mel
    "slideshowmel":            "SlideshowMel",
    # Sports & Entertainment
    "dredricktatum":           "DredrickTatum",
    "rainierwolfcastle":      "RainierWolfcastle",
    # Business & Administration
    "lindsaynaegle":           "LindsayNaegle",
    # Law & Order
    "judgeconstableharm":      "JudgeConstableHarm",
    "judgeconstablesnyder":   "JudgeConstableSnyder",
    # Springfield Elementary kids
    "jimbo":                   "Jimbo",
    "dolph":                   "Dolph",
    "kearny":                  "Kearny",
    "nina":                    "Nina",
    "sherri":                  "Sherri",
    "terri":                   "Terri",
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

    def __init__(self, name: str, system_prompt: str, color: str = "\033[0m", 
                 memory_window: int = None, use_chroma: bool = None):
        self.name     = name
        self.color    = color
        self.reset    = "\033[0m"
        self.location = "Springfield"
        self.activity = ""
        
        # Memory settings - use global defaults if not specified
        self.memory_window = memory_window if memory_window is not None else _MEMORY_WINDOW
        self.use_chroma = use_chroma if use_chroma is not None else _USE_CHROMA
        
        # Initialize memory systems
        self.conv_memory = ConversationMemory(max_exchanges=self.memory_window, character_name=self.name)
        self.chroma_memory = ChromaMemory(self.name) if self.use_chroma and CHROMA_AVAILABLE else None
        
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
            f"where you are: you are currently in {self.location}"
        )
        if self.activity:
            ctx += f", and you are {self.activity}"
        ctx += ". Never mention your location in brackets or parentheses "
        ctx += "in your response. Just speak naturally as your character.]"
        return ctx

    # ── Memory management ──────────────────────────────────────────────────────
    
    def clear_memory(self):
        """Clear all conversation memory."""
        self.conv_memory.exchanges.clear()
    
    def get_memory_summary(self) -> str:
        """Get a summary of what's in memory."""
        if not self.conv_memory.exchanges:
            return f"{self.name} has no recent conversation memory."
        
        count = len(self.conv_memory.exchanges)
        last_user = self.conv_memory.exchanges[-1].get("user", "")[:50]
        last_response = self.conv_memory.exchanges[-1].get("assistant", "")[:50]
        return f"{self.name} has {count} exchanges in memory. Last: User='{last_user}...' -> '{last_response}...'"

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
        
        # Add memory context from recent conversations
        memory_context = self.conv_memory.get_context(self.location)
        
        # Add ChromaDB memory if available
        chroma_context = ""
        if self.chroma_memory:
            chroma_context = self.chroma_memory.query(message)
        
        # Combine all context
        full_context = context
        if memory_context:
            full_context += f"\n[RECENT CONVERSATION CONTEXT]:\n{memory_context}"
        if chroma_context:
            full_context += f"\n[RELEVANT MEMORIES]:\n{chroma_context}"
        
        self.messages.append({
            "role": "user",
            "content": f"{full_context} [{sender} says]: {message}"
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
        
        # Store this exchange in conversation memory
        user_msg = f"[{sender} says]: {message}"
        self.conv_memory.add(user_msg, response)
        
        # Store in ChromaDB memory if available
        if self.chroma_memory:
            full_exchange = f"{sender}: {message}\n{self.name}: {response}"
            self.chroma_memory.add(full_exchange, {
                "character": self.name,
                "sender": sender,
                "location": self.location
            })
        
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