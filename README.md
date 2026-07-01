# fable

A terminal-based choose-your-own-adventure engine powered by YAML story modules.

Write your story in a single `.yaml` file, drop it in the `stories/` folder, and `fable_engine.py` handles the rest — typewriter text, animated scan bars, glitch effects, ASCII art, branching choices, stat tracking, inventory, flags, and multiple endings.

---

## Requirements

- Python 3.10+
- [PyYAML](https://pypi.org/project/PyYAML/)

```bash
pip install pyyaml
```

---

## Usage

```bash
# Interactive module picker — lists all stories in the stories/ folder
python3 fable_engine.py

# Load a specific story directly
python3 fable_engine.py stories/my_story.yaml
```

During play, type a number to make a choice. Press **Enter** to advance between scenes, or type **q** to quit at any time.

---

## Project Structure

```
fable/
├── fable_engine.py       # the engine
├── stories/
│   ├── my_story.yaml     # your story modules go here
│   └── another.yaml
├── AUTHORING.md          # full guide to writing story modules
└── README.md
```

---

## Writing Stories

Stories are plain YAML files. Here's the minimal skeleton:

```yaml
meta:
  title: "My Adventure"
  tagline: "A journey begins."
  start_scene: start
  end_scene: __end__
  stats:
    - id: courage
      label: "COURAGE   "
      start: 50
      colour: gold

ending_rules:
  - condition:
      stat_gte: {id: courage, value: 70}
    ending: hero
  - ending: forgotten

endings:
  hero:
    title: "A HERO RISES"
    colour: gold
    text:
      - text: "You did it."
        colour: gold

scenes:
  - id: start
    title: "THE BEGINNING"
    text:
      - text: "It was a dark and stormy night."
        colour: sand
    choice:
      prompt: "WHAT DO YOU DO?"
      options:
        - label: "Step outside"
          next: outside
          effects:
            - stat: courage
              delta: 10
        - label: "Stay inside"
          next: __end__

  - id: outside
    text:
      - text: "The rain soaks you immediately."
        colour: sand
    next: __end__
```

See **[AUTHORING.md](AUTHORING.md)** for the full reference — beats, conditions, flags, inventory, ASCII art, and more.

---

## Engine Features

- **Typewriter text** with configurable speed
- **Animated scan bars** and **glitch effects**
- **ASCII art** blocks per scene
- **Stat bars** displayed each scene (up to 100-point numeric stats)
- **Inventory** and **memory log** shown at the end of each run
- **Flags** for binary state (has_key, met_stranger, etc.)
- **Conditional options** — choices that only appear when conditions are met
- **Conditional beats** — show different text based on player state
- **Multiple endings** with ordered rule matching
- **Loop replay** — play again from the title screen, loop counter increments
- **Quit any time** by typing `q`

---

## Included Stories

| File | Description |
|------|-------------|
| `stories/neon_precinct.yaml` | A rain-soaked noir detective story. Gather evidence, manage heat, confront the killer. |

---

## Licence

[Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](LICENSE)

Free to use, share, and adapt for personal and non-commercial purposes, with attribution.
Commercial use is not permitted without explicit permission from the author.

