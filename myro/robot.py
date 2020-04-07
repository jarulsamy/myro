import threading
import time
import pickle
from . import graphics

class BackgroundThread(threading.Thread):
    """
    A thread class for running things in the background.
    """

    def __init__(self, function, pause=0.01):
        """
        Constructor, setting initial variables
        """
        self.function = function
        self._stopevent = threading.Event()
        self._sleepperiod = pause
        threading.Thread.__init__(self, name="MyroThread")

    def run(self):
        """
        overload of threading.thread.run()
        main control loop
        """
        while not self._stopevent.isSet():
            self.function()
            # self._stopevent.wait(self._sleepperiod)

    def join(self, timeout=None):
        """
        Stop the thread
        """
        self._stopevent.set()
        threading.Thread.join(self, timeout)


class Robot(object):
    _app = None
    _joy = None
    _cal = None

    def __init__(self):
        """
        Base robot class.
        """
        self.lock = threading.Lock()

    def initializeRemoteControl(self, password):
        self.chat = Chat(self.getName(), password)

    def processRemoteControlLoop(self, threaded=1):
        if threaded:
            self.thread = BackgroundThread(self.processRemoteControl, 1)  # seconds
            self.thread.start()
        else:
            while 1:
                self.processRemoteControl()

    def processRemoteControl(self):
        messages = self.chat.receive()
        # print "process", messages
        for _from, message in messages:
            if message.startswith("robot."):
                # For user IM messages
                # print ">>> self." + message[6:]
                retval = eval("self." + message[6:])
                name, domain = _from.split("@")
                # print "sending:", pickle.dumps(retval)
                self.chat.send(name.lower(), pickle.dumps(retval))

    def translate(self, amount):
        raise AttributeError("this method needs to be written")

    def rotate(self, amount):
        raise AttributeError("this method needs to be written")

    def move(self, translate, rotate):
        raise AttributeError("this method needs to be written")

    def beep(self, duration, frequency1, frequency2=None):

        print("beep!")
        return graphics._tkCall(
            graphics._beep, duration, frequency1, frequency2
        )

    def getLastSensors(self):
        """ Should not get the current, but the last. This is default behavior. """
        return self.get("all")

    def update(self):
        """ Update the robot """
        raise AttributeError("this method needs to be written")

    # The rest of these methods are just rearrangements of the above

    def getVersion(self):
        """ Returns robot version information. """
        return self.get("version")

    def getLight(self, *position):
        """ Return the light readings. """
        return self.get("light", *position)

    def getIR(self, *position):
        """ Returns the infrared readings. """
        return self.get("ir", *position)

    def getDistance(self, *position):
        """ Returns the S2 Distance readings. """
        return self.getDistance(*position)

    def getLine(self, *position):
        """ Returns the line sensor readings. """
        return self.get("line", *position)

    def getStall(self):
        """ Returns the stall reading. """
        return self.get("stall")

    def getInfo(self, *item):
        """ Returns the info. """
        retval = self.get("info", *item)
        retval["myro"] = __VERSION__
        return retval

    def getName(self):
        """ Returns the robot's name. """
        return self.get("name")

    def getPassword(self):
        """ Returns the robot's password. """
        return self.get("password")

    def getForwardness(self):
        """ Returns the robot's directionality. """
        return self.get("forwardness")

    def getAll(self):
        return self.get("all")

    def setLED(self, position, value):
        return self.set("led", position, value)

    def setName(self, name):
        return self.set("name", name)

    def setPassword(self, password):
        return self.set("password", password)

    def setForwardness(self, value):
        return self.set("forwardness", value)

    def setVolume(self, value):
        return self.set("volume", value)

    def setStartSong(self, songName):
        return self.set("startsong", songName)

    def forward(self, speed=1, interval=None):
        self.move(speed, 0)
        if interval is not None:
            time.sleep(interval)
            self.stop()

    def backward(self, speed=1, interval=None):
        self.move(-speed, 0)
        if interval is not None:
            time.sleep(interval)
            self.stop()

    def turn(self, direction, value=0.8, interval=None):
        if type(direction) in [float, int]:
            retval = self.move(0, direction)
        else:
            direction = direction.lower()
            if direction == "left":
                retval = self.move(0, value)
            elif direction == "right":
                retval = self.move(0, -value)
            elif direction in ["straight", "center"]:
                retval = self.move(0, 0)  # aka, stop!
            else:
                retval = "error"
        if interval is not None:
            time.sleep(interval)
            self.stop()
        return retval

    def turnLeft(self, speed=1, interval=None):
        retval = self.move(0, speed)
        if interval is not None:
            time.sleep(interval)
            self.stop()
        return retval

    def turnRight(self, speed=1, interval=None):
        retval = self.move(0, -speed)
        if interval is not None:
            time.sleep(interval)
            self.stop()
        return retval

    def stop(self):
        return self.move(0, 0)

    def motors(self, left, right):
        trans = (right + left) / 2.0
        rotate = (right - left) / 2.0
        return self.move(trans, rotate)

    def restart(self):
        pass

    def close(self):
        pass

    def open(self):
        pass

    def playSong(self, song, wholeNoteDuration=0.545):
        """ Plays a song [(freq, [freq2,] duration),...] """
        # 1 whole note should be .545 seconds for normal
        for tuple in song:
            self.playNote(tuple, wholeNoteDuration)

    def playNote(self, tuple, wholeNoteDuration=0.545):
        if len(tuple) == 2:
            (freq, dur) = tuple
            self.beep(dur * wholeNoteDuration, freq)
        elif len(tuple) == 3:
            (freq1, freq2, dur) = tuple
            self.beep(dur * wholeNoteDuration, freq1, freq2)
