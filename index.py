import signal
import tkinter as tk

from events import Event
from pet import Pet
from window import Transparency

root = tk.Tk()
root.title("Desktop Pet")
root.overrideredirect(True)         # no borders
root.attributes("-topmost", True)   # always on top

transparency = Transparency(root)
pet_label = tk.Label(root, bg=transparency.bg, bd=0, highlightthickness=0)
pet_label.pack()

my_pet = Pet(root, pet_label, transparency)
pet_events = Event(root, my_pet)  # right-click the pet -> Exit


def close(*_):
    # first signal plays the death animation, a second one quits right away
    if pet_events.dying:
        root.destroy()
    else:
        pet_events.die_event()


root.protocol("WM_DELETE_WINDOW", pet_events.die_event)
signal.signal(signal.SIGINT, close)    # Ctrl+C
signal.signal(signal.SIGTERM, close)   # kill

my_pet.start()
root.mainloop()
