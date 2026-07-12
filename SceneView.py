"""
SceneView.py  —  Scene-aware conversation display for Springfield Chat.

Tracks all messages, groups them by venue and sub-location, and renders
the conversation log in the format:

  SIMPSONS HOUSE
  --Kitchen--
  Marge: ...
  Lisa: ...
  --Couch--
  Bart: ...

  MOE'S TAVERN
  Homer: ...

  SPRINGFIELD ELEMENTARY
  [SCENE] A loud bang went off
  Skinner: ...
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import re

# ── ANSI colours ──────────────────────────────────────────────────────────────
WHITE  = "\033[97m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"
ITALIC = "\033[3m"
YELLOW = "\033[93m"

# ── Venue display names ───────────────────────────────────────────────────────
# Maps scene tag → friendly ALL-CAPS display name shown as the venue header.
VENUE_NAMES = {
    "742evergreen":       "SIMPSONS HOUSE",
    "744evergreen":       "FLANDERS HOUSE",
    "moes":               "MOE'S TAVERN",
    "powerplant":         "SPRINGFIELD NUCLEAR POWER PLANT",
    "elementary":         "SPRINGFIELD ELEMENTARY",
    "elementary_outside": "OUTSIDE SPRINGFIELD ELEMENTARY",
    "kwikemart":          "KWIK-E-MART",
    "androidsdungeon":    "THE ANDROID'S DUNGEON",
    "townhall":           "SPRINGFIELD TOWN HALL",
    "church":             "FIRST CHURCH OF SPRINGFIELD",
    "hospital":           "SPRINGFIELD GENERAL HOSPITAL",
    "krustburger":        "KRUSTY BURGER",
    "lardlad":            "LARD LAD DONUTS",
    "park":               "SPRINGFIELD PARK",
    "mall":               "SPRINGFIELD MALL",
    "channelocho":        "CHANNEL OCHO STUDIOS",
    "channel6":           "CHANNEL 6 NEWS STUDIO",
    "prison":             "SPRINGFIELD PENITENTIARY",
    "dmv":                "SPRINGFIELD DMV",
    "bowlarama":          "BARNEY'S BOWL-A-RAMA",
}

def venue_name(scene_tag: str, fallback_location: str) -> str:
    """Return a display-friendly venue name for a scene tag."""
    if scene_tag in VENUE_NAMES:
        return VENUE_NAMES[scene_tag]
    # Derive from location string — capitalise the venue part
    venue = fallback_location.split("—")[0].strip()
    return venue.upper()


def sub_location(location: str) -> str:
    """Extract the sub-location (after —) from a full location string."""
    if "—" in location:
        return location.split("—", 1)[1].strip()
    return ""


def format_sub(sub: str) -> str:
    """Format sub-location as --Title Case--"""
    if not sub:
        return ""
    # Capitalise first letter of each word
    return "--" + sub.title() + "--"


# ── Entry types ───────────────────────────────────────────────────────────────

@dataclass
class ConversationEntry:
    entry_type:   str          # "speech" | "event" | "thought" | "location"
    speaker:      str          # character name or "" for events
    scene_tag:    str          # scene tag at time of entry
    location:     str          # full location string
    sub_loc:      str          # sub-location string
    text:         str          # the content
    color:        str = ""     # ANSI color for the speaker


# ── Conversation log ──────────────────────────────────────────────────────────

class ConversationLog:
    """
    Tracks all conversation entries and renders them grouped by scene.
    Hook this into SpringfieldChat by calling .record() after each response.
    """

    def __init__(self):
        self.entries: list[ConversationEntry] = []
        self._scene_view_enabled = True

    def record(self, entry_type: str, speaker: str, scene_tag: str,
               location: str, text: str, color: str = ""):
        """Add an entry to the log."""
        sub = sub_location(location)
        self.entries.append(ConversationEntry(
            entry_type=entry_type,
            speaker=speaker,
            scene_tag=scene_tag,
            location=location,
            sub_loc=sub,
            text=text,
            color=color,
        ))

    def record_event(self, description: str, scene_tag: str = "", location: str = "Springfield"):
        self.record("event", "", scene_tag, location, description)

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(self, entries: Optional[list[ConversationEntry]] = None,
               clear: bool = False) -> str:
        """
        Render conversation entries grouped by venue and sub-location.
        Returns the formatted string.
        """
        if entries is None:
            entries = self.entries

        if not entries:
            return f"{DIM}  (no conversation yet){RESET}"

        lines = []
        last_venue    = None
        last_sub      = None

        for entry in entries:
            venue = venue_name(entry.scene_tag, entry.location)

            # ── Venue header ──────────────────────────────────────────────
            if venue != last_venue:
                if lines:
                    lines.append("")   # blank line between venues
                lines.append(f"{BOLD}{WHITE}{venue}{RESET}")
                last_venue = venue
                last_sub   = None     # reset sub when venue changes

            # ── Sub-location header ───────────────────────────────────────
            if entry.sub_loc and entry.sub_loc != last_sub:
                lines.append(f"{DIM}{WHITE}{format_sub(entry.sub_loc)}{RESET}")
                last_sub = entry.sub_loc

            # ── Entry content ─────────────────────────────────────────────
            if entry.entry_type == "event":
                lines.append(f"{BOLD}{YELLOW}[SCENE] {entry.text}{RESET}")
                last_sub = None   # events reset sub-location context

            elif entry.entry_type == "action":
                lines.append(
                    f"{entry.color}{BOLD}[{entry.speaker}]{RESET}"
                    f"{ITALIC}[33m {entry.text}{RESET}"
                )

            elif entry.entry_type == "thought":
                lines.append(
                    f"{entry.color}{entry.speaker}{RESET}"
                    f"{DIM} 💭 {entry.text}{RESET}"
                )

            elif entry.entry_type == "location":
                lines.append(f"{DIM}{WHITE}  ↳ {entry.text}{RESET}")

            else:  # speech
                # Truncate very long responses for the log view
                text = entry.text.strip()
                if len(text) > 300:
                    text = text[:297] + "..."
                lines.append(
                    f"{entry.color}{entry.speaker}{RESET}: {DIM}{text}{RESET}"
                )

        return "\n".join(lines)

    def show(self, last_n: int = 0):
        """Print the conversation log. last_n=0 shows everything."""
        entries = self.entries[-last_n:] if last_n else self.entries
        print(f"\n{BOLD}{WHITE}{'═'*62}{RESET}")
        print(f"{BOLD}{WHITE}  📋  CONVERSATION LOG{RESET}")
        print(f"{BOLD}{WHITE}{'═'*62}{RESET}\n")
        print(self.render(entries))
        print(f"\n{BOLD}{WHITE}{'═'*62}{RESET}\n")

    def show_live(self, entry: ConversationEntry):
        """
        Print a single entry in scene format immediately after it's recorded.
        Called in real-time as characters speak, so the output builds up
        naturally in the scene format rather than all at once.
        """
        venue    = venue_name(entry.scene_tag, entry.location)
        sub      = format_sub(entry.sub_loc)

        # Only print venue/sub headers if they've changed since last live entry
        last = self.entries[-2] if len(self.entries) >= 2 else None
        last_venue = venue_name(last.scene_tag, last.location) if last else None
        last_sub   = format_sub(last.sub_loc) if last else None

        if venue != last_venue:
            print(f"\n{BOLD}{WHITE}{venue}{RESET}")
        if sub and sub != last_sub:
            print(f"{DIM}{WHITE}{sub}{RESET}")

        if entry.entry_type == "event":
            print(f"{BOLD}{YELLOW}[SCENE] {entry.text}{RESET}")
        elif entry.entry_type == "thought":
            print(f"{entry.color}{entry.speaker}{RESET}{DIM} 💭 {entry.text}{RESET}")
        elif entry.entry_type == "location":
            print(f"{DIM}{WHITE}  ↳ {entry.text}{RESET}")

    def clear(self):
        """Clear the conversation log."""
        self.entries.clear()
        print(f"{DIM}[Conversation log cleared]{RESET}")

    def show_scenes(self, all_chars: dict):
        """
        Show a live scene switcher — all current venues with their
        occupants listed beneath, like a TV show scene breakdown.
        """
        from character_base import get_scene

        # Group characters by venue
        venues: dict[str, list] = {}
        for key, char in all_chars.items():
            tag   = get_scene(char.location)
            vname = venue_name(tag, char.location)
            sub   = sub_location(char.location)
            venues.setdefault(vname, []).append((char, sub))

        print(f"\n{BOLD}{WHITE}{'═'*62}{RESET}")
        print(f"{BOLD}{WHITE}  🎬  SCENE SWITCHER — WHERE IS EVERYONE?{RESET}")
        print(f"{BOLD}{WHITE}{'═'*62}{RESET}")

        for vname, occupants in sorted(venues.items()):
            print(f"\n{BOLD}{WHITE}{vname}{RESET}")
            # Group by sub-location within venue
            by_sub: dict[str, list] = {}
            for char, sub in occupants:
                by_sub.setdefault(sub or "—", []).append(char)
            for sub, chars in sorted(by_sub.items()):
                if sub and sub != "—":
                    print(f"  {DIM}{WHITE}{format_sub(sub)}{RESET}")
                for char in chars:
                    print(f"    {char.color}{char.name}{RESET}")

        print(f"\n{BOLD}{WHITE}{'═'*62}{RESET}\n")