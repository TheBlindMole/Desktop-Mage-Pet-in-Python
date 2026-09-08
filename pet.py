import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import os
import random
import event from events


class pet:

# inicio do walk aleatorio
    def __init__(self, root):
        self.root = root # é estupido mas precisa-se do root aqui
        #  Load GIF
        self.walk_gif = Image.open("frames/gifs/walk.gif")
        self.frames = []
        
        try:
            while True:
                self.frames.append(ImageTk.PhotoImage(self.walk_gif.copy()))
                self.walk_gif.seek(len(self.frames)) # Vai para o próximo frame
        except EOFError:
            pass # Fim dos quadros do GIF
            
        self.current_frame = 0

    def walk(self):

        if self.frames:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            
            # Chama o próximo frame da animação (a cada 100 milissegundos)
            self.root.after(100, self.walk)

    def start_wandering(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        new_x = random.randint(0, screen_width - 150)
        new_y = random.randint(0, screen_height - 150)
        self.root.geometry(f"+{new_x}+{new_y}")
        
        # Repete a movimentação a cada 4 segundos
        self.root.after(4000, self.start_wandering)

#Fim do walk aleatorio

    def idle(self, frames):
        img = Image.open("/frames/gifs/idle.gif")

    def run(self, frames):
        img = Image.open("/frames/gifs/run.gif")
    
    def magic_circle(self, frames):
        img = Image.open("/frames/gifs/magic_circle.gif")

    def die(self, frames):
        img = Image.open("/frames/gifs/die.gif")


