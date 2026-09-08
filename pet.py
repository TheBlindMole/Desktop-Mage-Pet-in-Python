import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import os
import event from events


class pet:

    def idle(self, frames):
        img = Image.open("/frames/gifs/idle.gif")

    def walk(self, frames):
        img = Image.open("/frames/gifs/walk.gif")

    def run(self, frames):
        img = Image.open("/frames/gifs/run.gif")
    
    def magic_circle(self, frames):
        img = Image.open("/frames/gifs/magic_circle.gif")

    def die(self, frames):
        img = Image.open("/frames/gifs/die.gif")


