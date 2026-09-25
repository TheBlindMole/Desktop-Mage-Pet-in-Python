import math
import random
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageOps, ImageSequence, ImageTk

from window import alpha_to_rects

GIF_DIR = Path(__file__).parent / "frames" / "gifs"

SCALE = 1.5               # sprite scale
OUTLINE = 3               # white border thickness, px
OUTLINE_COLOR = (255, 255, 255, 255)
TICK_MS = 33              # ~30 updates per second
WALK_SPEED = 60 * SCALE   # px/s (scaled with the sprite)
RUN_SPEED = 160 * SCALE   # px/s
WALK_RANGE = 350          # max distance of a walk target, px
MIN_TRAVEL = 80           # avoids tiny walks, px
RUN_MIN_TRAVEL = 300      # runs cover long distances, px
IDLE_TIME = (2.0, 5.0)    # seconds standing still
BODY_WIDTH = 64 * SCALE   # visible body inside the 128px frame,
BODY_HEIGHT = 70 * SCALE  # used to keep it on screen
DEAD_HEIGHT = 20 * SCALE  # body lying on the ground

# next action - weight
ACTIONS = {"walk": 40, "run": 15, "idle": 20, "jump": 10, "attack": 8, "magic_circle": 7}
LOOPING = {"walk", "run", "idle"}   # the others play once


def add_outline(image, thickness):
    """Surround the sprite with a border (adds `thickness` px of padding)."""
    t = thickness
    canvas = Image.new("RGBA", (image.width + 2 * t, image.height + 2 * t))
    canvas.paste(image, (t, t))
    mask = canvas.getchannel("A").point(lambda a: 255 if a else 0)
    grown = Image.new("L", canvas.size)
    for dx in range(-t, t + 1):
        for dy in range(-t, t + 1):
            if dx * dx + dy * dy <= t * t:  # round brush
                grown = ImageChops.lighter(grown, ImageChops.offset(mask, dx, dy))
    border = Image.new("RGBA", canvas.size, OUTLINE_COLOR)
    border.putalpha(grown)
    border.alpha_composite(canvas)  # sprite on top of the border
    return border


class Animation:
    """Frames (facing right and left), delays and X11 masks of one GIF."""

    def __init__(self, path, need_masks):
        self.frames = {1: [], -1: []}
        self.masks = {1: [], -1: []}
        self.delays = []
        with Image.open(path) as gif:
            for frame in ImageSequence.Iterator(gif):
                self.delays.append(max(20, frame.info.get("duration", 100)))
                right = frame.convert("RGBA")
                size = (round(right.width * SCALE), round(right.height * SCALE))
                right = add_outline(right.resize(size, Image.Resampling.NEAREST), OUTLINE)
                for side, image in ((1, right), (-1, ImageOps.mirror(right))):
                    self.frames[side].append(ImageTk.PhotoImage(image))
                    self.masks[side].append(alpha_to_rects(image) if need_masks else None)


class Pet:
    def __init__(self, root, label, transparency):
        self.root = root
        self.label = label
        self.transparency = transparency

        self.animations = {p.stem: Animation(p, transparency.needs_mask)
                           for p in sorted(GIF_DIR.glob("*.gif"))}
        missing = (set(ACTIONS) | {"die"}) - set(self.animations)
        if missing:
            raise FileNotFoundError(f"missing GIFs in {GIF_DIR}: {sorted(missing)}")

        first = self.animations["idle"].frames[1][0]
        self.width, self.height = first.width(), first.height()
        self.pad = OUTLINE      # border padding around the sprite

        self.on_action = None   # called with the action name when it starts
        self.on_move = None     # called after every move

        self.action = "idle"
        self.anim = self.animations["idle"]
        self.side = 1           # 1 = facing right, -1 = facing left
        self.x = self.y = 0.0   # feet position (bottom center of the sprite)
        self.autonomous = True  # False while a scripted animation plays

        self._frame = 0
        self._elapsed = 0.0     # ms spent on the current frame
        self._loop = True
        self._playing = True
        self._on_done = None
        self._target = (0.0, 0.0)
        self._idle_left = 0.0
        self._shown = None
        self._pos = None
        self._last_tick = 0.0

    #  public API 

    def start(self):
        x0, x1, y0, y1 = self._bounds()
        self.x, self.y = random.uniform(x0, x1), random.uniform(y0, y1)
        self.label.config(image=self.anim.frames[1][0])  # sizes the window
        self._place()
        self.root.update()  # map the window before sending the X11 mask
        self._start_action("idle")
        self._last_tick = time.monotonic()
        self._tick()

    def play_once(self, name, on_done=None):
        """Stop wandering and play one animation, holding its last frame."""
        self.autonomous = False
        self._on_done = on_done
        self._set_animation(name, loop=False)

    def head(self):
        """Point above the head, used to place the speech bubble."""
        return self.x, self.y - (DEAD_HEIGHT if self.action == "die" else BODY_HEIGHT)

    # main loop 

    def _tick(self):
        now = time.monotonic()
        dt = min(now - self._last_tick, 0.1)  # ignore long stalls
        self._last_tick = now

        if self._animate(dt):
            done, self._on_done = self._on_done, None
            if done:
                done()
            elif self.autonomous:
                self._choose_action()
        elif self.autonomous:
            self._behave(dt)

        self.root.after(TICK_MS, self._tick)

    def _animate(self, dt):
        """Advance frames. Returns True when a one-shot animation just ended."""
        if not self._playing:
            return False
        delays = self.anim.delays
        self._elapsed += dt * 1000
        finished = False
        while self._elapsed >= delays[self._frame]:
            self._elapsed -= delays[self._frame]
            if self._frame + 1 < len(delays):
                self._frame += 1
            elif self._loop:
                self._frame = 0
            else:
                self._playing = False
                finished = True
                break
        self._show_frame()
        return finished

    def _show_frame(self, force=False):
        key = (self.action, self.side, self._frame)
        if key == self._shown and not force:
            return
        self._shown = key
        self.label.config(image=self.anim.frames[self.side][self._frame])
        mask = self.anim.masks[self.side][self._frame]
        if mask:
            self.transparency.apply(mask)

    # --- behavior ---

    def _set_animation(self, name, loop):
        self.action = name
        self.anim = self.animations[name]
        self._frame, self._elapsed = 0, 0.0
        self._loop, self._playing = loop, True
        self._show_frame(force=True)

    def _start_action(self, name):
        self._set_animation(name, name in LOOPING)
        if name in ("walk", "run"):
            self._target = self._pick_target(far=(name == "run"))
            self.side = 1 if self._target[0] >= self.x else -1
            self._show_frame(force=True)  # apply the new facing
        elif name == "idle":
            self._idle_left = random.uniform(*IDLE_TIME)
        if self.on_action:
            self.on_action(name)

    def _choose_action(self):
        name = random.choices(list(ACTIONS), weights=list(ACTIONS.values()))[0]
        self._start_action(name)

    def _behave(self, dt):
        if self.action in ("walk", "run"):
            self._move(dt)
        elif self.action == "idle":
            self._idle_left -= dt
            if self._idle_left <= 0:
                self._choose_action()

    def _move(self, dt):
        speed = RUN_SPEED if self.action == "run" else WALK_SPEED
        tx, ty = self._target
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        step = speed * dt
        arrived = dist <= step
        if arrived:
            self.x, self.y = tx, ty
        else:
            self.x += dx / dist * step
            self.y += dy / dist * step
        self._place()
        if self.on_move:
            self.on_move()
        if arrived:
            self._choose_action()

    def _pick_target(self, far):
        x0, x1, y0, y1 = self._bounds()
        min_dist = RUN_MIN_TRAVEL if far else MIN_TRAVEL
        for _ in range(10):
            if far:
                tx, ty = random.uniform(x0, x1), random.uniform(y0, y1)
            else:
                tx = self.x + random.uniform(-WALK_RANGE, WALK_RANGE)
                ty = self.y + random.uniform(-WALK_RANGE / 2, WALK_RANGE / 2)
            tx, ty = min(max(tx, x0), x1), min(max(ty, y0), y1)
            if math.hypot(tx - self.x, ty - self.y) >= min_dist:
                break
        return tx, ty

    # geometry

    def _bounds(self):
        """Feet position limits: x0, x1, y0, y1."""
        half = BODY_WIDTH / 2
        return (half, self.root.winfo_screenwidth() - half,
                BODY_HEIGHT, self.root.winfo_screenheight())

    def _place(self):
        pos = (round(self.x - self.width / 2), round(self.y - self.height + self.pad))
        if pos != self._pos:
            self._pos = pos
            self.root.geometry(f"+{pos[0]}+{pos[1]}")
