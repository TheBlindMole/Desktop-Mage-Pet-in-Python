import tkinter as tk
import time
from pet import Pet
from events import Event

root = tk.Tk()

# Window settings
root.overrideredirect(True)
root.attributes('-topmost', True)  # Always on top
root.title("Desktop Pet")
root.minsize(300, 300)
root.attributes('-fullscreen', True)

# LINUX (GNOME) compatibility
root.wait_visibility(root)

# Transparency configuration
root.attributes("-alpha", 0.4)

# Function to update the machine's current time
def update_clock():
    current_time = time.strftime("%H:%M:%S")
    clock_label.config(text=current_time)
    root.after(1000, update_clock)

# --- TOP: Exit button ---
close_button = tk.Button(root, text="EXIT", command=root.destroy)
close_button.pack(side=tk.TOP, pady=20)

# --- CENTER: Label where the pet/GIF will run ---
pet_label = tk.Label(root)
pet_label.pack(expand=True)  # Centers the label in the middle of the screen

# --- BOTTOM: Clock label ---
clock_label = tk.Label(root, text="", font=("Arial", 20), fg="white", bg="black")
clock_label.pack(side=tk.BOTTOM, pady=5)

# --- BOTTOM (EXTRA): Dialogue label from events.py right below the clock ---
dialogue_label = tk.Label(root, text="Dialogue text will appear here...", font=("Arial", 14), fg="yellow", bg="black")
dialogue_label.pack(side=tk.BOTTOM, pady=10)

# Initialize the clock loop as soon as the window opens
update_clock()

# Instantiate the Pet and Events classes
my_pet = Pet(root, pet_label)
pet_events = Event(root, my_pet, pet_label, dialogue_label)

# Link the exit button to trigger the death animation and events
close_button.config(command=pet_events.die_event)

# Start wandering/walking behavior
my_pet.start_wandering()
my_pet.walk()

root.mainloop()
