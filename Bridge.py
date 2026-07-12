"""
bridge.py  —  Springfield fileless inter-process bridge.

Uses an abstract Unix domain socket (\0springfield) — kernel memory only,
no files, no /tmp, nothing on disk.

  Terminal 1:  python3 SpringfieldChat.py
  Terminal 2:  python3 bridge.py

Bridge.py listens as a server. SceneDirector connects as a client and
streams output — including live AI tokens — directly to the monitor.
If Bridge.py is not running, SceneDirector skips silently.
"""

import os
import sys
import socket
import threading
import datetime

# ── Abstract socket address ───────────────────────────────────────────────────
# \0 prefix = abstract namespace = kernel only, no filesystem entry
SOCKET_ADDR = "\0springfield"

# ═══════════════════════════════════════════════════════════════
#  ANSI COLOURS  (single definition, import from here)
# ═══════════════════════════════════════════════════════════════

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
ITALIC  = "\033[3m"
WHITE   = "\033[97m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
GREEN   = "\033[92m"
CYAN    = "\033[96m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
GOLD    = "\033[33m"
GREY    = "\033[90m"


# ═══════════════════════════════════════════════════════════════
#  CLIENT — used by SceneDirector (imported into SceneDirector.py)
# ═══════════════════════════════════════════════════════════════

def send(msg: str):
    """
    Send a single timestamped line to the bridge monitor.
    Non-blocking — if Bridge.py isn't running, silently skips.
    """
    try:
        ts   = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(0.05)
            s.connect(SOCKET_ADDR)
            s.sendall(line.encode("utf-8"))
    except (ConnectionRefusedError, OSError, TimeoutError):
        pass


def send_raw(data: str):
    """
    Send raw data (no timestamp) — for streaming AI tokens character by character.
    Non-blocking — silently skips if no monitor connected.
    """
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(0.05)
            s.connect(SOCKET_ADDR)
            s.sendall(data.encode("utf-8"))
    except (ConnectionRefusedError, OSError, TimeoutError):
        pass


class Stream:
    """
    Context manager for streaming AI tokens to the bridge.
    Opens one socket connection and keeps it open for the duration —
    much more efficient than reconnecting per token.

    Usage:
        with Stream() as st:
            for chunk in ollama_stream:
                st.write(chunk)
    """
    def __init__(self):
        self._sock = None

    def __enter__(self):
        try:
            self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._sock.settimeout(0.05)
            self._sock.connect(SOCKET_ADDR)
        except (ConnectionRefusedError, OSError):
            self._sock = None
        return self

    def write(self, data: str):
        if self._sock:
            try:
                self._sock.sendall(data.encode("utf-8"))
            except OSError:
                self._sock = None

    def writeline(self, msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.write(f"[{ts}] {msg}\n")

    def __exit__(self, *_):
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None


# ═══════════════════════════════════════════════════════════════
#  SHARED SCENE UTILITIES
# ═══════════════════════════════════════════════════════════════

import time

def scene_line(text: str):
    """Print a [SCENE] line and send to bridge."""
    print(f"\n{BOLD}{WHITE}[SCENE] {text}{RESET}")
    send(f"SCENE  {text}")


def action_line(char_name: str, char_color: str, text: str):
    """Print a character action in gold italic and send to bridge."""
    print(f"\n{char_color}{BOLD}[{char_name}]{RESET} {ITALIC}{GOLD}{text}{RESET}")
    send(f"ACTION  {char_name}: {text}")


def narrator_line(text: str):
    """Print a narrator line and send to bridge."""
    print(f"\n{ITALIC}{WHITE}  📺 {text}{RESET}")
    send(f"NARRATOR  {text}")


def event_banner(description: str, label: str = ""):
    """Print a white event banner and send to bridge."""
    print(f"\n{BOLD}{WHITE}{'─'*60}{RESET}")
    print(f"{BOLD}{WHITE}  [Event] {description}{RESET}")
    if label:
        print(f"{BOLD}{WHITE}  {label}{RESET}")
    print(f"{BOLD}{WHITE}{'─'*60}{RESET}")
    send(f"EVENT  {description}")


def location_update(char_name: str, new_location: str):
    """Print and send a dim location update."""
    msg = f"↳ {char_name} → {new_location}"
    print(f"{DIM}{WHITE}  {msg}{RESET}")
    send(f"MOVE  {msg}")


def pause(secs: float = 0.6):
    time.sleep(secs)


# ═══════════════════════════════════════════════════════════════
#  SHARED CONSTANTS
# ═══════════════════════════════════════════════════════════════

CHILD_KEYS     = {"bart", "lisa", "maggie", "milhouse", "ralph",
                  "martin", "rod", "todd", "nelson"}
AUTHORITY_KEYS = {"marge", "homer", "ned", "skinner", "mrskrabappel",
                  "mrlargo", "superintendentchalmers", "willie"}


# ═══════════════════════════════════════════════════════════════
#  SERVER / MONITOR — python3 bridge.py
# ═══════════════════════════════════════════════════════════════

def _colour_line(line: str) -> str:
    """Colour-code a received line by its type prefix."""
    if line.startswith("━━━"):
        return f"\n{BOLD}{CYAN}{line}{RESET}"
    elif "AI >>>" in line:
        return f"{DIM}{CYAN}{line}{RESET}"
    elif line.startswith("── LOCATIONS") or line.startswith("── LOC"):
        return f"\n{BOLD}{GREEN}{line}{RESET}"
    elif "→" in line and line.strip().startswith("   "):
        k, _, v = line.strip().partition("→")
        return f"   {YELLOW}{k.strip()}{RESET} → {GREEN}{v.strip()}{RESET}"
    elif "NARRATOR" in line:
        return f"{CYAN}{line}{RESET}"
    elif "EVENT" in line:
        return f"{MAGENTA}{line}{RESET}"
    elif "SCENE" in line:
        return f"{BOLD}{WHITE}{line}{RESET}"
    elif "ACTION" in line:
        return f"{GOLD}{line}{RESET}"
    elif "ERROR" in line:
        return f"{RED}{line}{RESET}"
    elif any(w in line for w in ("MOVE", "CALL", "GROUP")):
        return f"{YELLOW}{line}{RESET}"
    elif "APPLY" in line:
        return f"{GREEN}{line}{RESET}"
    elif "MANUAL" in line:
        return f"{WHITE}{line}{RESET}"
    elif "INIT" in line:
        return f"{DIM}{GREEN}{line}{RESET}"
    elif "MOOD" in line:
        return f"{DIM}{line}{RESET}"
    # Raw AI tokens (no prefix) — streamed mid-analysis
    return f"{DIM}{CYAN}{line}{RESET}"


def _handle_client(conn: socket.socket):
    """Receive data from one client connection and print it."""
    buf = ""
    try:
        with conn:
            conn.settimeout(2.0)
            while True:
                try:
                    data = conn.recv(4096)
                except socket.timeout:
                    break
                if not data:
                    break
                buf += data.decode("utf-8", errors="replace")
                # Print complete lines immediately; buffer the rest
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if line.strip():
                        print(_colour_line(line), flush=True)
        # Print anything remaining without a newline (streaming tokens)
        if buf.strip():
            print(_colour_line(buf), flush=True)
    except OSError:
        pass


def run_monitor():
    """Start the bridge server and display incoming director output."""
    print(f"{BOLD}{WHITE}╔══════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{WHITE}║   🎬  SPRINGFIELD — SCENE DIRECTOR BRIDGE            ║{RESET}")
    print(f"{BOLD}{WHITE}║   Socket: abstract://springfield  (kernel only)      ║{RESET}")
    print(f"{BOLD}{WHITE}║   No files. No /tmp. Pure memory.                    ║{RESET}")
    print(f"{BOLD}{WHITE}║   Ctrl+C to exit                                     ║{RESET}")
    print(f"{BOLD}{WHITE}╚══════════════════════════════════════════════════════╝{RESET}")
    print()
    print(f"  {BOLD}Colour key:{RESET}")
    print(f"  {CYAN}■{RESET} AI stream / analysis     "
          f"{YELLOW}■{RESET} location moves")
    print(f"  {GREEN}■{RESET} applied updates           "
          f"{MAGENTA}■{RESET} events")
    print(f"  {WHITE}■{RESET} scene lines               "
          f"{GOLD}■{RESET} character actions")
    print(f"  {RED}■{RESET} errors\n")

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind(SOCKET_ADDR)
    except OSError as e:
        print(f"{RED}Could not bind socket: {e}{RESET}")
        print(f"{DIM}Is another Bridge.py already running?{RESET}")
        sys.exit(1)

    server.listen(5)
    print(f"{GREEN}✓ Listening. Start SpringfieldChat.py in the other terminal.{RESET}\n")

    try:
        while True:
            conn, _ = server.accept()
            # Each connection handled in its own thread so tokens stream smoothly
            t = threading.Thread(target=_handle_client, args=(conn,), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print(f"\n{DIM}Bridge closed.{RESET}")
    finally:
        server.close()


if __name__ == "__main__":
    run_monitor()