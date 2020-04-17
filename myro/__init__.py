import atexit
import glob
import os
import random
import signal
import sys
import threading
import time
import traceback

import serial
from PIL import Image
from PIL import ImageChops

from . import globvars
from .graphics import AskDialog
from .graphics import Calibrate
from .graphics import Color
from .graphics import GraphWin
from .graphics import Picture
from .graphics import Pixel
from .graphics import Point
from .robot import Robot
from .robots.scribbler import Scribbler
from .robots.simulator import SimScribbler
from .version import __VERSION__

# import atexit
# import glob
# import io
# import os
# import pickle
# import random
# import signal
# import sys
# import threading
# import time
# import urllib.error
# import urllib.parse
# import urllib.request

# import globvars
# import myro.graphics
# import pygame
# from myro.chat import *
# from myro.graphics import *
# from myro.media import *
# from myro.robots.epuck import Epuck
# from .robots.scribbler import Scribbler

# from myro.robots.simulator import SimScribbler
# from myro.robots.surveyor import Surveyor
# from myro.system import *
# from myro.robots.surveyor import watch


# Check versions of things:
# _pil_version = None
# try:
#     import PIL.Image as Image
#     _pil_version = Image.VERSION
#     del Image
# except:
#     print("ERROR: you need to install Python Image Library to make pictures", file=sys.stderr)
# if _pil_version is not None:
#     if _pil_version.split(".") < ["1", "1", "5"]:
#         print(("ERROR: you need to upgrade Python Image Library to at least 1.1.5 (you're running %s)" %
#                               _pil_version), file=sys.stderr)
# del _pil_version


def timer(seconds=0):
    """ A function to be used with 'for' """
    start = time.time()
    while True:
        timepast = time.time() - start
        if seconds != 0 and timepast > seconds:
            raise StopIteration
        yield round(timepast, 3)


_timers = {}


def timeRemaining(seconds=0):
    """ Function to be used with 'while' """
    global _timers
    if seconds == 0:
        return True
    now = time.time()
    stack = traceback.extract_stack()
    filename, line_no, q1, q2 = stack[-2]
    if filename.startswith("<pyshell"):
        filename = "pyshell"
    if (filename, line_no) not in _timers:
        _timers[(filename, line_no)] = (now, seconds)
        return True
    start, duration = _timers[(filename, line_no)]
    if seconds != duration:
        _timers[(filename, line_no)] = (now, seconds)
        return True
    if now - start > duration:
        del _timers[(filename, line_no)]
        return False
    else:
        return True


pickled = None


def wait(seconds):
    """
    Wrapper for time.sleep() so it can be later overloaded.
    """
    return time.sleep(seconds)


def currentTime():
    """
    Returns current time in seconds since
    """
    return time.time()


def pickOne(*args):
    """
    Randomly pick one of a list, or one between [0, arg).
    """
    if len(args) == 1:
        return random.randrange(args[0])
    else:
        return args[random.randrange(len(args))]


def pickOneInRange(start, stop):
    """
    Randomly pick one of a list, or one between [0, arg).
    """
    return random.randrange(start, stop)


def heads():
    return flipCoin() == "heads"


def tails():
    return flipCoin() == "tails"


def flipCoin():
    """
    Randomly returns "heads" or "tails".
    """
    return ("heads", "tails")[random.randrange(2)]


def randomNumber():
    """
    Returns a number between 0 (inclusive) and 1 (exclusive).
    """
    return random.random()


def ask(item, title="Information Request", useCache=0, useDict=0):
    """ Ask the user for a value """
    if type(item) in [list, tuple] and len(item) == 1:
        item = item[0]
    retval = _ask(item, title=title, useCache=useCache)
    if useDict:
        if "ok" in retval:
            del retval["ok"]
        return retval
    elif len(list(retval.keys())) == 1:
        return retval[item]
    elif len(list(retval.keys())) == 2 and "ok" in list(retval.keys()):
        return retval[item]
    else:
        return retval


def _ask(data, title="Information Request", forceAsk=1, forceConsole=0, useCache=1):
    """ Given a dictionary return dictionary with answers. """
    if type(data) in [str]:
        data = {data: ""}
    if type(data) in [list, tuple]:
        newData = {}
        for item in data:
            newData[item] = ""
        data = newData
    if useCache:
        # get data, if in cache:
        needToAsk = 0
        for question in list(data.keys()):
            if question in list(globvars.askData.keys()):
                data[question] = globvars.askData[question]
            else:
                needToAsk = 1
    else:
        needToAsk = 1
    # if I got it all, and don't need to ask, return
    # else, ask it all:
    if needToAsk or forceAsk:
        if globvars.gui is None or forceConsole:
            _askConsole(data, title)
        else:
            data = _askGUI(data, title)
            if data["ok"] == 0:
                raise KeyboardInterrupt
        # cache data in globals:
        for text in list(data.keys()):
            globvars.askData[text] = data[text]
    return data


def _askGUI(qdict, title="Information Request"):
    d = AskDialog(title, qdict)
    ok = d.run()
    if ok:
        retval = {"ok": 1}
        for name in list(qdict.keys()):
            retval[name] = d.textbox[name].get()
        d.stop()
        return retval
    else:
        d.stop()
        return {"ok": 0}


def _askConsole(data, title="Information Request"):
    print("+-----------------------------------------------------------------+")
    print("|" + title.center(65) + "|")
    print("+-----------------------------------------------------------------+")
    print("| Please enter the following information. Default values are in   |")
    print("| brackets. To accept default values, just press enter.           |")
    print("------------------------------------------------------------------")
    for key in list(data.keys()):
        retval = input("   " + key + (" [%s]" % data[key]) + ": ")
        retval.strip()  # remove any spaces on either side
        if retval != "":
            data[key] = retval
    return data


class Computer(Robot):
    """ An interface to computer devices. """

    def __init__(self):
        """ Constructs a computer object. """
        Robot.__init__(self)
        self.lock = threading.Lock()

    def move(self, translate, rotate):
        """ Moves the robot translate, rotate velocities. """
        print("move(%f, %f)" % (translate, rotate))

    def speak(self, message, async_=0):
        """ Speaks a text message. """
        if globvars.tts is not None:
            globvars.tts.speak(message, async_)
        else:
            print("Text-to-speech is not loaded")

    def get(self, what):
        return {}

    def stopSpeaking(self):
        if globvars.tts is not None:
            globvars.tts.stop()
        else:
            print("Text-to-speech is not loaded")

    def setVoice(self, name):
        if globvars.tts is not None:
            globvars.tts.setVoice(name)
        else:
            print("Text-to-speech is not loaded")

    def getVoice(self):
        if globvars.tts is not None:
            return str(globvars.tts.getVoice())
        else:
            print("Text-to-speech is not loaded")

    def getVoices(self):
        if globvars.tts is not None:
            return list(map(str, globvars.tts.getVoices()))
        else:
            print("Text-to-speech is not loaded")

    def playSpeech(self, filename):
        if globvars.tts is not None:
            globvars.tts.playSpeech(filename)
        else:
            print("Text-to-speech is not loaded")

    def saveSpeech(self, message, filename):
        if globvars.tts is not None:
            globvars.tts.saveSpeech(message, filename)
        else:
            print("Text-to-speech is not loaded")


computer = Computer()


def _cleanup():
    if globvars.robot:
        if "robot" in globvars.robot.robotinfo:
            try:
                globvars.robot.stop()  # hangs?
                time.sleep(0.5)
            except serial.SerialException:  # catch serial.SerialException
                # port already closed
                pass
        try:
            globvars.robot.close()
        except Exception:
            pass


def ctrlc_handler(signum, frame):
    if globvars.robot:
        # globvars.robot.open()
        # print "done opening"
        globvars.robot.manual_flush()
        if "robot" in globvars.robot.robotinfo:
            globvars.robot.hardStop()
    # raise KeyboardInterrupt
    orig_ctrl_handler()


orig_ctrl_handler = signal.getsignal(signal.SIGINT)
# Set the signal handler and a 5-second alarm
signal.signal(signal.SIGINT, ctrlc_handler)

# Get ready for user prompt; set up environment:
if not globvars.setup:
    globvars.setup = 1
    atexit.register(_cleanup)
    # Ok, now we're ready!
    print(f"Myro version {__VERSION__} is ready!", file=sys.stderr)

# Functional interface:


def requestStop():
    if globvars.robot:
        globvars.robot.requestStop = 1


def initialize(id_=None):
    if id_ == "simulator":
        simulator(None)
    else:
        globvars.robot = Scribbler(id_)
    __builtins__["robot"] = globvars.robot


init = initialize


def simulator(id_=None):
    _startSimulator()
    time.sleep(2)
    globvars.robot = SimScribbler(id_)
    __builtins__["robot"] = globvars.robot


def translate(amount):
    if globvars.robot:
        return globvars.robot.translate(amount)
    else:
        raise AttributeError("need to initialize robot")


def rotate(amount):
    if globvars.robot:
        return globvars.robot.rotate(amount)
    else:
        raise AttributeError("need to initialize robot")


def move(translate, rotate):
    if globvars.robot:
        return globvars.robot.move(translate, rotate)
    else:
        raise AttributeError("need to initialize robot")


def forward(speed=1, seconds=None):
    if globvars.robot:
        return globvars.robot.forward(speed, seconds)
    else:
        raise AttributeError("need to initialize robot")


def backward(speed=1, seconds=None):
    if globvars.robot:
        return globvars.robot.backward(speed, seconds)
    else:
        raise AttributeError("need to initialize robot")


def turn(direction, amount=0.8, seconds=None):
    if globvars.robot:
        return globvars.robot.turn(direction, amount, seconds)
    else:
        raise AttributeError("need to initialize robot")


def turnLeft(speed=1, seconds=None):
    if globvars.robot:
        return globvars.robot.turnLeft(speed, seconds)
    else:
        raise AttributeError("need to initialize robot")


def turnRight(speed=1, seconds=None):
    if globvars.robot:
        return globvars.robot.turnRight(speed, seconds)
    else:
        raise AttributeError("need to initialize robot")


def stop():
    if globvars.robot:
        return globvars.robot.stop()


def getPosition():
    """This returns the x and y coordinates of the scribbler 2"""
    if globvars.robot:
        return globvars.robot.getPosition()
    else:
        raise AttributeError("need to initialize robot")


def hereIs(x=0, y=0):
    if globvars.robot:
        return globvars.robot.setHereIs(x, y)
    else:
        raise AttributeError("need to initialize robot")


def getAngle():
    """This returns the current angle of the scribbler 2"""
    if globvars.robot:
        return globvars.robot.getAngle()
    else:
        raise AttributeError("need to initialize robot")


def setAngle(angle):
    if globvars.robot:
        return globvars.robot.setAngle(angle)
    else:
        raise AttributeError("need to initialize robot")


def beginPath():
    """Speed can be a value from 1 to 15"""
    if globvars.robot:
        return globvars.robot.setBeginPath()
    else:
        raise AttributeError("need to initialize robot")


def moveTo(x, y):
    if globvars.robot:
        return globvars.robot.setMove(x, y, "to")
    else:
        raise AttributeError("need to initialize robot")


def moveBy(x, y):
    if globvars.robot:
        return globvars.robot.setMove(x, y, "by")
    else:
        raise AttributeError("need to initialize robot")


def turnTo(angle, radsOrDegrees):
    if globvars.robot:
        return globvars.robot.setTurn(angle, "to", radsOrDegrees)
    else:
        raise AttributeError("need to initialize robot")


def turnBy(angle, radsOrDegrees):
    if globvars.robot:
        return globvars.robot.setTurn(angle, "by", radsOrDegrees)
    else:
        raise AttributeError("need to initialize robot")


def arcTo(x, y, radius):
    if globvars.robot:
        return globvars.robot.setArc(x, y, radius, "to")
    else:
        raise AttributeError("need to initialize robot")


def arcBy(x, y, radius):
    if globvars.robot:
        return globvars.robot.setArc(x, y, radius, "by")
    else:
        raise AttributeError("need to initialize robot")


def endPath():
    if globvars.robot:
        return globvars.robot.setEndPath()
    else:
        raise AttributeError("need to initialize robot")


def getMicEnvelope():
    """Returns a number representing the microphone envelope noise"""
    if globvars.robot:
        return globvars.robot.getMicEnvelope()
    else:
        raise AttributeError("need to initialize robot")


def getMotorStats():
    """Return the current motion status as a packed long and single additional byte showing if motors are ready for commands (1=ready, 0=busy):
 Left wheel and right wheel are signed, twos complement eight bit velocity values,
 Idler timer is the time in 1/10 second since the last idler edge,
 Idler spd is an unsigned six-bit velocity value, and
 Mov is non-zero iff one or more motors are turning.
 Left and right wheel velocities are instanteous encoder counts over a 1/10-second interval.
 Idler wheel wheel velocity is updated every 1/10 second and represents the idler encoder count during the last 1.6 seconds."""
    if globvars.robot:
        return globvars.robot.getMotorStats()
    else:
        raise AttributeError("need to initialize robot")


def getEncoders(zeroEncoders=False):
    """Gets the values for the left and right encoder wheels.  Negative value means they have moved
    backwards from the robots perspective.  Each turn of the encoder wheel is counted as and increment or
    decrement of 2 depending on which direction the wheels moved.
    if zeroEncoders is set to True then the encoders will be set to zero after reading the values"""
    if globvars.robot:
        return globvars.robot.getEncoders(zeroEncoders)
    else:
        raise AttributeError("need to initialize robot")


def openConnection():
    if globvars.robot:
        return globvars.robot.open()
    else:
        raise AttributeError("need to initialize robot")


def closeConnection():
    if globvars.robot:
        return globvars.robot.close()
    else:
        raise AttributeError("need to initialize robot")


def get(sensor="all", *pos):
    if globvars.robot:
        return globvars.robot.get(sensor, *pos)
    else:
        raise AttributeError("need to initialize robot")


def getVersion():
    if globvars.robot:
        return globvars.robot.get("version")
    else:
        raise AttributeError("need to initialize robot")


def getLight(*pos):
    if globvars.robot:
        return globvars.robot.get("light", *pos)
    else:
        raise AttributeError("need to initialize robot")


def getIR(*pos):
    if globvars.robot:
        return globvars.robot.get("ir", *pos)
    else:
        raise AttributeError("need to initialize robot")


def getDistance(*pos):
    if globvars.robot:
        return globvars.robot.getDistance(*pos)
    else:
        raise AttributeError("need to initialize robot")


def getLine(*pos):
    if globvars.robot:
        return globvars.robot.get("line", *pos)
    else:
        raise AttributeError("need to initialize robot")


def getStall():
    if globvars.robot:
        return globvars.robot.get("stall")
    else:
        raise AttributeError("need to initialize robot")


def getInfo(*item):
    if globvars.robot:
        retval = globvars.robot.getInfo(*item)
        retval["myro"] = __VERSION__
        return retval
    else:
        return {"myro": __VERSION__}


def getAll():
    if globvars.robot:
        return globvars.robot.get("all")
    else:
        raise AttributeError("need to initialize robot")


def getName():
    if globvars.robot:
        return globvars.robot.get("name")
    else:
        raise AttributeError("need to initialize robot")


def getPassword():
    if globvars.robot:
        return globvars.robot.get("password")
    else:
        raise AttributeError("need to initialize robot")


def getForwardness():
    if globvars.robot:
        return globvars.robot.get("forwardness")
    else:
        raise AttributeError("need to initialize robot")


def getStartSong():
    if globvars.robot:
        return globvars.robot.get("startsong")
    else:
        raise AttributeError("need to initialize robot")


def getVolume():
    if globvars.robot:
        return globvars.robot.get("volume")
    else:
        raise AttributeError("need to initialize robot")


def update():
    if globvars.robot:
        return globvars.robot.update()
    else:
        raise AttributeError("need to initialize robot")


def beep(duration=0.5, frequency1=None, frequency2=None):
    if type(duration) in [tuple, list]:
        frequency2 = frequency1
        frequency1 = duration
        duration = 0.5
    if frequency1 is None:
        frequency1 = random.randrange(200, 10000)
    if type(frequency1) in [tuple, list]:
        if frequency2 is None:
            frequency2 = [None for i in range(len(frequency1))]
        for (f1, f2) in zip(frequency1, frequency2):
            if globvars.robot:
                globvars.robot.beep(duration, f1, f2)
            else:
                computer.beep(duration, f1, f2)
    else:
        if globvars.robot:
            globvars.robot.beep(duration, frequency1, frequency2)
        else:
            computer.beep(duration, frequency1, frequency2)


def scaleDown(loopCount):
    beep(0.5, 9000 - 200 * loopCount)


def scaleUp(loopCount):
    beep(0.5, 200 + 200 * loopCount)


def set(item, position, value=None):
    if globvars.robot:
        return globvars.robot.set(item, position, value)
    else:
        raise AttributeError("need to initialize robot")


def setLED(position, value):
    if globvars.robot:
        return globvars.robot.set("led", position, value)
    else:
        raise AttributeError("need to initialize robot")


def setName(name):
    if globvars.robot:
        return globvars.robot.set("name", name)
    else:
        raise AttributeError("need to initialize robot")


def setPassword(password):
    if globvars.robot:
        return globvars.robot.set("password", password)
    else:
        raise AttributeError("need to initialize robot")


def setForwardness(value):
    if globvars.robot:
        return globvars.robot.set("forwardness", value)
    else:
        raise AttributeError("need to initialize robot")


def setVolume(value):
    if globvars.robot:
        return globvars.robot.set("volume", value)
    else:
        raise AttributeError("need to initialize robot")


def setS2Volume(value):
    """Level can be between 0-100 and represents the percent volume level of the speaker"""
    if globvars.robot:
        return globvars.robot.setS2Volume(value)
    else:
        raise AttributeError("need to initialize robot")


def setStartSong(songName):
    if globvars.robot:
        return globvars.robot.set("startsong", songName)
    else:
        raise AttributeError("need to initialize robot")


def motors(left, right):
    if globvars.robot:
        return globvars.robot.motors(left, right)
    else:
        raise AttributeError("need to initialize robot")


def restart():
    if globvars.robot:
        return globvars.robot.restart()
    else:
        raise AttributeError("need to initialize robot")


def calibrate():
    if globvars.robot:
        return Calibrate(globvars.robot)
    else:
        raise AttributeError("need to initialize robot")


def playSong(song, wholeNoteDuration=0.545):
    if globvars.robot:
        return globvars.robot.playSong(song, wholeNoteDuration)
    else:
        raise AttributeError("need to initialize robot")


def playNote(tup, wholeNoteDuration=0.545):
    if globvars.robot:
        return globvars.robot.playNote(tup, wholeNoteDuration)
    else:
        raise AttributeError("need to initialize robot")


# New dongle commands


def getBright(position=None):
    if globvars.robot:
        return globvars.robot.getBright(position)
    else:
        raise AttributeError("need to initialize robot")


def getBlob():
    if globvars.robot:
        return globvars.robot.getBlob()
    else:
        raise AttributeError("need to initialize robot")


def getObstacle(position=None):
    if globvars.robot:
        return globvars.robot.getObstacle(position)
    else:
        raise AttributeError("need to initialize robot")


def setIRPower(value):
    if globvars.robot:
        return globvars.robot.setIRPower(value)
    else:
        raise AttributeError("need to initialize robot")


def getBattery():
    if globvars.robot:
        return globvars.robot.getBattery()
    else:
        raise AttributeError("need to initialize robot")


def identifyRobot():
    if globvars.robot:
        return globvars.robot.identifyRobot()
    else:
        raise AttributeError("need to initialize robot")


def getIRMessage():
    if globvars.robot:
        return globvars.robot.getIRMessage()
    else:
        raise AttributeError("need to initialize robot")


def sendIRMessage(msg):
    if globvars.robot:
        return globvars.robot.sendIRMessage(msg)
    else:
        raise AttributeError("need to initialize robot")


def setCommunicateLeft(on=True):
    if globvars.robot:
        return globvars.robot.setCommunicateLeft(on)
    else:
        raise AttributeError("need to initialize robot")


def setCommunicateRight(on=True):
    if globvars.robot:
        return globvars.robot.setCommunicateLeft(on)
    else:
        raise AttributeError("need to initialize robot")


def setCommunicateCenter(on=True):
    if globvars.robot:
        return globvars.robot.setCommunicateCenter(on)
    else:
        raise AttributeError("need to initialize robot")


def setCommunicateAll(on=True):
    if globvars.robot:
        return globvars.robot.setCommunicateAll(on)
    else:
        raise AttributeError("need to initialize robot")


def configureBlob(
    y_low=0, y_high=255, u_low=0, u_high=255, v_low=0, v_high=255, smooth_thresh=4
):
    if globvars.robot:
        return globvars.robot.configureBlob(
            y_low, y_high, u_low, u_high, v_low, v_high, smooth_thresh
        )
    else:
        raise AttributeError("need to initialize robot")


def setWhiteBalance(value):
    if globvars.robot:
        return globvars.robot.setWhiteBalance(value)
    else:
        raise AttributeError("need to initialize robot")


def darkenCamera(value=0):
    if globvars.robot:
        return globvars.robot.darkenCamera(value)
    else:
        raise AttributeError("need to initialize robot")


def manualCamera(gain=0x00, brightness=0x80, exposure=0x41):
    if globvars.robot:
        return globvars.robot.manualCamera(gain, brightness, exposure)
    else:
        raise AttributeError("need to initialize robot")


def autoCamera(value=0):
    if globvars.robot:
        return globvars.robot.autoCamera()
    else:
        raise AttributeError("need to initialize robot")


def setLEDFront(value):
    """ Set the Light Emitting Diode on the robot's front. """
    if globvars.robot:
        return globvars.robot.setLEDFront(value)
    else:
        raise AttributeError("need to initialize robot")


def setLEDBack(value):
    """ Set the Light Emitting Diode on the robot's back. """
    if globvars.robot:
        return globvars.robot.setLEDBack(value)
    else:
        raise AttributeError("need to initialize robot")


def _ndim(n, *args, **kwargs):
    if not args:
        return [kwargs.get("value", 0)] * n
    A = []
    for i in range(n):
        A.append(_ndim(*args, **kwargs))
    return A


class Column(object):
    def __init__(self, picture, column):
        self.picture = picture
        self.column = column

    def __getitem__(self, row):
        return self.picture.getPixel(self.column, row)


class Array(object):
    def __init__(self, n=0, *args, **kwargs):
        if type(n) == Picture:
            self.data = n
        else:
            self.data = _ndim(n, *args, **kwargs)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, *args):
        if type(self.data) == Picture:
            return Column(self.data, args[0])
        else:
            current = self.data
            for i in args:
                n, _ = args[0], args[1:]
                current = current[n]
            return current


def makeArray(*args, **kwargs):
    """ Returns an array of the given dimensions. """
    return Array(*args, **kwargs)


def takePicture(mode=None):
    """ Takes a picture using the camera. Mode can be 'color', 'gray', or 'blob' """
    if globvars.robot:
        return globvars.robot.takePicture(mode)
    else:
        raise AttributeError("need to initialize robot")


def loadPicture(filename):
    """ Loads a picture from a filename. """
    picture = Picture()
    picture.load(filename)
    return picture


def copyPicture(picture):
    """ Takes a Picture object and returns a copy. """
    newPicture = Picture()
    newPicture.set(getWidth(picture), getHeight(picture), picture.image, mode="image")
    return newPicture


def makePicture(*args):
    """
    Takes zero or more args to make a picture.

    makePicture() - makes a 0x0 image
    makePicture(width, height)
    makePicture("filename")
    makePicture("http://image")
    makePicture(width, height, data)
    makePicture(width, height, data, "mode")
    """
    if len(args) == 0:
        retval = Picture()
    elif len(args) == 1:
        filename = args[0]
        retval = Picture()
        retval.load(filename)
    elif len(args) == 2:
        x = args[0]
        y = args[1]
        retval = Picture()
        retval.set(x, y)
    elif len(args) == 3:
        x = args[0]
        y = args[1]
        if type(args[2]) in [Color, Pixel]:
            retval = Picture()
            retval.set(x, y, value=args[2].getRGB())
        elif type(args[2]) == int:
            retval = Picture()
            retval.set(x, y, value=args[2])
        elif type(args[2]) in [list, tuple]:  # Undocumented
            array = args[2]
            retval = Picture()
            retval.set(x, y, value=args[2])
        else:
            raise AttributeError(
                "unknown type: %s is '%s'; " + "should be Color, Pixel, int grayscale",
                args[2],
                type(args[2]),
            )
    elif len(args) == 4:
        x = args[0]
        y = args[1]
        array = args[2]
        mode = args[3]
        retval = Picture()
        retval.set(x, y, array, mode)
    return retval


def _mouseCallback(point, name="default", scale=1):
    window = globvars.windows[name]
    picture = globvars.pictures[name]
    if (
        0 <= point.x < getWidth(picture) * scale
        and 0 <= point.y < getHeight(picture) * scale
    ):
        pixel = picture.getPixel(point.x, point.y)
        window.lastX, window.lastY = point.x, point.y
        rgba = pixel.getRGBA()
        window.setStatusDirect(
            "(%d, %d): (%d,%d,%d,a=%d)"
            % (point.x / scale, point.y / scale, rgba[0], rgba[1], rgba[2], rgba[3])
        )


def _mouseCallbackRelease(point, name="default", scale=1):
    window = globvars.windows[name]
    picture = globvars.pictures[name]
    if (
        0 <= point.x < getWidth(picture) * scale
        and 0 <= point.y < getHeight(picture) * scale
    ):
        if abs(window.lastX - point.x) < 3 or abs(window.lastY - point.y) < 3:
            return
        if globvars.robot is not None:
            yMin, yMax, uMin, uMax, vMin, vMax = globvars.robot.set_blob_yuv(
                picture,
                window.lastX / scale,
                window.lastY / scale,
                point.x / scale,
                point.y / scale,
            )
            window.setStatusDirect(
                "Set configureBlob(%d,%d,%d,%d,%d,%d)"
                % (yMin, yMax, uMin, uMax, vMin, vMax)
            )


def writePictureTo(picture, filename):
    return picture.image.save(filename)


def savePicture(picture, filename):
    if type(picture) == type([]):

        # open output file
        fp = open(filename, "wb")
        previous = None
        for im in picture:
            if type(im) == type(""):  # filename
                im = Image.open(im)
                im.load()
                im = im.convert("P")  # in case jpeg, etc
            else:
                im = im.image.convert("P")
            if not previous:
                for s in getheader(im) + getdata(im):
                    fp.write(s)
            else:
                delta = ImageChops.subtract_modulo(im, previous)
                bbox = delta.getbbox()
                if bbox:
                    for s in getdata(im.crop(bbox), offset=bbox[:2]):
                        fp.write(s)
            previous = im.copy()
        fp.write(";")
        fp.close()
    else:
        return picture.image.save(filename)


def show(picture, name="default"):
    if globvars.windows.get(name, None) is None:
        globvars.windows[name] = GraphWin("Myro: %s" % name)
    try:
        globvars.windows[name].delete("image")
    except Exception:
        globvars.windows[name] = GraphWin("Myro: %s" % name)
    if picture.displayScale != 1:
        picture = Picture(picture)
        picture.scale(picture.displayScale)
    globvars.pictures[name] = picture
    globvars.windows[name]["width"] = picture.width
    globvars.windows[name]["height"] = picture.height
    globvars.windows[name].setMouseHandler(
        lambda point: _mouseCallback(point, name, picture.displayScale)
    )
    globvars.windows[name].setMouseReleaseHandler(
        lambda point: _mouseCallbackRelease(point, name, picture.displayScale)
    )
    globvars.images[name] = Image(
        Point(picture.width / 2, picture.height / 2), globvars.pixmaps[name]
    )
    globvars.images[name].draw(globvars.windows[name])


def repaint(picture=None, name="default"):
    if picture is None:
        picture = globvars.pictures[name]
    elif picture.displayScale != 1:
        picture = Picture(picture)
        picture.scale(picture.displayScale)
        globvars.pictures[name] = picture
    # get a new photoimage from data
    photoimage = ImageTk.PhotoImage(picture.image)
    # replace the pixmap data:
    globvars.images[name].img = photoimage
    # refresh the canvas:
    globvars.images[name].refresh(globvars.windows[name])


def getWindow(name="default"):
    return globvars.windows[name]


def draw(obj, win=None):
    if win is None:
        win = globvars.windows["default"]
    obj.draw(win)


def undraw(obj):
    obj.undraw()


def getWidth(picture):
    return picture.width


def getHeight(picture):
    return picture.height


def getPixel(picture, x, y):
    return picture.getPixel(x, y)


def getPixels(picture):
    return picture.getPixels()


def setPixel(picture, x, y, color):
    return picture.setColor(x, y, color)


def getGray(picture, x, y):
    return sum((picture.getPixel(x, y)).getRGB()) / 3


def setGray(picture, x, y, gray):
    return getPixel(picture, x, y).setRGB([gray, gray, gray])


# Pixels and Colors


def getX(pixel):
    return pixel.x


def getY(pixel):
    return pixel.y


def getRed(pixel):
    return pixel.getRGB()[0]


def getGreen(pixel):
    return pixel.getRGB()[1]


def getBlue(pixel):
    return pixel.getRGB()[2]


def getColor(pixel):
    return pixel.getColor()


def getGray(pixel):
    return sum(pixel.getRGB()) / 3


def setRGB(pixel_or_color, rgb):
    return pixel_or_color.setRGB(rgb)


def setRGBA(pixel_or_color, rgba):
    return pixel_or_color.setRGBA(rgba)


def getRGB(pixel_or_color):
    return pixel_or_color.getRGB()


def getRGBA(pixel_or_color):
    return pixel_or_color.getRGBA()


def setRed(pixel, value):
    return pixel.setColor(Color(value, pixel.getRGB()[1], pixel.getRGB()[2]))


def setGreen(pixel, value):
    return pixel.setColor(Color(pixel.getRGB()[0], value, pixel.getRGB()[2]))


def setBlue(pixel, value):
    return pixel.setColor(Color(pixel.getRGB()[0], pixel.getRGB()[1], value))


def setGray(pixel, value):
    return pixel.setColor(Color(value, value, value))


def setAlpha(pixel, value):
    return pixel.setAlpha(value)


def getAlpha(pixel):
    return pixel.getAlpha()


def setColor(pixel, color):
    return pixel.setColor(color)


def makeColor(red, green, blue, alpha=255):
    return Color(red, green, blue, alpha)


def makeDarker(color):
    return color.makeDarker()


def makeLighter(color):
    return color.makeLighter()


def odd(n):
    return (n % 2) == 1


def even(n):
    return (n % 2) == 0


def wall(threshold=4500):
    return getObstacle(1) > threshold


def loop(*functions):
    """
    Calls each of the given functions sequentially, N times.
    Example:

    >>> loop(f1, f2, 10)
    will call f1() then f2(), 10 times.
    """
    assert len(functions) > 1, "loop: takes 1 (or more) functions and an integer"
    assert type(functions[-1]) == int, "loop: last parameter must be an integer"
    count = functions[-1]
    for i in range(count):
        for function in functions[:-1]:
            print("   loop #%d: running %s()... " % (i + 1, function.__name__), end=" ")
            try:
                retval = function()
            except TypeError:
                retval = function(i + 1)
            if retval:
                print(" => %s" % retval)
            else:
                print("")
    stop()
    return "ok"


def doTogether(*functions):
    """
    Runs each of the given functions at the same time.
    Example:

    >>> doTogether(f1, f2, f3)
    will call f1() f2() and f3() together.
    """
    thread_results = [None] * len(functions)

    def makeThread(function, position):
        def newfunction():
            result = function()
            thread_results[position] = result
            return result

        thread = threading.Thread()
        thread.run = newfunction
        return thread

    assert len(functions) >= 2, "doTogether: takes 2 (or more) functions"
    thread_list = []
    # first make the threads:
    for i in range(len(functions)):
        thread_list.append(makeThread(functions[i], i))
    # now, start them:
    for thread in thread_list:
        thread.start()
    # wait for them to finish:
    for thread in thread_list:
        thread.join()
    if thread_results == [None] * len(functions):
        print("ok")
    else:
        return thread_results


def beepScale(duration, start, stop, factor=2):
    """
    Calls computer.beep(duration, Hz) repeatedly, where Hz is between
    the given start and stop frequencies, incrementing by the given
    factor.
    """
    hz = start
    while hz <= stop:
        computer.beep(duration, hz)
        hz *= factor


def getFilenames(pattern):
    """ Get a list of filenames via a pattern, like "z??.jpg"."""
    filenames = glob.glob(pattern)
    filenames.sort()  # get in order, back to front
    return filenames


def _startSimulator():
    globalspath, filename = os.path.split(globvars.__file__)
    globvars.myropath, directory = os.path.split(globalspath)
    simulator_file = os.path.join(globvars.myropath, "simulator.py")
    path = globvars.myropath
    if os.name in ["nt", "dos", "os2"]:
        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] = (
                path + ";" + os.getcwd() + ";" + os.environ["PYTHONPATH"]
            )
        else:
            os.environ["PYTHONPATH"] = path
        os.system("""start c:\Python24\python.exe "%s" """ % simulator_file)
    elif os.name in ["posix"]:
        if "PYTHONPATH" in os.environ:
            os.environ["PYTHONPATH"] = (
                path + ":" + os.getcwd() + ":" + os.environ["PYTHONPATH"]
            )
        else:
            os.environ["PYTHONPATH"] = path
        os.system("""/usr/bin/env python "%s" &""" % simulator_file)
    else:
        raise AttributeError(
            "your operating system (%s) is not currently supported" % os.name
        )


# --------------------------------------------------------
# Error handler:
# --------------------------------------------------------
def _myroExceptionHandler(etype, value, tb):
    # make a window
    # win = HelpWindow()
    lines = traceback.format_exception(etype, value, tb)
    print(
        "Myro is stopping: -------------------------------------------", file=sys.stderr
    )
    for line in lines:
        print(line.rstrip(), file=sys.stderr)


sys.excepthook = _myroExceptionHandler


_functions = (
    "timer",
    "time Remaining",
    "send Picture",
    "register",
    "set Password",
    "set Forwardness",
    "wait",
    "current Time",
    "pick One",
    "flip Coin",
    "random Number",
    "get Gamepad",
    "get Gamepad Now",
    "ask",
    "request Stop",
    "initialize",
    "simulator",
    "translate",
    "rotate",
    "move",
    "forward",
    "backward",
    "turn",
    "turn Left",
    "turn Right",
    "stop",
    "open Connection",
    "close Connection",
    "get",
    "get Version",
    "get Light",
    "get I R",
    "get Line",
    "get Stall",
    "get Info",
    "get All",
    "get Name",
    "get Start Song",
    "get Volume",
    "update",
    "beep",
    "set",
    "set L E D",
    "set Name",
    "set Volume",
    "set Start Song",
    "motors",
    "restart",
    "joy Stick",
    "calibrate",
    "play Song",
    "play Note",
    "get Bright",
    "get Obstacle",
    "set I R Power",
    "get Battery",
    "set White Balance",
    "set L E D Front",
    "set L E D Back",
    "make Array",
    "take Picture",
    "load Picture",
    "copy Picture",
    "make Picture",
    "write Picture To",
    "save Picture",
    "show",
    "repaint",
    "get Width",
    "get Height",
    "get Pixel",
    "get Pixels",
    "set Pixel",
    "get X",
    "get Y",
    "get Red",
    "get Green",
    "get Blue",
    "get Color",
    "set Red",
    "set Green",
    "set Blue",
    "set Color",
    "make Color",
    "make Darker",
    "make Lighter",
)

globvars.makeEnvironment(locals(), _functions)
