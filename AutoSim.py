"""
AutoSim.py  —  Springfield Autonomous Simulation.

Runs Springfield continuously overnight or for days/weeks with no user input.
Characters live their lives based on the real time of day and day of week.

Run in background:
  screen -S springfield python3 AutoSim.py
  tmux new -s springfield python3 AutoSim.py
  nohup python3 AutoSim.py > autosim.log 2>&1 &

Attach later:
  screen -r springfield
  tmux attach -t springfield

Stop cleanly:
  Ctrl+C  (saves state before exiting)
"""

import time
import random
import datetime
import json
import os
import sys
import signal
import traceback

# ── Springfield imports ───────────────────────────────────────────────────────
import Homer, Lisa, Bart, Marge, Maggie
import moe, nelson, BumbleBeeMan
import Lenny, Carl
import Ned, Rod, Todd
import Skinner, Willie, LunchLadyDoris
import SuperintendentChalmers, MrsKrabappel, MrLargo
import Milhouse, Ralph, Martin
import Apu, Barney, Krusty

try:
    import Comicbookguy, Montyburns, Mayorquimby
    import Patty, Selma, HansMoleman
    import SideshowBob, KentBrockman, Sanjay
except ModuleNotFoundError as e:
    print(f"[AutoSim] Optional character not found: {e} — continuing")

# New characters
try:
    import DredrickTatum, RainierWolfcastle, LindsayNaegle
    import JudgeConstableHarm, JudgeConstableSnyder
    import Jimbo, Dolph, Kearny
    import Nina, Sherri, Terri
except ModuleNotFoundError as e:
    print(f"[AutoSim] Optional character not found: {e} — continuing")

import character_base as _cb
from character_base import get_scene
from Bridge import send as bridge_send, scene_line, pause, WHITE, BOLD, DIM, RESET, YELLOW, CYAN, GREEN, RED

try:
    from SceneDirector import SceneDirector
except ImportError:
    SceneDirector = None

# ── Simulation settings ───────────────────────────────────────────────────────
try:
    import settings as _cfg
    MODEL = _cfg.MODEL
    SIMULATION_INTENSITY = getattr(_cfg, 'SIMULATION_INTENSITY', "medium")
except ImportError:
    MODEL = "llama3.2:latest"
    SIMULATION_INTENSITY = "medium"

# How many real seconds between simulation ticks
# 300 = 5 minutes between events (good for overnight)
# 60  = 1 minute (more active, heavier on RAM)
TICK_SECONDS = 300

# How many simulation minutes pass per real tick
# 30 = each tick advances sim time by 30 minutes
SIM_MINUTES_PER_TICK = 30

# Log file for the overnight run
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autosim.log")

# State persistence — so you can restart and pick up roughly where you left off
STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autosim_state.json")

# ── All characters ────────────────────────────────────────────────────────────
ALL_CHARS = {}
for mod, key in [
    (Homer, "homer"), (Lisa, "lisa"), (Bart, "bart"),
    (Marge, "marge"), (Maggie, "maggie"),
    (moe, "moe"), (nelson, "nelson"), (BumbleBeeMan, "bumblebeeman"),
    (Lenny, "lenny"), (Carl, "carl"),
    (Ned, "ned"), (Rod, "rod"), (Todd, "todd"),
    (Skinner, "skinner"), (Willie, "willie"),
    (LunchLadyDoris, "lunchladydoris"),
    (SuperintendentChalmers, "superintendentchalmers"),
    (MrsKrabappel, "mrskrabappel"), (MrLargo, "mrlargo"),
    (Milhouse, "milhouse"), (Ralph, "ralph"), (Martin, "martin"),
    (Apu, "apu"), (Barney, "barney"), (Krusty, "krusty"),
    # New characters
    (DredrickTatum, "dredricktatum"), (RainierWolfcastle, "rainierwolfcastle"),
    (LindsayNaegle, "lindsaynaegle"),
    (JudgeConstableHarm, "judgeconstableharm"), (JudgeConstableSnyder, "judgeconstablesnyder"),
    (Jimbo, "jimbo"), (Dolph, "dolph"), (Kearny, "kearny"),
    (Nina, "nina"), (Sherri, "sherri"), (Terri, "terri"),
]:
    try:
        ALL_CHARS[key] = mod.character
    except AttributeError:
        pass

# Optional characters - check if module exists before adding
optional_modules = [
    ("Comicbookguy", "comicbookguy"), ("Montyburns", "montyburns"), ("Mayorquimby", "mayorquimby"),
    ("Patty", "patty"), ("Selma", "selma"), ("HansMoleman", "hansmoleman"),
    ("SideshowBob", "sideshowbob"), ("KentBrockman", "kentbrockman"), ("Sanjay", "sanjay"),
]
for mod_name, key in optional_modules:
    try:
        mod = globals().get(mod_name)
        if mod:
            ALL_CHARS[key] = mod.character
    except (AttributeError, NameError):
        pass

_cb.ALL_CHARS_REF.update(ALL_CHARS)


# ── Schedule ──────────────────────────────────────────────────────────────────
# Each entry: (hour_start, hour_end, weekdays, description, event_fn)
# weekdays: set of 0-6 (0=Mon) or None for any day

def is_weekday(dt): return dt.weekday() < 5
def is_weekend(dt): return dt.weekday() >= 5


# ── Daily schedule blocks ─────────────────────────────────────────────────────
class TimeBlock:
    def __init__(self, h_start, h_end, label, chars, prompt,
                 weekend_only=False, weekday_only=False):
        self.h_start      = h_start
        self.h_end        = h_end
        self.label        = label
        self.chars        = chars   # list of character keys
        self.prompt       = prompt
        self.weekend_only = weekend_only
        self.weekday_only = weekday_only

    def active(self, dt):
        if self.weekday_only and not is_weekday(dt):
            return False
        if self.weekend_only and not is_weekend(dt):
            return False
        return self.h_start <= dt.hour < self.h_end


SCHEDULE = [
    TimeBlock(6, 8, "Morning routine",
              ["marge", "homer", "bart", "lisa", "maggie"],
              "It's early morning at 742 Evergreen Terrace. The family is waking up. "
              "React to the morning — getting up, getting ready, the usual chaos."),

    TimeBlock(7, 8, "School morning rush",
              ["bart", "lisa", "milhouse", "martin", "ralph"],
              "It's a school morning. You need to get to Springfield Elementary. "
              "React — are you running late? Did you do your homework?",
              weekday_only=True),

    TimeBlock(8, 15, "School day",
              ["bart", "lisa", "skinner", "mrskrabappel", "mrlargo",
               "willie", "milhouse", "ralph", "martin", "nelson"],
              "It's a school day at Springfield Elementary. React to whatever is "
              "happening right now in your role at the school.",
              weekday_only=True),

    TimeBlock(8, 17, "Work day — plant",
              ["homer", "lenny", "carl"],
              "It's a work day at the Springfield Nuclear Power Plant. React to "
              "the day — the work, the boredom, the danger of Homer being here.",
              weekday_only=True),

    TimeBlock(9, 22, "Kwik-E-Mart open",
              ["apu"],
              "The Kwik-E-Mart is open. React to the customers, the day, "
              "the state of the store."),

    TimeBlock(9, 20, "Moe's opens",
              ["moe", "barney"],
              "Moe's Tavern is open for business. React to the day at the bar. "
              "Who's come in? What's Barney doing?"),

    TimeBlock(10, 18, "Weekend freedom",
              ["bart", "lisa", "milhouse", "nelson", "ralph"],
              "It's the weekend! No school. React to what you're doing with your "
              "free time in Springfield.",
              weekend_only=True),

    TimeBlock(15, 17, "After school",
              ["bart", "lisa", "milhouse", "martin"],
              "School's out. React to being free — heading home, hanging out, "
              "causing trouble.",
              weekday_only=True),

    TimeBlock(17, 19, "Dinner time",
              ["marge", "homer", "bart", "lisa", "maggie"],
              "It's dinner time at 742 Evergreen Terrace. The family is gathering "
              "for dinner. React to the meal, the family, the day you've had."),

    TimeBlock(19, 22, "Evening — Homer at Moe's",
              ["homer", "moe", "lenny", "carl", "barney"],
              "Homer has come to Moe's for his evening beer. React to the evening "
              "at the tavern."),

    TimeBlock(19, 21, "Kids' evening",
              ["bart", "lisa", "maggie"],
              "It's evening at home. React to what you're doing — TV, homework, "
              "getting ready for bed."),

    TimeBlock(20, 22, "Ned's evening",
              ["ned", "rod", "todd"],
              "It's evening at 744 Evergreen Terrace. The Flanders family is "
              "having their evening. React — prayer, reading, family time."),

    TimeBlock(21, 23, "Bedtime",
              ["bart", "lisa", "maggie", "rod", "todd", "milhouse", "ralph"],
              "It's bedtime. React to being sent to bed — or trying to stay up."),

    TimeBlock(22, 24, "Late night Moe's",
              ["homer", "moe", "barney", "lenny"],
              "It's late night at Moe's. The serious drinkers remain. "
              "React to the late hour and whatever state you're all in."),

    TimeBlock(0, 6, "Night / sleeping",
              ["homer", "marge", "bart", "lisa", "ned"],
              "Everyone is asleep. React to the quiet of Springfield at night. "
              "Are you sleeping soundly? Having a dream? Raiding the fridge?"),
]

# ── Spontaneous events (fire randomly) ───────────────────────────────────────
RANDOM_EVENTS = [
    ("A squirrel gets into the house", ["homer", "marge", "bart"],        0.08),
    ("Homer sits on the TV remote and changes to a boring channel",
     ["homer", "bart"],                                                    0.10),
    ("Bart's skateboard rolls into the kitchen",
     ["marge", "bart"],                                                    0.08),
    ("Ned waves enthusiastically from over the fence",
     ["homer", "ned"],                                                     0.12),
    ("Maggie escapes from the living room",
     ["marge", "maggie"],                                                  0.06),
    ("The phone rings at Moe's Tavern",
     ["moe"],                                                              0.15),
    ("Barney lets out an enormous belch",
     ["moe", "barney", "homer", "lenny"],                                  0.20),
    ("Someone tips over a Duff Beer",
     ["homer", "lenny", "barney"],                                         0.10),
    ("Principal Skinner spots Bart doing something suspicious",
     ["skinner", "bart"],                                                  0.12),
    ("Willie starts shouting about Scotland for no clear reason",
     ["willie", "skinner"],                                                0.10),
    ("Lisa plays a particularly mournful saxophone solo",
     ["lisa", "homer", "marge"],                                           0.08),
    ("Homer says D'oh and nobody knows why",
     ["homer"],                                                            0.20),
    ("Ralph says something completely baffling",
     ["ralph", "bart", "lisa"],                                            0.10),
    ("Nelson laughs at something in the distance",
     ["nelson", "bart", "milhouse"],                                       0.12),
    ("Milhouse says everything is coming up Milhouse",
     ["milhouse", "bart"],                                                 0.08),
    ("MontyBurns stares at a photograph of Smithers with confusion",
     ["montyburns"],                                                       0.06),
]

# ── Dramatic events (only enabled at high intensity) ────────────────────────────
DRAMATIC_EVENTS = [
    ("ALERT: Meltdown at the Springfield Nuclear Power Plant! Sirens blare as smoke rises from the cooling towers.",
     ["homer", "marge", "bart", "lisa", "montyburns", "lenny", "carl", "smithers"],  0.05),
    ("BREAKING: Mayor Quimby announces an emergency election after a scandal rocks City Hall!",
     ["mayorquimby", "homer", "marge", "lisa", "bart", "ned", "kentbrockman"],      0.04),
    ("DISASTER: A Duff Beer truck has overturned on Main Street, sending kegs rolling everywhere!",
     ["homer", "barney", "moe", "lenny", "carl", "wiggum", "eddie"],                 0.06),
    ("CHAOS: A prison break at Springfield Penitentiary! Sideshow Bob is on the loose!",
     ["sideshowbob", "wiggum", "eddie", "lou", "homer", "bart", "krusty"],          0.03),
    ("CRISIS: Springfield Elementary is on lockdown after a mysterious substance is found in the cafeteria!",
     ["skinner", "krabappel", "willie", "lunchladydoris", "bart", "lisa", "milhouse"], 0.05),
    ("URGENT: A tornado warning has been issued for Springfield! Everyone seeks shelter!",
     ["homer", "marge", "bart", "lisa", "maggie", "ned", "rod", "todd", "moe"],      0.04),
    ("SHOCKING: Krusty the Clown announces his retirement from show business!",
     ["krusty", "homer", "bart", "lisa", "sideshowmel", "sideshowbob"],              0.05),
    ("TURMOIL: The Kwik-E-Mart is robbed at gunpoint! Apu fights back with surprising bravery.",
     ["apu", "homer", "barney", "snake", "wiggum", "sanjay"],                         0.04),
    ("SCANDAL: Mr. Burns cuts health benefits for all plant employees, sparking a protest!",
     ["montyburns", "smithers", "homer", "lenny", "carl", "marge", "lintony"],       0.05),
    ("TRAGEDY: A fire breaks out at Moe's Tavern after Homer's cigar mishap!",
     ["moe", "homer", "barney", "lenny", "carl", "wiggum"],                           0.04),
]


# ═══════════════════════════════════════════════════════════════════════════════
#  SIMULATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class AutoSim:

    def __init__(self):
        self.running      = True
        self.tick_count   = 0
        self.start_time   = datetime.datetime.now()
        self.director     = SceneDirector(ALL_CHARS) if SceneDirector else None
        self._setup_signal()

    def _setup_signal(self):
        """Catch Ctrl+C and SIGTERM for clean shutdown."""
        signal.signal(signal.SIGINT,  self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, *_):
        self.running = False
        print(f"\n{BOLD}{WHITE}[AutoSim] Shutting down gracefully...{RESET}")
        self._save_state()
        sys.exit(0)

    # ── Logging ───────────────────────────────────────────────────────────────

    def log(self, msg: str):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(f"{DIM}{line}{RESET}")
        bridge_send(f"AUTOSIM  {msg}")
        try:
            with open(LOG_PATH, "a") as f:
                f.write(line + "\n")
        except Exception:
            pass

    # ── State persistence ─────────────────────────────────────────────────────

    def _save_state(self):
        state = {
            "tick_count": self.tick_count,
            "saved_at":   datetime.datetime.now().isoformat(),
            "locations":  {k: c.location for k, c in ALL_CHARS.items()},
        }
        try:
            with open(STATE_PATH, "w") as f:
                json.dump(state, f, indent=2)
            self.log(f"State saved ({self.tick_count} ticks)")
        except Exception as e:
            self.log(f"Could not save state: {e}")

    def _load_state(self):
        if not os.path.exists(STATE_PATH):
            return
        try:
            with open(STATE_PATH) as f:
                state = json.load(f)
            for key, loc in state.get("locations", {}).items():
                char = ALL_CHARS.get(key)
                if char:
                    char.set_location(loc)
            self.tick_count = state.get("tick_count", 0)
            self.log(f"State restored from {state.get('saved_at', 'unknown')}")
        except Exception as e:
            self.log(f"Could not load state: {e}")

    # ── Simulation time ───────────────────────────────────────────────────────

    def sim_time(self) -> datetime.datetime:
        """Return the current real time (simulation runs in real-time)."""
        return datetime.datetime.now()

    # ── Fire a character response ─────────────────────────────────────────────

    def fire(self, char_key: str, prompt: str, label: str = ""):
        char = ALL_CHARS.get(char_key)
        if not char:
            return
        try:
            if label:
                print(f"\n{YELLOW}[{label}]{RESET}")
            print(f"\n{char.color}[{char.name.upper()}]:{RESET} ", end="")
            response = char.get_response(prompt, sender="[AutoSim]",
                                         ignore_location=True)
            if self.director and response:
                self.director.analyse(char_key, char.name, response)
            return response
        except Exception as e:
            self.log(f"Error firing {char_key}: {e}")
            return ""

    # ── Schedule block ────────────────────────────────────────────────────────

    def run_schedule_block(self, block: TimeBlock, dt: datetime.datetime):
        """Pick one character from the block and have them react."""
        chars = [k for k in block.chars if k in ALL_CHARS]
        if not chars:
            return
        char_key = random.choice(chars)
        self.log(f"Schedule: {block.label} — {char_key}")
        scene_line(f"{block.label}")
        self.fire(char_key, block.prompt, label=block.label)

    # ── Random event ──────────────────────────────────────────────────────────

    def maybe_random_event(self):
        """Roll the dice on each random event."""
        # Build the pool of events based on simulation intensity
        event_pools = []
        if SIMULATION_INTENSITY == "high":
            event_pools = [RANDOM_EVENTS, DRAMATIC_EVENTS]
        elif SIMULATION_INTENSITY == "medium":
            event_pools = [RANDOM_EVENTS]
        elif SIMULATION_INTENSITY == "low":
            # Only low-impact events for low intensity
            event_pools = [[e for e in RANDOM_EVENTS if e[2] < 0.15]]
        
        for pool in event_pools:
            for desc, chars, prob in pool:
                if random.random() < prob:
                    valid = [k for k in chars if k in ALL_CHARS]
                    if not valid:
                        continue
                    char_key = random.choice(valid)
                    event_type = "Dramatic Event" if pool is DRAMATIC_EVENTS else "Random Event"
                    self.log(f"{event_type}: {desc} → {char_key}")
                    scene_line(desc)
                    self.fire(char_key,
                              f"The following just happened: {desc}. "
                              f"React naturally as your character.",
                              label=event_type)
                    return  # only one event per tick

    # ── Spontaneous character interaction ─────────────────────────────────────

    def maybe_interaction(self, dt: datetime.datetime):
        """Occasionally have two characters in the same scene talk to each other."""
        if random.random() > 0.3:
            return

        from character_base import get_scene
        scenes: dict[str, list] = {}
        for key, char in ALL_CHARS.items():
            scenes.setdefault(get_scene(char.location), []).append(key)

        # Pick a scene with at least 2 characters
        populated = [(tag, keys) for tag, keys in scenes.items() if len(keys) >= 2]
        if not populated:
            return

        _, keys = random.choice(populated)
        a_key, b_key = random.sample(keys, 2)
        a, b = ALL_CHARS[a_key], ALL_CHARS[b_key]

        topics = [
            "something that happened today",
            "what you're doing right now",
            "an opinion about Springfield",
            "something that's been on your mind",
            "a complaint or observation",
            "something funny you saw",
        ]
        topic = random.choice(topics)

        self.log(f"Interaction: {a.name} → {b.name} about {topic}")
        print(f"\n{a.color}[{a.name.upper()} → {b.name}]:{RESET} ", end="")
        response = a.get_response(
            f"Start a natural conversation with {b.name} about {topic}. "
            f"Speak directly to them in your own voice.",
            sender="[AutoSim]", ignore_location=True
        )
        if response:
            print(f"\n{b.color}[{b.name.upper()} replies]:{RESET} ", end="")
            b.get_response(response, sender=a.name, ignore_location=True)

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        print(f"\n{BOLD}{WHITE}{'═'*62}{RESET}")
        print(f"{BOLD}{WHITE}  🏙️  SPRINGFIELD AUTOSIM — RUNNING{RESET}")
        print(f"{BOLD}{WHITE}  Tick interval: {TICK_SECONDS}s  "
              f"({TICK_SECONDS//60}m real time){RESET}")
        print(f"{BOLD}{WHITE}  Characters loaded: {len(ALL_CHARS)}{RESET}")
        print(f"{BOLD}{WHITE}  Simulation intensity: {SIMULATION_INTENSITY}{RESET}")
        print(f"{BOLD}{WHITE}  Log: {LOG_PATH}{RESET}")
        print(f"{BOLD}{WHITE}  Ctrl+C to stop cleanly{RESET}")
        print(f"{BOLD}{WHITE}{'═'*62}{RESET}\n")

        self._load_state()
        self.log(f"AutoSim started — {len(ALL_CHARS)} characters")

        while self.running:
            try:
                self.tick_count += 1
                dt = self.sim_time()
                self.log(f"Tick {self.tick_count} — "
                         f"{dt.strftime('%A %H:%M')} "
                         f"({'weekday' if is_weekday(dt) else 'weekend'})")

                print(f"\n{BOLD}{CYAN}{'─'*62}{RESET}")
                print(f"{BOLD}{CYAN}  🕐 {dt.strftime('%A %H:%M')}  "
                      f"Tick {self.tick_count}{RESET}")
                print(f"{BOLD}{CYAN}{'─'*62}{RESET}")

                # ── Run matching schedule blocks (pick one) ────────────────
                active_blocks = [b for b in SCHEDULE if b.active(dt)]
                if active_blocks:
                    block = random.choice(active_blocks)
                    self.run_schedule_block(block, dt)

                # ── Maybe fire a random event ──────────────────────────────
                self.maybe_random_event()

                # ── Maybe fire a spontaneous interaction ───────────────────
                self.maybe_interaction(dt)

                # ── Save state every 12 ticks (1 hour at 5min ticks) ──────
                if self.tick_count % 12 == 0:
                    self._save_state()

                # ── Sleep until next tick ──────────────────────────────────
                self.log(f"Sleeping {TICK_SECONDS}s until next tick...")
                time.sleep(TICK_SECONDS)

            except KeyboardInterrupt:
                self._shutdown()
            except Exception as e:
                self.log(f"Tick error: {e}")
                traceback.print_exc()
                self.log("Continuing after error...")
                time.sleep(30)   # brief pause after error before retrying


if __name__ == "__main__":
    sim = AutoSim()
    sim.run()