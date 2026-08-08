"""
settings.py  —  Springfield Chat Configuration
Edit this file to change the model or toggle characters on/off.
Changes take effect next time you run SpringfieldChat.py.
"""

# ── Ollama Model ──────────────────────────────────────────────────────────────
# Change this to any model you have pulled locally.
# Run 'ollama list' in your terminal to see what's available.
# Examples: "llama3.2:latest", "llama3.1:latest", "mistral:latest",
#           "gemma2:latest", "phi3:latest", "deepseek-r1:8b"

MODEL = "llama3.2:latest"


# ── Character Toggle ──────────────────────────────────────────────────────────
# Set a character to False to disable them completely.
# They won't respond in group chats (@all, @family etc.)
# and can't be addressed directly with @name.
# The file still needs to exist — just won't be loaded.

CHARACTERS = {

    # ── Simpson Family ────────────────────────────────────────────────────
    "Homer":                   True,
    "Lisa":                    True,
    "Bart":                    True,
    "Marge":                   True,
    "Maggie":                  True,

    # ── Springfield Locals ────────────────────────────────────────────────
    "moe":                     True,
    "nelson":                  True,
    "BumbleBeeMan":            True,

    # ── Power Plant ───────────────────────────────────────────────────────
    "Lenny":                   True,
    "Carl":                    True,
    "Montyburns":              True,

    # ── Springfield Notables ─────────────────────────────────────────────
    "Comicbookguy":            True,
    "Mayorquimby":             True,

    # ── Flanders Family ───────────────────────────────────────────────────
    "Ned":                     True,
    "Rod":                     True,
    "Todd":                    True,

    # ── Springfield Elementary ────────────────────────────────────────────
    "Skinner":                 True,
    "Willie":                  True,
    "LunchLadyDoris":          True,
    "SuperintendentChalmers":  True,
    "MrsKrabappel":            True,
    "MrLargo":                 True,

    # ── Springfield Elementary Kids ───────────────────────────────────────
    "Milhouse":                True,
    "Ralph":                   True,
    "Martin":                  True,
    "Jimbo":                   True,
    "Dolph":                   True,
    "Kearny":                  True,
    "Nina":                    True,
    "Sherri":                  True,
    "Terri":                   True,

    # ── Kwik-E-Mart ───────────────────────────────────────────────────────
    "Apu":                     True,
    "Sanjay":                  True,

    # ── Springfield Adults ────────────────────────────────────────────────
    "Barney":                  True,
    "Patty":                   True,
    "Selma":                   True,
    "Hansmoleman":             True,

    # ── Media & Celebs ────────────────────────────────────────────────────
    "Krusty":                  True,
    "Slideshowbob":            True,
    "Kentbrockman":           True,

    # ── Retirement Castle ─────────────────────────────────────────────────
    "Grampa":                  True,
    "Jasper":                  True,
    "OldJewishMan":            True,

    # ── Springfield Recurring ─────────────────────────────────────────────
    "SqueakyVoicedTeen":       True,
    "YesGuy":                  True,
    "Smithers":                True,
    "SlideshowMel":            True,
    "Gil":                     True,

    # ── Medical ───────────────────────────────────────────────────────────
    "DrNick":                  True,
    "DrHibbert":               True,

    # ── Springfield Services ──────────────────────────────────────────────
    "SeaCaptain":              True,

    # ── Police ────────────────────────────────────────────────────────────
    "ChiefWiggum":             True,
    "Eddie":                   True,
    "Lou":                     True,

    # ── Sports & Entertainment ───────────────────────────────────────────
    "DredrickTatum":           True,
    "RainierWolfcastle":      True,

    # ── Business & Administration ────────────────────────────────────────
    "LindsayNaegle":           True,

    # ── Law & Order ────────────────────────────────────────────────────────
    "JudgeConstableHarm":      True,
    "JudgeConstableSnyder":   True,

    # ── Springfield Mafia ─────────────────────────────────────────────
    "FatTony":                 True,
    "Legs":                   True,
    "Louie":                  True,
    "JohnnyTightLips":         True,
}


# ── Nelson HA-HA sensitivity ──────────────────────────────────────────────────
# How eagerly Nelson jumps in when misfortune is detected.
# "high"   — reacts to almost anything bad
# "medium" — reacts to clear misfortunes only (default)
# "low"    — only the most obvious disasters trigger him
# "off"    — Nelson never auto-interjects (can still be chatted to directly)

NELSON_SENSITIVITY = "high"


# ── Chain reaction depth ──────────────────────────────────────────────────────
# How many times a name-mention can trigger a chain of reactions.
# 0 = no chain reactions at all
# 1 = one level of reactions
# 2 = two levels (default)
# 3 = three levels (extreme)
# Warning: setting this high with many characters active can get very noisy!

TRIGGER_DEPTH = 3


# ── Simulation Intensity ──────────────────────────────────────────────────
# Controls how dramatic the auto-events are during simulation
# "low"    — only minor, everyday events (squirrels, spilled drinks, etc.)
# "medium" — mix of everyday and notable events (default)
# "high"   — includes major dramatic events (plant meltdowns, elections, disasters)
SIMULATION_INTENSITY = "high"


# ── Memory Configuration ──────────────────────────────────────────────────────
# 
# MEMORY_WINDOW: Number of recent conversation exchanges to remember per character
# (each exchange = 1 user message + 1 character response)
# Set to 0 to disable sliding window memory
MEMORY_WINDOW = 5

# USE_CHROMA: Enable ChromaDB vector memory for semantic search of past conversations
# Requires chromadb to be installed: pip install chromadb
# When enabled, each character will store their conversations in a vector database
# and retrieve relevant memories based on semantic similarity to current messages
# Set to False to use only sliding window memory (no dependencies required)
USE_CHROMA = False

# CHROMA_PERSIST: If True, ChromaDB collections will persist to disk
# Only relevant if USE_CHROMA is True
CHROMA_PERSIST = False

# CHROMA_PERSIST_PATH: Directory to store ChromaDB data
# Only relevant if USE_CHROMA and CHROMA_PERSIST are True
CHROMA_PERSIST_PATH = "./chroma_data"
