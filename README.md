# 
# Simpsons AI - Springfield Town Chat

<div align="center">

**🎭 Welcome to Springfield!**

*Every Simpsons character in one chaotic conversation.*

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Ollama Required](https://img.shields.io/badge/ollama-required-orange.svg)](https://ollama.ai)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

</div>

---
## **⚠️ Warning**
HIGHLY NOT RECOMMENDED TO PULL OR USE BECAUSE OF COPYRIGHT
EXPERIMENTAL PURPOSES ONLY
## 📋 Overview

**Simpsons AI** is an interactive chat application that brings the entire town of Springfield to life using AI-powered characters. Each character has their own unique personality, voice, and behavior patterns based on their portrayal in *The Simpsons* TV show.

With **50+ characters** from the Simpson family, Springfield Elementary, Moe's Tavern, the Nuclear Power Plant, and beyond, you can:

- 💬 Chat with individual characters like Homer, Bart, Lisa, Marge, and Maggie
- 🎭 Host group conversations with multiple characters at once
- 📍 Move characters between locations (742 Evergreen Terrace, Moe's Tavern, Power Plant, etc.)
- 🎬 Create and run custom scene scripts
- 🎯 Trigger special interactions (like Homer strangling Bart or Nelson's HA-HA)
- 🎨 Enjoy color-coded character dialogue

---

## ⚡ Quick Start

### Prerequisites

1. **Python 3.10 or higher**
2. **Ollama** installed and running locally
   - Download: [https://ollama.ai](https://ollama.ai)
   - Install: Follow platform-specific instructions
   - Start: `ollama serve`
3. **Pull a model** (default is `llama3.2:latest`):
   ```bash
   ollama pull llama3.2:latest
   ```

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/johnny-pilotgenerativeai/Simpsons-Ai.git
   cd Simpsons-Ai
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start chatting:
   ```bash
   python SpringfieldChat.py
   ```

---

## 🎯 Usage

### Basic Commands

| Command | Description |
|---------|-------------|
| `@homer Hello!` | Talk to Homer directly |
| `@all What's up?` | Address all characters at once |
| `@family Dinner time!` | Talk to the Simpson family |
| `@school Class dismissed!` | Address Springfield Elementary |
| `@plant Safety first!` | Talk to power plant workers |
| `exit` | Leave Springfield |

### Group Commands

You can address predefined groups:

- `@all` - Everyone in Springfield
- `@family` - Homer, Marge, Bart, Lisa, Maggie
- `@locals` - Moe, Nelson, BumbleBeeMan
- `@plant` - Lenny, Carl, Monty Burns
- `@notables` - Comic Book Guy, Mayor Quimby
- `@flanders` - Ned, Rod, Todd
- `@school` - Skinner, Willie, Lunch Lady Doris, Chalmers, Mrs. Krabappel, Mr. Largo
- `@kids` - Milhouse, Ralph, Martin
- `@kwikmart` - Apu, Sanjay
- `@adults` - Barney, Patty, Selma, Hans Moleman
- `@media` - Krusty, Sideshow Bob, Kent Brockman
- `@recurring` - Squeaky Voiced Teen, Yes Guy, Smithers, Sideshow Mel, Gil
- `@medical` - Dr. Nick, Dr. Hibbert
- `@police` - Chief Wiggum, Eddie, Lou

### Character-to-Character Communication

```
/speaker:target message
```

Examples:
- `/bart:moe Can I have a Duff?` - Bart talks to Moe
- `/homer:marge I'm hungry` - Homer talks to Marge
- `/marge:bart@lisa Clean your rooms!` - Marge talks to both Bart and Lisa

### Location Management

Set character locations:
```
[Location: char1@char2: description]
```
or
```
/locate char1@char2: description
```

Examples:
- `[Location: homer@marge: Kitchen at 742 Evergreen Terrace]`
- `/locate bart@milhouse: Treehouse in the backyard`
- `[Location: homer@barney: Moe's Tavern at the bar]`

### Scene Scripts

Create multi-line scripts with `/scene`:

```
/scene
[Location: homer@marge: Kitchen]
Marge: Dinner is ready!
Homer: Mmm... dinner...
[Event] The smell of food fills the air
/endscene
```

### Events

Trigger events that characters react to:

```
/event The power plant explodes!
```

Or target specific groups:
```
/event:family The power plant explodes!
```

### Private Thoughts

Make a character think privately (not spoken aloud):
```
/thoughts:homer Should I eat another donut?
```

### Other Commands

| Command | Description |
|---------|-------------|
| `/log` | Show conversation log |
| `/log 20` | Show last 20 entries |
| `/scenes` | Show all venues and occupants |
| `/clearlog` | Clear conversation log |
| `/locations` | Show where everyone is |
| `/director on` | Enable AI scene director |
| `/director off` | Disable AI scene director |

---

## 🎭 Character List

### The Simpson Family
- **Homer** - The lovable, beer-drinking, donut-obsessed patriarch
- **Marge** - The patient, blue-haired mother
- **Bart** - The mischievous 10-year-old troublemaker
- **Lisa** - The intelligent, saxophone-playing daughter
- **Maggie** - The silent baby with a pacifier

### Springfield Locals
- **Moe** - The grumpy tavern owner
- **Nelson** - The bully who loves to say "HA-HA!"
- **Bumblebee Man** - The Spanish-speaking superhero

### Nuclear Power Plant
- **Lenny** - Homer's coworker and friend
- **Carl** - Another coworker, often paired with Lenny
- **Monty Burns** - The evil, wealthy plant owner
- **Smithers** - Mr. Burns' loyal assistant
- **Waylon Smithers** - Alternative name for Smithers

### Springfield Elementary
- **Principal Skinner** - The nervous, rule-obsessed principal
- **Groundskeeper Willie** - The Scottish janitor
- **Lunch Lady Doris** - The lunch server
- **Superintendent Chalmers** - Skinner's boss
- **Mrs. Krabappel** - Bart's former teacher
- **Mr. Largo** - The music teacher

### Students
- **Milhouse** - Bart's best friend
- **Ralph** - The dim-witted student
- **Martin** - The intelligent, rule-following student

### Kwik-E-Mart
- **Apu** - The convenience store owner
- **Sanjay** - Apu's brother

### Springfield Adults
- **Barney** - Homer's drunk friend
- **Patty** - Marge's sister
- **Selma** - Marge's other sister
- **Hans Moleman** - The unlucky, visually impaired man

### Media & Entertainment
- **Krusty the Clown** - The washed-up TV clown
- **Sideshow Bob** - Krusty's former sidekick turned criminal
- **Kent Brockman** - The news anchor
- **Sideshow Mel** - Krusty's current sidekick
- **Comic Book Guy** - The nerdy comic shop owner

### Retirement Castle
- **Grampa Simpson** - Homer's father
- **Jasper** - Grampa's friend
- **Old Jewish Man** - Another retirement home resident

### Recurring Characters
- **Squeaky Voiced Teen** - The teenager with a squeaky voice
- **Yes Guy** - The guy who always says "Yes!"
- **Gil** - The salesman

### Medical
- **Dr. Nick** - The incompetent doctor
- **Dr. Hibbert** - The competent, laughing doctor

### Police
- **Chief Wiggum** - The bumbling police chief
- **Eddie** - Wiggum's partner
- **Lou** - Another police officer

### Services
- **Sea Captain** - The seafood restaurant owner
- **Mayor Quimby** - The corrupt mayor

---

## ⚙️ Configuration

Edit `Settings.py` to customize your experience:

### Change the AI Model

```python
MODEL = "llama3.2:latest"  # Change to any model you have pulled
```

Supported models (must be pulled first with `ollama pull`):
- `llama3.2:latest` (default)
- `llama3.1:latest`
- `mistral:latest`
- `gemma2:latest`
- `phi3:latest`
- `deepseek-r1:8b`

### Enable/Disable Characters

```python
CHARACTERS = {
    "Homer": True,
    "Bart": True,
    "Lisa": True,
    # ... set any character to False to disable them
}
```

### Nelson HA-HA Sensitivity

```python
NELSON_SENSITIVITY = "medium"  # Options: "high", "medium", "low", "off"
```

- **high**: Nelson reacts to almost anything bad
- **medium**: Nelson reacts to clear misfortunes (default)
- **low**: Only obvious disasters trigger him
- **off**: Nelson never auto-interjects

### Chain Reaction Depth

```python
TRIGGER_DEPTH = 2  # How many levels of name-mention reactions
```

Higher values allow more chain reactions but can get noisy with many characters.

---

## 🎬 Special Features

### Nelson's HA-HA

Nelson automatically detects misfortune and interjects with his signature "HA-HA!" when:
- Someone says "D'oh!"
- Someone gets hurt or embarrassed
- Something goes wrong
- Any misfortune occurs

The sensitivity can be adjusted in `Settings.py`.

### Homer Strangling Bart

When Homer says "Why you little—!" or similar phrases, the classic strangling sequence is triggered automatically if both characters are in the same location.

### Scene Director

The AI Scene Director automatically:
- Tracks character locations
- Updates locations based on context
- Triggers appropriate reactions
- Manages scene transitions

Toggle with `/director on` or `/director off`.

### Location Awareness

Characters only react to each other when they're in the same location. Use `/locate` or `[Location:]` commands to move characters around Springfield.

Recognized locations include:
- 742 Evergreen Terrace (Simpson house)
- 744 Evergreen Terrace (Flanders house)
- Moe's Tavern
- Nuclear Power Plant / Sector 7-G
- Springfield Elementary
- Kwik-E-Mart
- Android's Dungeon (comic book store)
- Town Hall
- Church
- Hospital
- Krusty Burger
- Lard Lad Donuts
- Springfield Park
- Springfield Mall
- Channel Ocho Studio
- And many more!

---

## 📦 Requirements

Create a `requirements.txt` file with:

```
ollama>=0.1.0
```

Install with:
```bash
pip install -r requirements.txt
```

---

## 🐛 Troubleshooting

### Ollama Connection Issues

If you see connection errors:

1. Make sure Ollama is running:
   ```bash
   ollama serve
   ```

2. Check if the model is pulled:
   ```bash
   ollama list
   ```

3. If not, pull the model:
   ```bash
   ollama pull llama3.2:latest
   ```

4. Restart Ollama:
   ```bash
   systemctl restart ollama  # Linux
   # or restart the service on your platform
   ```

### Character Not Found

Make sure:
- The character file exists (e.g., `Homer.py`)
- The filename matches exactly (Linux is case-sensitive)
- The character is enabled in `Settings.py`

### Slow Responses

- Use a smaller model (e.g., `llama3.2:1b` instead of `llama3.2:latest`)
- Reduce the number of active characters
- Lower the `TRIGGER_DEPTH` in settings

---

## 📜 Examples

### Example 1: Simple Chat

```
You: @homer What's your favorite food?

[HOMER]: Mmm... donuts... especially from Lard Lad! *drools*
```

### Example 2: Group Conversation

```
You: @family Let's have dinner!

[MARGE]: Alright everyone, dinner's ready!
[HOMER]: Mmm... dinner...
[BART]: Do we have to?
[LISA]: I'm practicing my saxophone.
[MAGGIE]: *sucking pacifier*
```

### Example 3: Location-Based Interaction

```
You: [Location: homer@moe: Moe's Tavern at the bar]
You: @homer What are you drinking?

[HOMER]: Just a nice cold Duff beer, Moe!
```

### Example 4: Scene Script

```
You: /scene
  [Location: homer@marge: Kitchen]
  Marge: Homer, we need to talk about your spending
  Homer: Uh oh...
  [Event] Marge shows Homer the credit card bill
  Homer: D'oh!
  /endscene
```

---

## 🎨 Color Coding

Each character has their own color for easy identification:

- **Homer**: Yellow
- **Marge**: Cyan
- **Bart**: Green
- **Lisa**: Magenta
- **Maggie**: White
- And many more unique colors!

---

## 📚 Project Structure

```
Simpsons-Ai/
├── SpringfieldChat.py      # Main chat application
├── character_base.py       # Base class for all characters
├── SceneView.py            # Conversation logging and display
├── SceneDirector.py        # AI scene management
├── Actions.py              # Character action handling
├── StranglingSequence.py   # Homer strangling Bart logic
├── NelsonSequence.py       # Nelson HA-HA logic
├── Settings.py             # Configuration
├── TODO.py                 # Development notes
├── Homer.py                # Homer character definition
├── Marge.py                # Marge character definition
├── Bart.py                 # Bart character definition
├── Lisa.py                 # Lisa character definition
├── Maggie.py               # Maggie character definition
├── ...                     # 50+ more character files
└── README.md               # This file
```

---

## 🤝 Contributing

Want to add a new character?

1. Create a new Python file (e.g., `CharacterName.py`)
2. Import `SimpsonsCharacter` from `character_base`
3. Define a system prompt that captures the character's personality
4. Create the character instance with name, system prompt, and color
5. Add the character to `Settings.py`
6. Import the character in `SpringfieldChat.py`

Example template:

```python
"""Example.py — Example AI"""
from character_base import SimpsonsCharacter

character = SimpsonsCharacter(
    name="Example",
    system_prompt="""
[Add a character description]

⚠️ CRITICAL RULE: Speak ONLY as Example Never voice other characters.

[Add personality]

[Add signature phrases]


[Final description]
""",
    color="\033[32m",
)

if __name__ == "__main__":
    character.run()
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Created by: johnny-pilotgenerativeai
- Inspired by: The Simpsons TV show (© 20th Century Fox)
- Powered by: Ollama and local LLM inference

---

## 🎉 Have Fun!

D'oh! Wait, that's not right... **Have fun exploring Springfield!**

Remember: In Springfield, anything can happen, and usually does!

```
   ███████╗██╗███╗   ██╗██████╗ ██████╗ ███████╗
   ██╔════╝██║████╗  ██║██╔══██╗██╔══██╗██╔════╝
   █████╗  ██║██╔██╗ ██║██║  ██║██████╔╝█████╗
   ██╔══╝  ██║██║╚██╗██║██║  ██║██╔══██╗██╔══╝
   ██║     ██║██║ ╚████║╚██████╔╝██║  ██║███████╗
   ╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝
```

**Welcome to Springfield!**
