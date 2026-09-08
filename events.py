import tkinter as tk
from PIL import Image, ImageTk
import pet

class Event:
    #inicio do def die
    def __init__(self, root, pet_instance, pet_label):
        self.root = root
        self.pet_instance = pet_instance
        self.pet_label = pet_label
        self.die_frames = []
        self.current_die_frame = 0
        self.load_die_animation()

    def load_die_animation(self):
        # Load and slice the death GIF frames
        try:
            die_gif = Image.open("frames/gifs/die.gif")
            while True:
                self.die_frames.append(ImageTk.PhotoImage(die_gif.copy()))
                die_gif.seek(len(self.die_frames))
        except EOFError:
            pass

    def die_event(self):
        # Stop any active wandering or walking loops if necessary
        # Play the death animation frames sequentially before closing
        if self.die_frames:
            frame = self.die_frames[self.current_die_frame]
            self.pet_label.config(image=frame)
            self.current_die_frame = (self.current_die_frame + 1) % len(self.die_frames)
            # Call the next frame after 100 milliseconds
            self.root.after(100, self.die_event)
        else:
            # If no frames are loaded, destroy immediately as fallback
            self.root.destroy()

            #fim def die

    def dialogue_event

    def crono_event

    def spotify_event