# Fable — Story Authoring Guide

Stories for Fable are plain YAML files. Drop them in the `stories/` folder and `fable_engine.py` will find them automatically.

---

## File Structure

A story module has four top-level keys:

```yaml
meta:          # title, stats, colours, start/end scene IDs
scenes:        # list of scene objects
ending_rules:  # ordered list of conditions → ending name
endings:       # named ending screens
```

---

## `meta`

| Key | Type | Description |
|-----|------|-------------|
| `title` | string | Shown on the title screen |
| `tagline` | string | Glitched under the title art |
| `subtitle` | string | Shown dimly below the tagline |
| `title_art` | multiline string | ASCII art for the title screen (use `\|` literal block) |
| `title_colour` | colour name | Colour for title art and tagline |
| `default_box_colour` | colour name | Default scene box border colour |
| `title_pause` | float | Seconds to pause on the title screen (default: 1.5) |
| `start_scene` | string | ID of the first scene |
| `end_scene` | string | Use `__end__` to trigger the ending screen |
| `stats` | list | See Stats below |

### Stats

```yaml
stats:
  - id: courage      # referenced in effects and conditions
    label: "COURAGE " # shown in the stat bar — pad labels to equal width
    start: 50         # starting value (0–100)
    colour: gold      # bar fill colour
```

### Available Colours

`gold` `rust` `sand` `steel` `red` `cyan` `white` `grey` `dim` `green` `purple` `blue`

---

## Scenes

Each entry in `scenes:` is a scene object:

```yaml
scenes:
  - id: my_scene
    title: "SCENE TITLE"       # shown in box header (optional)
    box_colour: gold           # border colour (falls back to default_box_colour)
    stats: true                # show stat bar? (default: true)
    text: [...]                # narrative lines shown in a framed box
    beats: [...]               # freeform render actions that follow the box
    effects: [...]             # state changes applied before the choice is shown
    choice:                    # optional — if absent, scene uses `next:`
      prompt: "What do you do?"
      options: [...]
    next: other_scene_id       # auto-advance target when there is no choice
```

### Text Lines

Items in `text:` can be a plain string or a block-style object:

```yaml
text:
  - "A plain line in the default sand colour."
  - text: "Bold gold header."
    colour: gold
    style: bold
  - text: "A dimmed hint."
    colour: dim
  - ""    # blank spacer line
```

**Substitutions** available anywhere in text strings:

| Token | Replaced with |
|-------|--------------|
| `{name}` | The player's name |
| `{loop}` | Current loop number |
| `{stat:id}` | Current numeric value of a stat |

---

## Beats

Beats are freeform render actions that run after the text box, in order. Each beat requires a `type:` field. All beats also accept an optional `condition:` (see Conditions) to show content only when certain state is met.

### `typeout`
Typewriter text printed character by character.
```yaml
- type: typeout
  text: "The door creaks open."
  colour: sand
  delay: 0.025    # seconds per character (optional, default: 0.025)
```

### `scan`
Animated progress bar — good for loading, scanning, or hacking moments.
```yaml
- type: scan
  text: "ANALYSING SAMPLE"
  duration: 2.0
  colour: cyan
```

### `glitch`
Text corrupts with random characters before resolving — good for dramatic reveals.
```yaml
- type: glitch
  text: "SOMETHING IS WRONG."
  colour: gold
  iterations: 6    # optional, default: 6
```

### `ascii`
Print a block of ASCII art. Avoid backslashes inside `|` literal blocks — use a quoted string with `\\n` instead if your art contains `\`.
```yaml
- type: ascii
  colour: rust
  art: |
    .---.
    |   |
    '---'
```

### `pause`
Silent delay with no output.
```yaml
- type: pause
  duration: 1.0
```

### `box`
Draw a framed box mid-scene, outside the main text box.
```yaml
- type: box
  title: "CLUE"
  colour: cyan
  lines:
    - text: "A name. A number."
      colour: sand
```

### `inline`
A simple indented line with no box.
```yaml
- type: inline
  text: "[ Item acquired: Skeleton Key ]"
  colour: gold
```

### `hline`
A horizontal divider line.
```yaml
- type: hline
  char: "─"
  colour: grey
```

---

## Effects

Effects mutate game state. They can appear at the scene level (applied before the choice) or on individual choice options (applied when chosen).

```yaml
effects:
  - stat: courage          # adjust a numeric stat
    delta: 15              # positive or negative; clamped to 0–100

  - set_flag: found_key    # set a boolean flag

  - add_item: "Skeleton Key"   # add to inventory (announced to player)

  - add_memory: "Met the stranger"  # add to the memory log shown at the end

  - set_name: true         # prompt the player to enter their name (stored as {name})
```

---

## Choices

```yaml
choice:
  prompt: "WHAT DO YOU DO?"
  options:
    - label: "Pick the lock"
      next: locked_room
      condition:           # optional — hides this option if condition fails
        item: "Skeleton Key"
      effects:             # optional — applied when this option is chosen
        - stat: courage
          delta: 10
```

Options whose `condition:` fails are hidden from the player. If no options pass, the scene falls through to `next:` or `__end__`.

---

## Conditions

All keys are optional and AND-combined — all specified keys must be true.

```yaml
condition:
  flag: "found_key"               # player has this flag set
  no_flag: "already_searched"     # player does NOT have this flag
  item: "Lantern"                 # item is in inventory
  stat_gte: {id: courage, value: 30}   # stat >= value
  stat_lte: {id: fear, value: 50}      # stat <= value
```

---

## Ending Rules

Evaluated top-to-bottom; the first matching rule wins. Always include a final entry with no condition as a fallback.

```yaml
ending_rules:
  - condition:
      stat_gte: {id: courage, value: 70}
      stat_lte: {id: fear, value: 30}
    ending: triumphant
  - condition:
      stat_gte: {id: fear, value: 60}
    ending: fled
  - ending: forgotten    # no condition = always matches
```

---

## Endings

```yaml
endings:
  triumphant:
    title: "VICTORY"
    colour: gold
    text:
      - text: "You faced it. You won."
        colour: gold
        style: bold
      - text: "The town will remember your name."
        colour: sand
```

---

## ASCII Art Tips

- Avoid `\` (backslashes) and `` ` `` (backticks) inside YAML `|` literal blocks — they can confuse the parser. If your art needs them, use a quoted string with `\\n` for newlines and `\\\\` for backslashes.
- Keep art indented consistently inside the block.
- Test art rendering in your terminal before committing — width varies.

---

## General Tips

- **Scene IDs** should be short lowercase slugs: `forest_path`, `act2_tower`
- **Use `__end__`** as a `next:` value or choice target to trigger the ending screen
- **Flags** are ideal for one-time events: meeting a character, finding an object, making a key choice
- **Pad stat labels** to equal width (e.g. `"COURAGE   "`) so the stat bar aligns
- **Blank lines** in `text:` are just `- ""` (an empty string entry)
- **Beat conditions** let you show different text depending on player state — great for branching flavour without branching scenes
- **The memory log** shown at the end is a great way to recap the player's unique path through the story

