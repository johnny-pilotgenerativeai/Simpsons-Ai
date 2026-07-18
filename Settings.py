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

MODEL = "llama3.2:3b"


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

    # ── Kwik-E-Mart ───────────────────────────────────────────────────────
    "Apu":                     True,
    "Sanjay":                  True,

    # ── Springfield Adults ────────────────────────────────────────────────
    "Barney":                  True,
    "Patty":                   True,
    "Selma":                   True,
    "HansMoleman":             True,

    # ── Media & Celebs ────────────────────────────────────────────────────
    "Krusty":                  True,
    "SideshowBob":             True,
    "KentBrockman":            True,
}


# ── Nelson HA-HA sensitivity ──────────────────────────────────────────────────
# How eagerly Nelson jumps in when misfortune is detected.
# "high"   — reacts to almost anything bad
# "medium" — reacts to clear misfortunes only (default)
# "low"    — only the most obvious disasters trigger him
# "off"    — Nelson never auto-interjects (can still be chatted to directly)

NELSON_SENSITIVITY = "medium"


# ── Chain reaction depth ──────────────────────────────────────────────────────
# How many times a name-mention can trigger a chain of reactions.
# 0 = no chain reactions at all
# 1 = one level of reactions
# 2 = two levels (default)
# Warning: setting this high with many characters active can get very noisy!
TRIGGER_DEPTH = 5
