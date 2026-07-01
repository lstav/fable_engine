#!/usr/bin/env python3
"""
adventure engine
────────────────
Loads a YAML story module and runs it as a terminal choose-your-own-adventure.

Usage:
    python3 engine.py                          # picks a story interactively
    python3 engine.py stories/westworld.yaml   # load a specific module
    python3 engine.py stories/my_story.yaml
"""

import sys, os, re, time, random, shutil, textwrap
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML not found. Installing…")
    os.system(f"{sys.executable} -m pip install pyyaml -q")
    import yaml


# ══════════════════════════════════════════════════════════════════════════════
#  TERMINAL / COLOUR HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def term_width():
    return shutil.get_terminal_size((80, 24)).columns

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def hide_cursor():
    sys.stdout.write("\033[?25l"); sys.stdout.flush()

def show_cursor():
    sys.stdout.write("\033[?25h"); sys.stdout.flush()

def pause(n=1.0):
    time.sleep(n)

# Named ANSI colours the story YAML can reference
COLOUR_MAP = {
    "gold":   "\033[38;5;178m",
    "rust":   "\033[38;5;166m",
    "sand":   "\033[38;5;223m",
    "steel":  "\033[38;5;250m",
    "red":    "\033[38;5;160m",
    "cyan":   "\033[38;5;81m",
    "white":  "\033[97m",
    "grey":   "\033[38;5;240m",
    "dim":    "\033[38;5;240m",
    "green":  "\033[38;5;114m",
    "purple": "\033[38;5;141m",
    "blue":   "\033[38;5;75m",
}
RESET = "\033[0m"
BOLD  = "\033[1m"

def ansi(name):
    """Return ANSI escape for a colour name, or empty string."""
    return COLOUR_MAP.get(str(name).lower(), "")

def coloured(text, colour):
    if not colour:
        return text
    return f"{ansi(colour)}{text}{RESET}"

def strip_ansi(s):
    return re.sub(r'\033\[[0-9;]*m', '', s)


# ══════════════════════════════════════════════════════════════════════════════
#  RENDERING PRIMITIVES
# ══════════════════════════════════════════════════════════════════════════════

def hline(char="─", colour="grey"):
    w = term_width()
    print(f"{ansi(colour)}{char * w}{RESET}")

def type_out(text, delay=0.025, colour="sand"):
    c = ansi(colour)
    sys.stdout.write(c)
    for ch in text:
        sys.stdout.write(ch); sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(RESET + "\n"); sys.stdout.flush()

def scan_bar(label="SCANNING", duration=2.0, colour="cyan"):
    w = min(term_width() - 4, 50)
    steps = 40
    c = ansi(colour)
    hide_cursor()
    for i in range(steps + 1):
        filled = int(w * i / steps)
        bar = "█" * filled + "░" * (w - filled)
        pct = int(100 * i / steps)
        sys.stdout.write(f"\r  {c}{label}  [{bar}] {pct:3d}%{RESET}")
        sys.stdout.flush()
        time.sleep(duration / steps)
    print(); show_cursor()

def glitch_text(text, colour="gold", iterations=6):
    chars = "░▒▓█▄▀■□▪▫◘◙∴∵∷"
    c = ansi(colour)
    hide_cursor()
    for _ in range(iterations):
        corrupted = "".join(
            random.choice(chars) if random.random() < 0.4 else ch
            for ch in text
        )
        sys.stdout.write(f"\r{c}{corrupted}{RESET}"); sys.stdout.flush()
        time.sleep(0.07)
    sys.stdout.write(f"\r{c}{BOLD}{text}{RESET}\n"); sys.stdout.flush()
    show_cursor()

def _wrap_rendered(line, width):
    """If a rendered line is wider than *width*, wrap the text portion into
    multiple lines, preserving the ANSI formatting prefix on each segment."""
    visible = strip_ansi(line)
    if len(visible) <= width:
        return [line]

    body = line[:-len(RESET)] if line.endswith(RESET) else line
    pos = 0
    if body.startswith("  "):
        pos = 2
    while pos < len(body) and body[pos] == '\033':
        end = body.find('m', pos)
        if end == -1:
            break
        pos = end + 1
    prefix = body[:pos]
    text  = body[pos:]

    wrap_w = width - 4
    segs = textwrap.wrap(text, wrap_w) if text else [text]
    return [f"{prefix}{s}{RESET}" for s in segs] if segs else [line]

def draw_box(lines, title="", colour="gold", width=None):
    """Draw a double-line box around a list of pre-coloured strings."""
    w = width or min(term_width(), 74)
    inner = w - 2
    tl, tr, bl, br, h, v = "╔", "╗", "╚", "╝", "═", "║"
    c = ansi(colour)

    if width is None:
        max_visible = max((len(strip_ansi(l)) for l in lines), default=0)
        if title:
            max_visible = max(max_visible, len(title) + 2)
        box_w = min(w, max_visible + 6)
        inner = box_w - 2

    max_content = inner - 2
    # top
    sys.stdout.write(f"{c}{tl}")
    if title:
        t = f" {title} "
        pad = inner - len(t)
        lp, rp = pad // 2, pad - pad // 2
        sys.stdout.write(f"{h*lp}{BOLD}{c}{t}{c}{h*rp}")
    else:
        sys.stdout.write(h * inner)
    print(f"{tr}{RESET}")
    # body
    for line in lines:
        for wrapped in _wrap_rendered(line, max_content):
            raw_len = len(strip_ansi(wrapped))
            padding = max_content - raw_len
            print(f"{c}{v}{RESET} {wrapped}{' '*padding} {c}{v}{RESET}")
    # bottom
    print(f"{c}{bl}{h*inner}{br}{RESET}")

def stat_bar(label, value, max_val=100, width=20, hi="gold", lo="grey"):
    filled = int(width * value / max_val)
    bar = f"{ansi(hi)}{'█'*filled}{ansi(lo)}{'░'*(width-filled)}{RESET}"
    return f"{ansi('dim')}{label}:{RESET} {bar} {ansi('dim')}{value}{RESET}"

def draw_ascii(art, colour="gold"):
    c = ansi(colour)
    for line in art.split("\n"):
        print(f"{c}{line}{RESET}")

def print_inline(text, colour="sand"):
    print(f"  {ansi(colour)}{text}{RESET}")


# ══════════════════════════════════════════════════════════════════════════════
#  GAME STATE
# ══════════════════════════════════════════════════════════════════════════════

class State:
    """
    Holds everything mutable about the current run.
    Stats are initialised from story['meta']['stats'].
    """
    def __init__(self, stat_defs: list):
        self.vars: dict[str, int]  = {}   # numeric stats
        self.flags: set[str]       = set() # boolean flags
        self.inventory: list[str]  = []
        self.memories: list[str]   = []
        self.loop: int             = 1
        self.name: str             = "Stranger"

        for s in stat_defs:
            self.vars[s["id"]] = s.get("start", 0)

    # ── stat helpers ──────────────────────────────────────────────────────────

    def adjust(self, stat, delta):
        if stat in self.vars:
            self.vars[stat] = max(0, min(100, self.vars[stat] + delta))

    def set_flag(self, flag):
        self.flags.add(flag)

    def has_flag(self, flag):
        return flag in self.flags

    def has_item(self, item):
        return item in self.inventory


# ══════════════════════════════════════════════════════════════════════════════
#  CONDITION / EFFECT EVALUATOR
# ══════════════════════════════════════════════════════════════════════════════

def eval_condition(cond: dict | None, state: State) -> bool:
    """
    Supported condition keys (all optional, AND-combined):
      flag: "flag_name"          state must have this flag
      no_flag: "flag_name"       state must NOT have this flag
      item: "item_name"          inventory must contain item
      stat_gte: {id, value}      stat >= value
      stat_lte: {id, value}      stat <= value
    """
    if not cond:
        return True
    if "flag" in cond and not state.has_flag(cond["flag"]):
        return False
    if "no_flag" in cond and state.has_flag(cond["no_flag"]):
        return False
    if "item" in cond and not state.has_item(cond["item"]):
        return False
    if "stat_gte" in cond:
        s = cond["stat_gte"]
        if state.vars.get(s["id"], 0) < s["value"]:
            return False
    if "stat_lte" in cond:
        s = cond["stat_lte"]
        if state.vars.get(s["id"], 0) > s["value"]:
            return False
    return True

def apply_effects(effects: list | None, state: State):
    """
    Each effect is a dict with one of:
      {stat: id, delta: n}          adjust a numeric stat
      {set_flag: "name"}            set a boolean flag
      {add_item: "name"}            add to inventory
      {add_memory: "text"}          add to memories list
      {set_name: true}              prompt player for their name
    """
    if not effects:
        return
    for eff in effects:
        if "stat" in eff:
            state.adjust(eff["stat"], eff.get("delta", 0))
        if "set_flag" in eff:
            state.set_flag(eff["set_flag"])
        if "add_item" in eff:
            item = eff["add_item"]
            if item not in state.inventory:
                state.inventory.append(item)
                print_inline(f"[ Item added: {item} ]", colour="gold")
        if "add_memory" in eff:
            mem = eff["add_memory"]
            if mem not in state.memories:
                state.memories.append(mem)
        if eff.get("set_name"):
            sys.stdout.write(f"  {ansi('gold')}Your name: {RESET}")
            sys.stdout.flush()
            name = input().strip() or "Stranger"
            state.name = name


# ══════════════════════════════════════════════════════════════════════════════
#  QUIT
# ══════════════════════════════════════════════════════════════════════════════

def quit_game():
    clear()
    hline(colour="gold")
    print()
    glitch_text("  Goodbye for now...", colour="gold")
    print(f"\n  {ansi('dim')}Session ended. Goodbye.{RESET}\n")
    hline(colour="gold")
    print()
    show_cursor()
    sys.exit(0)


# ══════════════════════════════════════════════════════════════════════════════
#  SCENE RENDERER
# ══════════════════════════════════════════════════════════════════════════════

def render_text(raw: str, state: State) -> str:
    """Substitute {name}, {loop}, {stat:id} into text."""
    text = str(raw)
    text = text.replace("{name}", state.name)
    text = text.replace("{loop}", str(state.loop))
    for sid, val in state.vars.items():
        text = text.replace(f"{{stat:{sid}}}", str(val))
    return text

def render_line(line_def, state: State) -> str:
    """
    A line in a scene's 'text' block can be:
      - a plain string
      - {text: "...", colour: "gold"}
      - {text: "...", style: "bold"}
    """
    if isinstance(line_def, str):
        return f"  {ansi('sand')}{render_text(line_def, state)}{RESET}"
    text = render_text(line_def.get("text", ""), state)
    colour = line_def.get("colour", line_def.get("color", "sand"))
    bold_it = line_def.get("style") == "bold"
    prefix = BOLD if bold_it else ""
    return f"  {prefix}{ansi(colour)}{text}{RESET}"

def show_stats_bar(story_meta: dict, state: State):
    stats = story_meta.get("stats", [])
    if not stats:
        return
    hline("─", "grey")
    parts = []
    for s in stats:
        sid = s["id"]
        label = s.get("label", sid.upper())
        hi = s.get("colour", s.get("color", "gold"))
        parts.append(stat_bar(f"{label:10}", state.vars.get(sid, 0), hi=hi))
    # Print two per row
    for i in range(0, len(parts), 2):
        row = parts[i:i+2]
        print("  " + "    ".join(row))
    if state.inventory:
        print(f"  {ansi('dim')}Items: {', '.join(state.inventory)}{RESET}")
    if state.memories:
        print(f"  {ansi('dim')}Memories: {len(state.memories)}{RESET}")
    hline("─", "grey")
    print()

def run_beat(beat: dict, state: State):
    """
    Execute a single beat (an entry in a scene's 'beats' list).
    Beat types: typeout | scan | glitch | ascii | pause | box | inline | input
    """
    btype = beat.get("type", "typeout")
    text  = render_text(beat.get("text", ""), state)
    colour = beat.get("colour", beat.get("color", "sand"))
    duration = beat.get("duration", 2.0)

    if btype == "typeout":
        type_out(f"  {text}", delay=beat.get("delay", 0.025), colour=colour)
    elif btype == "scan":
        scan_bar(text or "SCANNING", duration=duration, colour=colour)
    elif btype == "glitch":
        glitch_text(f"  {text}", colour=colour, iterations=beat.get("iterations", 6))
    elif btype == "ascii":
        draw_ascii(beat.get("art", ""), colour=colour)
    elif btype == "pause":
        pause(duration)
    elif btype == "inline":
        print_inline(text, colour=colour)
    elif btype == "box":
        lines_raw = beat.get("lines", [text] if text else [])
        lines = [render_line(l, state) for l in lines_raw]
        draw_box(lines, title=beat.get("title", ""), colour=colour,
                 width=beat.get("width"))
    elif btype == "hline":
        hline(beat.get("char", "─"), colour=colour)


def run_scene(scene: dict, story: dict, state: State) -> str:
    """
    Render a scene and return the id of the next scene to go to.
    Scene structure (all optional except 'id'):
      id, title, box_colour, stats: true/false
      text: [line, ...]        shown in a box
      beats: [beat, ...]       freeform render actions
      effects: [effect, ...]   applied before choice
      choice:
        prompt: "text"
        options:
          - label: "text"
            next: scene_id
            condition: {...}
            effects: [...]
      next: scene_id           used when there's no choice (auto-advance)
    """
    clear()

    meta = story.get("meta", {})
    if scene.get("stats", True):
        show_stats_bar(meta, state)

    # Box of narrative text
    text_lines = scene.get("text", [])
    if text_lines:
        rendered = [render_line(l, state) for l in text_lines]
        title = scene.get("title", "")
        colour = scene.get("box_colour", scene.get("box_color",
                 meta.get("default_box_colour", meta.get("default_box_color", "gold"))))
        draw_box(rendered, title=title, colour=colour)
        print()

    # Freeform beats
    for beat in scene.get("beats", []):
        if eval_condition(beat.get("condition"), state):
            run_beat(beat, state)

    # Scene-level effects (run after display, before choice)
    apply_effects(scene.get("effects", []), state)

    # Choice block
    choice_def = scene.get("choice")
    if choice_def:
        options_raw = choice_def.get("options", [])
        # Filter by condition
        options = [o for o in options_raw if eval_condition(o.get("condition"), state)]
        if not options:
            # No valid options → go to fallback or end
            return scene.get("next", story.get("meta", {}).get("end_scene", "end"))

        prompt = render_text(choice_def.get("prompt", "What do you do?"), state)
        draw_box([f"  {ansi('sand')}{prompt}{RESET}"], colour="gold")
        print()
        for i, opt in enumerate(options, 1):
            label = render_text(opt.get("label", "…"), state)
            print(f"  {ansi('gold')}{BOLD}{i}.{RESET}  {ansi('steel')}{label}{RESET}")
        print()

        print(f"  {ansi('gold')}{BOLD}q.{RESET}  {ansi('dim')}Quit game{RESET}")
        print()
        while True:
            sys.stdout.write(f"  {ansi('gold')}▶ {RESET}")
            sys.stdout.flush()
            try:
                raw = input().strip().lower()
                if raw in ("q", "quit", "exit"):
                    quit_game()
                idx = int(raw) - 1
                if 0 <= idx < len(options):
                    chosen = options[idx]
                    print()
                    type_out(f"  » {render_text(chosen['label'], state)}",
                             delay=0.015, colour="sand")
                    print()
                    apply_effects(chosen.get("effects", []), state)
                    return chosen.get("next", story.get("meta", {}).get("end_scene", "end"))
            except (ValueError, KeyboardInterrupt):
                pass
            print(f"  {ansi('red')}Invalid choice.{RESET}")

    # No choice -> prompt player to continue, then advance
    next_id = scene.get("next", story.get("meta", {}).get("end_scene", "end"))
    if next_id and next_id != "__end__":
        print()
        sys.stdout.write(f"  {ansi('dim')}[ Press Enter to continue, or Q to quit ]{RESET}")
        sys.stdout.flush()
        try:
            raw = input().strip().lower()
            if raw in ("q", "quit", "exit"):
                quit_game()
        except KeyboardInterrupt:
            pass
    return next_id


# ══════════════════════════════════════════════════════════════════════════════
#  STORY RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_story(story: dict):
    meta   = story.get("meta", {})
    scenes = {s["id"]: s for s in story.get("scenes", [])}
    stat_defs = meta.get("stats", [])

    state = State(stat_defs)
    state.loop = 1

    while True:
        # Title screen
        clear()
        title_art = meta.get("title_art")
        title_colour = meta.get("title_colour", meta.get("title_color", "gold"))
        if title_art:
            draw_ascii(title_art, colour=title_colour)
            print()
        else:
            print(f"\n  {ansi(title_colour)}{BOLD}{meta.get('title','ADVENTURE')}{RESET}\n")

        tagline = meta.get("tagline")
        if tagline:
            glitch_text(f"  {tagline}", colour=title_colour)
        subtitle = meta.get("subtitle")
        if subtitle:
            print(f"\n  {ansi('dim')}{subtitle}{RESET}\n")
        print(f"  {ansi('dim')}Loop {state.loop}{RESET}")
        print()
        hline(colour="grey")
        pause(meta.get("title_pause", 1.5))

        # Run scenes
        current_id = meta.get("start_scene", "start")
        while current_id and current_id != "__end__":
            scene = scenes.get(current_id)
            if not scene:
                print(f"\n  {ansi('red')}[Engine] Scene not found: '{current_id}'{RESET}\n")
                break
            current_id = run_scene(scene, story, state)

        # End summary
        clear()
        hline(colour="gold")
        end_scenes = story.get("endings", {})
        # pick ending by evaluating conditions in order
        chosen_end = None
        for end_def in story.get("ending_rules", []):
            if eval_condition(end_def.get("condition"), state):
                chosen_end = end_def.get("ending")
                break

        if chosen_end and chosen_end in end_scenes:
            e = end_scenes[chosen_end]
            lines = [render_line(l, state) for l in e.get("text", [])]
            draw_box(lines, title=e.get("title", "THE END"),
                     colour=e.get("colour", e.get("color", "gold")), width=62)
        else:
            draw_box([f"  {ansi('sand')}Your story ends here.{RESET}"],
                     title="THE END", colour="gold")

        # Memory log
        if state.memories:
            print()
            print(f"  {ansi('dim')}┌─ MEMORIES ─────────────────────────────────────────")
            for m in state.memories:
                print(f"  │  ◈ {m}")
            print(f"  └─────────────────────────────────────────────────{RESET}")

        # Play again?
        print()
        again_colour = meta.get("default_box_colour", "gold")
        draw_box([f"  {ansi('sand')}Begin a new loop?{RESET}"], colour=again_colour)
        print()
        print(f"  {ansi('gold')}{BOLD}1.{RESET}  {ansi('steel')}Yes — loop again{RESET}")
        print(f"  {ansi('gold')}{BOLD}2.{RESET}  {ansi('steel')}No  — exit{RESET}")
        print()
        sys.stdout.write(f"  {ansi('gold')}▶ {RESET}"); sys.stdout.flush()
        try:
            raw = input().strip()
        except KeyboardInterrupt:
            raw = "2"
        if raw == "1":
            new_loop = state.loop + 1
            state.__init__(stat_defs)
            state.loop = new_loop
        else:
            break

    clear()
    hline(colour="gold")
    print()
    tagline = meta.get("tagline", "")
    if tagline:
        glitch_text(f"  {tagline}", colour=title_colour)
    print(f"\n  {ansi('dim')}Thank you for playing.{RESET}\n")
    hline(colour="gold")
    print()


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE PICKER
# ══════════════════════════════════════════════════════════════════════════════

def pick_story() -> Path:
    """If no file argument given, list available YAML modules and let user pick."""
    search_dirs = [Path("."), Path("stories")]
    candidates = []
    for d in search_dirs:
        if d.exists():
            candidates.extend(sorted(d.glob("*.yaml")) + sorted(d.glob("*.yml")))
    # Deduplicate
    seen, unique = set(), []
    for p in candidates:
        rp = str(p.resolve())
        if rp not in seen:
            seen.add(rp); unique.append(p)

    if not unique:
        print(f"\n  {ansi('red')}No story modules found.{RESET}")
        print(f"  Place .yaml files in the current directory or a 'stories/' subfolder.\n")
        sys.exit(1)

    if len(unique) == 1:
        return unique[0]

    clear()
    print(f"\n  {ansi('gold')}{BOLD}STORY MODULES{RESET}\n")
    hline(colour="grey")
    print()
    for i, p in enumerate(unique, 1):
        # Try to read title from yaml quickly
        try:
            with open(p) as f:
                data = yaml.safe_load(f)
            title = data.get("meta", {}).get("title", p.stem)
            tagline = data.get("meta", {}).get("tagline", "")
        except Exception:
            title, tagline = p.stem, ""
        print(f"  {ansi('gold')}{BOLD}{i}.{RESET}  {ansi('steel')}{title}{RESET}  "
              f"{ansi('dim')}{tagline}{RESET}")
        print(f"      {ansi('dim')}{p}{RESET}")
    print()
    while True:
        sys.stdout.write(f"  {ansi('gold')}▶ Choose a module: {RESET}")
        sys.stdout.flush()
        try:
            raw = input().strip()
            idx = int(raw) - 1
            if 0 <= idx < len(unique):
                return unique[idx]
        except (ValueError, KeyboardInterrupt):
            sys.exit(0)
        print(f"  {ansi('red')}Invalid.{RESET}")


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        if not path.exists():
            print(f"  File not found: {path}")
            sys.exit(1)
    else:
        path = pick_story()

    with open(path, "r", encoding="utf-8") as f:
        story = yaml.safe_load(f)

    hide_cursor()
    try:
        run_story(story)
    except KeyboardInterrupt:
        print(f"\n  {ansi('dim')}Session interrupted.{RESET}\n")
    finally:
        show_cursor()

if __name__ == "__main__":
    main()

