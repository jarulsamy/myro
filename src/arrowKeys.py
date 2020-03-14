# -*- coding: utf-8 -*-
# from myro import *
import time
from tkinter import *

from myro import backward
from myro import forward
from myro import init
from myro import motors
from myro import stop
from myro import turnLeft
from myro import turnRight


init("COM5")


def keyup(e):
    stop()


def keydown(e):
    # print('down', e.char)
    key = e.char
    if key == "q":
        exit(0)
    elif key == "w":
        motors(5, 5)
    elif key == "s":
        motors(-5, -5)
    elif key == "a":
        motors(-5, 5)
    elif key == "d":
        motors(5, -5)


root = Tk()
frame = Frame(root, width=100, height=100)
frame.bind("<KeyPress>", keydown)
frame.bind("<KeyRelease>", keyup)
frame.pack()
frame.focus_set()
root.mainloop()
