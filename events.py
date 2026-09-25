import json
import random
import time
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont

DIALOGUES_FILE = Path(__file__).parent / "dialogues.json"

LANGUAGE = "english"        # key used in dialogues.json
SPEAK_CHANCE = 0.5          # chance to talk when an action starts
COOLDOWN = 8.0              # seconds of silence after a line
BUBBLE_BASE_MS = 2000       # minimum time a line stays on screen
BUBBLE_MS_PER_CHAR = 50     # extra time per character
BUBBLE_WRAP = 240           # px
BUBBLE_GAP = 8              # px between bubble and pet
DEATH_HOLD_MS = 500         # pause after the last line before closing


class Event:
    def __init__(self, root, pet):
        self.root = root
        self.pet = pet
        self.dialogues = self._load_dialogues()
        self.dying = False

        self._visible = False
        self._hide_id = None
        self._hide_at = 0.0       # monotonic time the bubble goes away
        self._quiet_until = 0.0   # no automatic lines before this time
        self._last_line = None
        self._bubble_size = (0, 0)
        self._bubble_pos = None

        self._build_bubble()
        self._build_menu()

        pet.on_action = self._on_pet_action
        pet.on_move = self._reposition_bubble
        pet.label.bind("<Button-1>", lambda _e: self.dialogue_event(force=True))
        pet.label.bind("<Button-3>", self._show_menu)

    # --- events ---

    def dialogue_event(self, action=None, force=False):
        """Show a random line for the action (defaults to the current one)."""
        if not force and (self.dying or time.monotonic() < self._quiet_until):
            return
        lines = self.dialogues.get(action or self.pet.action)
        if not lines:
            return
        texts = [self._text(line) for line in lines]
        text = random.choice([t for t in texts if t != self._last_line] or texts)
        self._last_line = text
        self._say(text)

    def die_event(self):
        """Say goodbye, play the death animation and close the app."""
        if self.dying:
            return
        self.dying = True
        self.pet.play_once("die", on_done=self._close_after_bubble)
        self.dialogue_event("die", force=True)

    def crono_event(self):
        pass  # TODO

    def spotify_event(self):
        pass  # TODO

    # --- internals ---

    def _load_dialogues(self):
        with open(DIALOGUES_FILE, encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _text(line):
        return line.get(LANGUAGE) or line["english"]

    def _on_pet_action(self, name):
        if random.random() < SPEAK_CHANCE:
            self.dialogue_event(name)

    def _close_after_bubble(self):
        # let the last line be read before closing
        remaining_ms = max(0.0, self._hide_at - time.monotonic()) * 1000
        self.root.after(int(remaining_ms) + DEATH_HOLD_MS, self.root.destroy)

    # --- speech bubble ---

    def _build_bubble(self):
        self.bubble = tk.Toplevel(self.root)
        self.bubble.withdraw()
        self.bubble.overrideredirect(True)
        self.bubble.attributes("-topmost", True)
        self._font = tkfont.nametofont("TkDefaultFont").copy()  # keep a reference
        self._font.configure(size=11)
        self.bubble_label = tk.Label(
            self.bubble, font=self._font, wraplength=BUBBLE_WRAP, justify="center",
            bg="#fffbe6", fg="#222222", padx=10, pady=6, bd=0,
            highlightthickness=2, highlightbackground="#222222")
        self.bubble_label.pack()
        self.bubble.bind("<Button-1>", lambda _e: self._hide_bubble())  # click to dismiss
        self.bubble_label.bind("<Button-1>", lambda _e: self._hide_bubble())

    def _say(self, text):
        if self._hide_id:
            self.root.after_cancel(self._hide_id)
        self.bubble_label.config(text=text)
        self.bubble.update_idletasks()
        self._bubble_size = (self.bubble.winfo_reqwidth(), self.bubble.winfo_reqheight())

        duration = BUBBLE_BASE_MS + BUBBLE_MS_PER_CHAR * len(text)
        self._hide_at = time.monotonic() + duration / 1000
        self._quiet_until = self._hide_at + COOLDOWN
        self._visible = True
        self._bubble_pos = None
        self._reposition_bubble()
        self.bubble.deiconify()
        self._hide_id = self.root.after(duration, self._hide_bubble)

    def _hide_bubble(self):
        if self._hide_id:
            self.root.after_cancel(self._hide_id)
        self._hide_id = None
        self._visible = False
        self.bubble.withdraw()

    def _reposition_bubble(self):
        if not self._visible:
            return
        width, height = self._bubble_size
        cx, head_y = self.pet.head()
        x = min(max(cx - width / 2, 0), self.root.winfo_screenwidth() - width)
        y = head_y - height - BUBBLE_GAP
        if y < 0:  # no room above, show below the feet
            y = self.pet.y + BUBBLE_GAP
        pos = (round(x), round(y))
        if pos != self._bubble_pos:
            self._bubble_pos = pos
            self.bubble.geometry(f"+{pos[0]}+{pos[1]}")

    # --- context menu ---

    def _build_menu(self):
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Exit", command=self.die_event)

    def _show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()
