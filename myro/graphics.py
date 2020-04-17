# graphics.py
"""
Simple object oriented graphics library

Original code by John Zelle
Updates       by Joshua Arulsamy

The library is designed to make it very easy for novice programmers to
experiment with computer graphics in an object oriented fashion. It is
written by John Zelle for use with the book "Python Programming: An
Introduction to Computer Science" (Franklin, Beedle & Associates).

LICENSE: This is open-source software released under the terms of the
GPL (http://www.gnu.org/licenses/gpl.html).

PLATFORMS: The package is a wrapper around Tkinter and should run on
any platform where Tkinter is available.

OVERVIEW: There are two kinds of objects in the library. The GraphWin
class implements a window where drawing can be done and various
GraphicsObjects are provided that can be drawn into a GraphWin. As a
simple example, here is a complete program to draw a circle of radius
10 centered in a 100x100 window:

--------------------------------------------------------------------
from graphics import *

def main():
    win = GraphWin("My Circle", 100, 100)
    c = Circle(Point(50,50), 10)
    c.draw(win)
    win.getMouse() // Pause to view result

main()
--------------------------------------------------------------------
GraphWin objects support coordinate transformation through the
setCoords method and pointer-based input through getMouse.

The library provides the following graphical objects:
    Point
    Line
    Circle
    Oval
    Rectangle
    Polygon
    Text
    Entry (for text-based input)
    Image

Various attributes of graphical objects can be set such as
outline-color, fill-color and line-width. Graphical objects also
support moving and hiding for animation effects.

"""
import _thread
import array
import atexit
import math
import sys
import time
import tkinter.colorchooser
import tkinter.dialog
import tkinter.filedialog
from copy import copy
from queue import Queue

import PIL.Image as PyImage

import myro.globvars
from . import globvars
from myro.widgets import AlertDialog


# TODO: Fix tkinter for Py > 3
tk = tkinter

# Module Exceptions


class GraphicsError(Exception):
    """
    Generic error class for graphics module exceptions.
    """

    def __init__(self, args=None):
        self.args = args


OBJ_ALREADY_DRAWN = "Object currently drawn"
UNSUPPORTED_METHOD = "Object doesn't support operation"
BAD_OPTION = "Illegal option value"
DEAD_THREAD = "Graphics thread quit unexpectedly"

# Support to run Tk in a separate thread
_tk_request = Queue(0)
_tk_result = Queue(1)
_POLL_INTERVAL = 10

_root = None
_thread_running = True
_exception_info = None


def _tk_thread():
    global _root

    try:
        _root = tk.Tk()
        myro.globvars.gui = _root
        _root.withdraw()
        _root.after(_POLL_INTERVAL, _tk_pump)
        _root.mainloop()
    except Exception as e:
        _root = None
        print("ERROR: graphics did not start", file=sys.stderr)
        print(e)


def _tk_pump():
    global _thread_running
    global _root
    global _tk_request
    global _tk_result

    # if myro.globvars.pygame:
    # myro.globvars.pygame.event.pump()
    while not _tk_request.empty():
        command, returns_value = _tk_request.get()
        try:
            result = command()
            if returns_value:
                _tk_result.put(result)
        except Exception as e:
            _thread_running = False
            if returns_value:
                _tk_result.put(None)  # release client
            raise e  # re-raise the exception -- kills the thread
    if _thread_running:
        try:
            _root.after(_POLL_INTERVAL, _tk_pump)
        except Exception:
            print("Graphics: Can't pump anymore")


if myro.globvars.runtkthread:

    def _tkCall(f, *args, **kw):
        # execute synchronous call to f in the Tk thread
        # this function should be used when a return value from
        #   f is required or when synchronizing the threads.
        # call to _tkCall in Tk thread == DEADLOCK !
        if not _thread_running:
            raise GraphicsError(DEAD_THREAD)

        def func():
            return f(*args, **kw)

        _tk_request.put((func, True), True)
        result = _tk_result.get(True)
        return result

    def _tkExec(f, *args, **kw):
        # schedule f to execute in the Tk thread. This function does
        #   not wait for f to actually be executed.
        # global _exception_info
        # _exception_info = None
        if not _thread_running:
            raise GraphicsError(DEAD_THREAD)

        def func():
            return f(*args, **kw)

        _tk_request.put((func, False), True)
        # if _exception_info is not None:
        #    raise GraphicsError, "Invalid Operation: %s" % str(_exception_info)


else:

    def _tkCall(f, *args, **kw):
        return f(*args, **kw)

    def _tkExec(f, *args, **kw):
        return f(*args, **kw)


def _tkShutdown():
    # shutdown the tk thread
    global _thread_running
    # _tkExec(sys.exit)
    _thread_running = False
    time.sleep(0.5)  # give tk thread time to quit


# Fire up the separate Tk thread
if myro.globvars.runtkthread:
    _thread.start_new_thread(_tk_thread, ())
else:
    _root = tk.Tk()
    myro.globvars.gui = _root
    _root.withdraw()


def updateGraphics():
    """
    Update the Tk graphics when not in IDLE, and there is no
    graphics thread running to take care of updating.
    """
    _root.update_idletasks()


def moveToTop(window):
    if "darwin" not in sys.platform and "win" in sys.platform:
        window.wm_attributes("-topmost", 1)

    # window.lift(aboveThis=_root)
    window.lift()
    window.focus()


def distance(tuple1, tuple2):
    return math.sqrt(sum([(t1 - t2) ** 2 for (t1, t2) in zip(tuple1, tuple2)]))


# Graphics classes start here


class AskDialog(AlertDialog):
    def __init__(self, title, qdict):
        _tkCall(self.__init_help, title, qdict)

    def run(self):
        return _tkCall(self.Show)

    def stop(self):
        return _tkCall(self.DialogCleanup)

    def __init_help(self, title, qdict):
        AlertDialog.__init__(self, _root, title)
        self.title = title
        self.qdict = qdict
        self.textbox = {}
        moveToTop(self.top)
        self.top.bind("<Return>", lambda event: self.OkPressed())

    def SetupDialog(self):
        AlertDialog.SetupDialog(self)
        self.bitmap["bitmap"] = "question"
        first = 1
        qlist = list(self.qdict.keys())
        qlist.sort()
        for text in qlist:
            default = self.qdict[text]
            if "password" in text.lower():
                self.CreateTextBox(text, width=30, default=default, show="*")
            else:
                self.CreateTextBox(text, width=30, default=default)
            if first:
                self.textbox[text].focus_set()
                first = 0
        self.CreateButton("Ok", self.OkPressed)
        self.CreateButton("Cancel", self.CancelPressed)


def askQuestion(
    question,
    answers=["Yes", "No"],
    title="Myro Question",
    default=0,
    bitmap=tkinter.dialog.DIALOG_ICON,
):
    """
    Displays a question and returns answer.
    """
    d = _tkCall(
        tkinter.dialog.Dialog,
        myro.globvars.gui,
        title=title,
        default=default,
        bitmap=bitmap,
        text=question,
        strings=answers,
    )
    return answers[int(d.num)]


# This is a HACK.
_askQuestion = askQuestion


def pickAFile():
    """
    Returns a filename
    """
    path = _tkCall(tkinter.filedialog.askopenfilename)
    return path


def pickAColor():
    """
    Returns an RGB color tuple
    """
    color = _tkCall(tkinter.colorchooser.askcolor)
    if color[0] is not None:
        return Color(color[0][0], color[0][1], color[0][2])


def pickAFolder():
    """ Returns a folder path/name """
    folder = _tkCall(tkinter.filedialog.askdirectory)
    if folder == "":
        folder = myro.globvars.mediaFolder
    return folder


class GraphWin(tk.Canvas):

    """
    A GraphWin is a toplevel window for displaying graphics.
    """

    def __init__(self, title="Graphics Window", width=200, height=200, autoflush=False):
        _tkCall(self.__init_help, title, width, height, autoflush)

    def __init_help(self, title, width, height, autoflush):
        master = tk.Toplevel(_root)
        master.protocol("WM_DELETE_WINDOW", self.__close_help)
        tk.Canvas.__init__(self, master, width=width, height=height)
        self.status = tk.Label(self.master, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X, side="bottom")

        moveToTop(self.master)
        self.master.title(title)
        self.pack()
        master.resizable(0, 0)
        self.foreground = "black"
        self.items = []
        self.mouseX, self.mouseY = (None, None)
        self.lastX, self.lastY = (0, 0)
        self.bind("<Button-1>", self._onClick)
        self.bind("<ButtonRelease-1>", self._onRelease)
        self.height = height
        self.width = width
        self.autoflush = autoflush
        self._mouseCallback = None
        self._mouseCallbackRelease = None
        self.trans = None
        self.closed = False
        # at least flash:
        self.master.after(50, self.master.deiconify)
        self.master.after(70, self.master.tkraise)
        if autoflush:
            _root.update()

    def setStatusDirect(self, format=""):
        self.status.config(text=format)

    def setStatus(self, format=""):
        self._setStatus(format)

    def _setStatus(self, format=""):
        _tkCall(self.status.config, text=format)

    def __checkOpen(self):
        if self.closed:
            raise GraphicsError("window is closed")

    def setBackground(self, color):
        """
        Set background color of the window
        """
        self.__checkOpen()
        _tkExec(self.config, bg=color)
        # self.config(bg=color)

    def setCoords(self, x1, y1, x2, y2):
        """
        Set coordinates of window to run from (x1,y1) in the
        lower-left corner to (x2,y2) in the upper-right corner.
        """
        self.trans = Transform(self.width, self.height, x1, y1, x2, y2)

    def close(self):
        if self.closed:
            return
        _tkCall(self.__close_help)

    def __close_help(self):
        """
        Close the window
        """
        self.closed = True
        self.master.destroy()
        _root.update()

    def isClosed(self):
        return self.closed

    def __autoflush(self):
        if self.autoflush:
            _tkCall(_root.update)

    def plot(self, x, y, color="black"):
        """
        Set pixel (x,y) to the given color
        """
        self.__checkOpen()
        xs, ys = self.toScreen(x, y)
        # self.create_line(xs,ys,xs+1,ys, fill=color)
        _tkExec(self.create_line, xs, ys, xs + 1, ys, fill=color, tag="line")
        self.__autoflush()

    def plotPixel(self, x, y, color="black"):
        """
        Set pixel raw (independent of window coordinates) pixel
        (x,y) to color
        """
        self.__checkOpen()
        # self.create_line(x,y,x+1,y, fill=color)
        _tkExec(self.create_line, x, y, x + 1, y, fill=color, tag="line")
        self.__autoflush()

    def flush(self):
        """
        Update drawing to the window
        """
        # self.update_idletasks()
        self.__checkOpen()
        _tkCall(self.update_idletasks)

    def redraw(self):
        _tkCall(self.update)

    def getMouse(self):
        """
        Wait for mouse click and return Point object representing
        the click
        """
        self.mouseX = None
        self.mouseY = None
        while self.mouseX is None or self.mouseY is None:
            # self.update()
            _tkCall(self.update)
            if self.isClosed():
                raise GraphicsError("getMouse in closed window")
            time.sleep(0.1)  # give up thread
        x, y = self.toWorld(self.mouseX, self.mouseY)
        self.mouseX = None
        self.mouseY = None
        return Point(x, y)

    def checkMouse(self):
        """
        Return mouse click last mouse click or None if mouse has
        not been clicked since last call
        """
        if self.isClosed():
            raise GraphicsError("checkMouse in closed window")
        _tkCall(self.update)
        if self.mouseX is not None and self.mouseY is not None:
            x, y = self.toWorld(self.mouseX, self.mouseY)
            self.mouseX = None
            self.mouseY = None
            return Point(x, y)
        else:
            return None

    def getHeight(self):
        """
        Return the height of the window
        """
        return self.height

    def getWidth(self):
        """
        Return the width of the window
        """
        return self.width

    def toScreen(self, x, y):
        trans = self.trans
        if trans:
            return self.trans.screen(x, y)
        else:
            return x, y

    def toWorld(self, x, y):
        trans = self.trans
        if trans:
            return self.trans.world(x, y)
        else:
            return x, y

    def setMouseHandler(self, func):
        self._mouseCallback = func

    def setTimer(self, msec, func, *args):
        _tkCall(self.after, msec, func, *args)

    def setMouseReleaseHandler(self, func):
        self._mouseCallbackRelease = func

    def _onClick(self, e):
        self.mouseX = e.x
        self.mouseY = e.y
        if self._mouseCallback:
            self._mouseCallback(Point(e.x, e.y))

    def _onRelease(self, e):
        self.mouseX = e.x
        self.mouseY = e.y
        if self._mouseCallbackRelease:
            self._mouseCallbackRelease(Point(e.x, e.y))


class Transform:

    """
    Internal class for 2-D coordinate transformations
    """

    def __init__(self, w, h, xlow, ylow, xhigh, yhigh):
        # w, h are width and height of window
        # (xlow,ylow) coordinates of lower-left [raw (0,h-1)]
        # (xhigh,yhigh) coordinates of upper-right [raw (w-1,0)]
        xspan = xhigh - xlow
        yspan = yhigh - ylow
        self.xbase = xlow
        self.ybase = yhigh
        self.xscale = xspan / float(w - 1)
        self.yscale = yspan / float(h - 1)

    def screen(self, x, y):
        # Returns x,y in screen (actually window) coordinates
        xs = (x - self.xbase) / self.xscale
        ys = (self.ybase - y) / self.yscale
        return int(xs + 0.5), int(ys + 0.5)

    def world(self, xs, ys):
        # Returns xs,ys in world coordinates
        x = xs * self.xscale + self.xbase
        y = self.ybase - ys * self.yscale
        return x, y


# Default values for various item configuration options. Only a subset of
#   keys may be present in the configuration dictionary for a given item
DEFAULT_CONFIG = {
    "fill": "",
    "outline": "black",
    "width": "1",
    "arrow": "none",
    "text": "",
    "justify": "center",
    "font": ("helvetica", 12, "normal"),
}


class GraphicsObject:

    """
    Generic base class for all of the drawable objects
    """

    # A subclass of GraphicsObject should override _draw and
    #   and _move methods.

    def __init__(self, options):
        # options is a list of strings indicating which options are
        # legal for this object.

        # When an object is drawn, canvas is set to the GraphWin(canvas)
        #    object where it is drawn and id is the TK identifier of the
        #    drawn shape.
        self.canvas = None
        self.id = None

        # config is the dictionary of configuration options for the widget.
        config = {}
        for option in options:
            config[option] = DEFAULT_CONFIG[option]
        self.config = config

    def setFill(self, color):
        """
        Set interior color to color
        """
        self._reconfig("fill", color)

    def setOutline(self, color):
        """
        Set outline color to color
        """
        self._reconfig("outline", color)

    def setWidth(self, width):
        """
        Set line weight to width
        """
        self._reconfig("width", width)

    def draw(self, graphwin):
        """
        Draw the object in graphwin, which should be a GraphWin
        object.  A GraphicsObject may only be drawn into one
        window. Raises an error if attempt made to draw an object that
        is already visible.
        """

        if self.canvas and not self.canvas.isClosed():
            raise GraphicsError(OBJ_ALREADY_DRAWN)
        if graphwin.isClosed():
            raise GraphicsError("Can't draw to closed window")
        self.canvas = graphwin
        # self.id = self._draw(graphwin, self.config)
        self.id = _tkCall(self._draw, graphwin, self.config)
        if graphwin.autoflush:
            # _root.update()
            _tkCall(_root.update)

    def undraw(self):
        """
        Undraw the object (i.e. hide it). Returns silently if the
        object is not currently drawn.
        """

        if not self.canvas:
            return
        if not self.canvas.isClosed():
            # self.canvas.delete(self.id)
            _tkExec(self.canvas.delete, self.id)
            if self.canvas.autoflush:
                # _root.update()
                _tkCall(_root.update)
                pass
        self.canvas = None
        self.id = None

    def move(self, dx, dy):
        """
        move object dx units in x direction and dy units in y
        direction
        """

        self._move(dx, dy)
        canvas = self.canvas
        if canvas and not canvas.isClosed():
            trans = canvas.trans
            if trans:
                x = dx / trans.xscale
                y = -dy / trans.yscale
            else:
                x = dx
                y = dy
            # self.canvas.move(self.id, x, y)
            _tkExec(self.canvas.move, self.id, x, y)
            if canvas.autoflush:
                # _root.update()
                _tkCall(_root.update)

    def _reconfig(self, option, setting):
        # Internal method for changing configuration of the object
        # Raises an error if the option does not exist in the config
        #    dictionary for this object
        if option not in self.config:
            raise GraphicsError(UNSUPPORTED_METHOD)
        options = self.config
        options[option] = setting
        if self.canvas and not self.canvas.isClosed():
            # self.canvas.itemconfig(self.id, options)
            _tkExec(self.canvas.itemconfig, self.id, options)
            if self.canvas.autoflush:
                # _root.update()
                _tkCall(_root.update)

    def _draw(self, canvas, options):
        """
        draws appropriate figure on canvas with options provided
        Returns Tk id of item drawn
        """
        pass  # must override in subclass

    def _move(self, dx, dy):
        """
        updates internal state of object to move it dx,dy units
        """
        pass  # must override in subclass


class Point(GraphicsObject):
    def __init__(self, x, y):
        GraphicsObject.__init__(self, ["outline", "fill"])
        self.setFill = self.setOutline
        self.x = x
        self.y = y

    def _draw(self, canvas, options):
        x, y = canvas.toScreen(self.x, self.y)
        return canvas.create_rectangle(x, y, x + 1, y + 1, options, tag="rect")

    def _move(self, dx, dy):
        self.x = self.x + dx
        self.y = self.y + dy

    def clone(self):
        other = Point(self.x, self.y)
        other.config = self.config.copy()
        return other

    def getX(self):
        return self.x

    def getY(self):
        return self.y

    def getP1(self):
        return Point(self.x, self.y)

    def getP2(self):
        return Point(self.x, self.y)

    def getCenter(self):
        return Point(self.x, self.y)


class _BBox(GraphicsObject):
    # Internal base class for objects represented by bounding box
    # (opposite corners) Line segment is a degenerate case.

    def __init__(self, p1, p2, options=["outline", "width", "fill"]):
        GraphicsObject.__init__(self, options)
        self.p1 = p1.clone()
        self.p2 = p2.clone()

    def _move(self, dx, dy):
        self.p1.x = self.p1.x + dx
        self.p1.y = self.p1.y + dy
        self.p2.x = self.p2.x + dx
        self.p2.y = self.p2.y + dy

    def getP1(self):
        return self.p1.clone()

    def getP2(self):
        return self.p2.clone()

    def getCenter(self):
        p1 = self.p1
        p2 = self.p2
        return Point((p1.x + p2.x) / 2.0, (p1.y + p2.y) / 2.0)


class Rectangle(_BBox):
    def __init__(self, p1, p2):
        _BBox.__init__(self, p1, p2)

    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1, y1 = canvas.toScreen(p1.x, p1.y)
        x2, y2 = canvas.toScreen(p2.x, p2.y)
        return canvas.create_rectangle(x1, y1, x2, y2, options, tag="rect")

    def clone(self):
        other = Rectangle(self.p1, self.p2)
        other.config = self.config.copy()
        return other


class Oval(_BBox):
    def __init__(self, p1, p2):
        _BBox.__init__(self, p1, p2)

    def clone(self):
        other = Oval(self.p1, self.p2)
        other.config = self.config.copy()
        return other

    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1, y1 = canvas.toScreen(p1.x, p1.y)
        x2, y2 = canvas.toScreen(p2.x, p2.y)
        return canvas.create_oval(x1, y1, x2, y2, options, tag="oval")


class Circle(Oval):
    def __init__(self, center, radius):
        p1 = Point(center.x - radius, center.y - radius)
        p2 = Point(center.x + radius, center.y + radius)
        Oval.__init__(self, p1, p2)
        self.radius = radius

    def clone(self):
        other = Circle(self.getCenter(), self.radius)
        other.config = self.config.copy()
        return other

    def getRadius(self):
        return self.radius


class Line(_BBox):
    def __init__(self, p1, p2):
        super().__init__(self, p1, p2, ["arrow", "fill", "width"])
        self.setFill(DEFAULT_CONFIG["outline"])
        self.setOutline = self.setFill

    def clone(self):
        other = Line(self.p1, self.p2)
        other.config = self.config.copy()
        return other

    def _draw(self, canvas, options):
        p1 = self.p1
        p2 = self.p2
        x1, y1 = canvas.toScreen(p1.x, p1.y)
        x2, y2 = canvas.toScreen(p2.x, p2.y)
        return canvas.create_line(x1, y1, x2, y2, options, tag="line")

    def setArrow(self, option):
        if option not in ["first", "last", "both", "none"]:
            raise GraphicsError(BAD_OPTION)
        self._reconfig("arrow", option)


class Polygon(GraphicsObject):
    def __init__(self, *points):
        # if points passed as a list, extract it
        if len(points) == 1 and isinstance(points[0], list):
            points = points[0]
        self.points = list(map(Point.clone, points))
        self.p1 = Point(
            min([p.x for p in self.points]), min([p.y for p in self.points])
        )
        self.p2 = Point(
            max([p.x for p in self.points]), max([p.y for p in self.points])
        )
        GraphicsObject.__init__(self, ["outline", "width", "fill"])

    def clone(self):
        other = Polygon(*self.points)
        other.config = self.config.copy()
        return other

    def getPoints(self):
        return list(map(Point.clone, self.points))

    def _move(self, dx, dy):
        for p in self.points:
            p.move(dx, dy)
        self.p1.move(dx, dy)
        self.p2.move(dx, dy)

    def _draw(self, canvas, options):
        args = [canvas]
        for p in self.points:
            x, y = canvas.toScreen(p.x, p.y)
            args.append(x)
            args.append(y)
        args.append(options)
        return GraphWin.create_polygon(*args)


class Text(GraphicsObject):
    def __init__(self, p, text):
        GraphicsObject.__init__(self, ["justify", "fill", "text", "font"])
        self.setText(text)
        self.anchor = p.clone()
        self.setFill(DEFAULT_CONFIG["outline"])
        self.setOutline = self.setFill

    def _draw(self, canvas, options):
        p = self.anchor
        x, y = canvas.toScreen(p.x, p.y)
        return canvas.create_text(x, y, options, tag="text")

    def _move(self, dx, dy):
        self.anchor.move(dx, dy)

    def clone(self):
        other = Text(self.anchor, self.config["text"])
        other.config = self.config.copy()
        return other

    def setText(self, text):
        self._reconfig("text", text)

    def getText(self):
        return self.config["text"]

    def getAnchor(self):
        return self.anchor.clone()

    def setFace(self, face):
        if face in ["helvetica", "arial", "courier", "times roman"]:
            f, s, b = self.config["font"]
            self._reconfig("font", (face, s, b))
        else:
            raise GraphicsError(BAD_OPTION)

    def setSize(self, size):
        if 5 <= size <= 36:
            f, s, b = self.config["font"]
            self._reconfig("font", (f, size, b))
        else:
            raise GraphicsError(BAD_OPTION)

    def setStyle(self, style):
        if style in ["bold", "normal", "italic", "bold italic"]:
            f, s, b = self.config["font"]
            self._reconfig("font", (f, s, style))
        else:
            raise GraphicsError(BAD_OPTION)

    def setTextColor(self, color):
        self.setFill(color)


class Entry(GraphicsObject):
    def __init__(self, p, width):
        GraphicsObject.__init__(self, [])
        self.anchor = p.clone()
        # print self.anchor
        self.width = width
        # self.text = tk.StringVar(_root)
        # self.text.set("")
        self.text = _tkCall(tk.StringVar, _root)
        _tkCall(self.text.set, "")
        self.fill = "gray"
        self.color = "black"
        self.font = DEFAULT_CONFIG["font"]
        self.entry = None

    def _draw(self, canvas, options):
        p = self.anchor
        x, y = canvas.toScreen(p.x, p.y)
        frm = tk.Frame(canvas.master)
        self.entry = tk.Entry(
            frm,
            width=self.width,
            textvariable=self.text,
            bg=self.fill,
            fg=self.color,
            font=self.font,
        )
        self.entry.pack()
        # self.setFill(self.fill)
        return canvas.create_window(x, y, window=frm)

    def getText(self):
        return _tkCall(self.text.get)

    def _move(self, dx, dy):
        self.anchor.move(dx, dy)

    def getAnchor(self):
        return self.anchor.clone()

    def clone(self):
        other = Entry(self.anchor, self.width)
        return _tkCall(self.__clone_help, other)

    def __clone_help(self, other):
        other.config = self.config.copy()
        other.text = tk.StringVar()
        other.text.set(self.text.get())
        other.fill = self.fill
        return other

    def setText(self, t):
        # self.text.set(t)
        _tkCall(self.text.set, t)

    def setFill(self, color):
        self.fill = color
        if self.entry:
            # self.entry.config(bg=color)
            _tkExec(self.entry.config, bg=color)

    def _setFontComponent(self, which, value):
        font = list(self.font)
        font[which] = value
        self.font = tuple(font)
        if self.entry:
            # self.entry.config(font=self.font)
            _tkExec(self.entry.config, font=self.font)

    def setFace(self, face):
        if face in ["helvetica", "arial", "courier", "times roman"]:
            self._setFontComponent(0, face)
        else:
            raise GraphicsError(BAD_OPTION)

    def setSize(self, size):
        if 5 <= size <= 36:
            self._setFontComponent(1, size)
        else:
            raise GraphicsError(BAD_OPTION)

    def setStyle(self, style):
        if style in ["bold", "normal", "italic", "bold italic"]:
            self._setFontComponent(2, style)
        else:
            raise GraphicsError(BAD_OPTION)

    def setTextColor(self, color):
        self.color = color
        if self.entry:
            # self.entry.config(fg=color)
            _tkExec(self.entry.config, fg=color)


class Picture(object):
    def __init__(self, original=None):
        if original is not None:
            self.width = original.width
            self.height = original.height
            self.image = original.image.copy()
            self.filename = original.filename
            self.mode = original.mode
            self.displayScale = original.displayScale
        else:
            self.width = 0
            self.height = 0
            self.image = None
            self.filename = None
            self.mode = None
            self.displayScale = 1

    def set(self, width, height, data=None, mode="color", value=255):
        self.width = width
        self.height = height
        self.mode = mode
        if mode.lower() == "color":
            if data is None:
                if type(value) == int:
                    data = array.array("B", [value] * (height * width * 3))
                elif len(value) == 3:
                    data = array.array("B", value * (height * width))
            self.image = PyImage.frombuffer(
                "RGB", (self.width, self.height), data, "raw", "RGB", 0, 1
            )
        elif mode.lower() == "image":
            self.image = data.copy()
        elif mode.lower() == "jpeg":
            self.image = PyImage.open(data).resize((width, height), PyImage.BILINEAR)
            # self.image = PyImage.open(data)
        else:  # "gray", "blob"
            self.image = PyImage.frombuffer(
                "L", (self.width, self.height), data, "raw", "L", 0, 1
            )
        if self.image.mode != "RGBA":  # palette
            self.image = self.image.convert("RGBA")
        self.pixels = self.image.load()
        self.palette = self.image.getpalette()
        self.filename = "Camera Image"

        # self.image = ImageTk.PhotoImage(self.temp, master=_root)
        maxsize = max(self.width, self.height)
        smallWindowThreshold = 250
        if maxsize < smallWindowThreshold:
            self.displayScale = smallWindowThreshold / maxsize

    def rotate(self, degreesCCwise):
        self.image = self.image.rotate(degreesCCwise)
        self.pixels = self.image.load()
        self.width = self.image.size[0]
        self.height = self.image.size[1]

    def resize(self, x, y):
        self.image = self.image.resize((int(x), int(y)))
        self.pixels = self.image.load()
        self.width = self.image.size[0]
        self.height = self.image.size[1]

    def scale(self, xfactor=None, yfactor=None):
        if xfactor is None:
            xfactor = 1
        if yfactor is None:
            yfactor = xfactor
        newWidth = int(self.width * xfactor)
        newHeight = int(self.height * yfactor)
        self.resize(newWidth, newHeight)

    def load(self, filename):
        # self.image = tk.PhotoImage(file=filename, master=_root)
        self.image = PyImage.open(filename)
        if self.image.mode != "RGBA":  # palette
            self.image = self.image.convert("RGBA")
        self.pixels = self.image.load()
        self.width = self.image.size[0]
        self.height = self.image.size[1]
        self.palette = self.image.getpalette()
        self.filename = filename
        if self.pixels is None:
            raise AttributeError(
                "Myro needs at least Python Imaging Library version 1.1.6"
            )

    def __repr__(self):
        return "<Picture instance (%d x %d)>" % (self.width, self.height)

    def getPixels(self):
        return (
            Pixel(x, y, self) for x in range(self.width) for y in range(self.height)
        )

    def getPixel(self, x, y):
        return Pixel(x, y, self)

    def getColor(self, x, y):
        retval = self.pixels[x, y]
        return Color(retval)

    def setColor(self, x, y, newColor):
        self.pixels[x, y] = tuple(newColor.getRGBA())

    def setRGB(self, x, y, rgb):
        self.setColor(x, y, Color(*rgb))

    def getRGB(self, x, y):
        return self.pixels[x, y][:3]

    def getRGBA(self, x, y):
        return self.pixels[x, y]

    def getAlpha(self, x, y):
        return self.pixels[x, y][3]

    def getWidth(self):
        return self.width

    def getHeight(self):
        return self.height


class Pixel(object):
    def __init__(self, x, y, picture):
        self.x = x
        self.y = y
        self.picture = picture
        self.pixels = picture.pixels
        # we might need this, for gifs:
        self.palette = self.picture.image.getpalette()

    def __repr__(self):
        rgba = self.getRGBA()
        return "<Pixel instance (r=%d, g=%d, b=%d, a=%d) at (%d, %d)>" % (
            rgba[0],
            rgba[1],
            rgba[2],
            rgba[3],
            self.x,
            self.y,
        )

    def getPixel(self, x, y):
        return Pixel(x, y, self.picture)

    def getColor(self):
        retval = self.pixels[self.x, self.y]
        return Color(retval)

    def setColor(self, newColor):
        self.pixels[self.x, self.y] = tuple(newColor.getRGBA())

    def setRGB(self, rgb):
        self.setColor(Color(*rgb))

    def getRGB(self):
        return self.pixels[self.x, self.y][:3]

    def getRGBA(self):
        return self.pixels[self.x, self.y]

    def getAlpha(self):
        return self.pixels[self.x, self.y][3]

    def setAlpha(self, alpha):
        rgba = self.pixels[self.x, self.y]
        self.pixels[self.x, self.y] = (rgba[0], rgba[1], rgba[2], alpha)

    def getX(self):
        return self.x

    def getY(self):
        return self.y

    def __eq__(self, other):
        o1 = self.getRGBA()
        o2 = other.getRGBA()
        return o1[0] == o2[0] and o1[1] == o2[1] and o1[2] == o2[2] and o1[3] == o2[3]

    def __ne__(self, other):
        return not self.__eq__(other)

    def __sub__(self, other):
        o1 = self.getRGB()
        o2 = other.getRGB()
        return Color(o1[0] - o2[0], o1[1] - o2[1], o1[2] - o2[2])

    def __add__(self, other):
        o1 = self.getRGB()
        o2 = other.getRGB()
        return Color(o1[0] + o2[0], o1[1] + o2[1], o1[2] + o2[2])

    def makeLighter(self):
        r, g, b = self.getRGB()
        rgb = (
            int(max(min((255 - r) * 0.35 + r, 255), 0)),
            int(max(min((255 - g) * 0.35 + g, 255), 0)),
            int(max(min((255 - b) * 0.35 + b, 255), 0)),
        )
        self.setColor(Color(rgb))

    def makeDarker(self):
        r, g, b = self.getRGB()
        rgb = (
            int(max(min(r * 0.65, 255), 0)),
            int(max(min(g * 0.65, 255), 0)),
            int(max(min(b * 0.65, 255), 0)),
        )
        self.setColor(Color(rgb))


class Color(object):
    def __init__(self, *rgb):
        """
        Returns a Color object. Takes red, green, blue, and optionally
        a transparency (called alpha). All values are between 0 and 255).
        """
        self.alpha = 255
        if len(rgb) == 1:
            # Accept a string in the hext fromat made by color_rgb func.
            if isinstance(rgb[0], str):
                self.rgb = rgb_color(rgb[0])
            else:
                self.rgb = rgb[0]
        elif len(rgb) == 3:
            self.rgb = rgb
        elif len(rgb) == 4:
            self.rgb = rgb[:-1]
            self.alpha = rgb[-1]
        else:
            raise AttributeError(
                "invalid arguments to Color(); needs at least 3 integers: red, green, blue (transparency optional)"
            )
        self.rgb = [int(max(min(v, 255), 0)) for v in self.rgb]

    def __repr__(self):
        return "<Color instance (r=%d, g=%d, b=%d, a=%d)>" % (
            self.rgb[0],
            self.rgb[1],
            self.rgb[2],
            self.alpha,
        )

    def getColor(self):
        return Color(self.rgb)

    def getAlpha(self):
        return self.alpha

    def setAlpha(self, value):
        self.alpha = value

    def setColor(self, color):
        self.rgb = color.getRGB()

    def setRGB(self, rgb):
        self.rgb = copy(rgb)

    def getRGB(self):
        return self.rgb

    def getRGBA(self):
        return (self.rgb[0], self.rgb[1], self.rgb[2], self.alpha)

    def __eq__(self, other):
        o1 = self.getRGBA()
        o2 = other.getRGBA()
        return o1[0] == o2[0] and o1[1] == o2[1] and o1[2] == o2[2] and o1[3] == o2[3]

    def __ne__(self, other):
        return not self.__eq__(other)

    def __sub__(self, other):
        o1 = self.getRGB()
        o2 = other.getRGB()
        return Color(o1[0] - o2[0], o1[1] - o2[1], o1[2] - o2[2])

    def __add__(self, other):
        o1 = self.getRGB()
        o2 = other.getRGB()
        return Color(o1[0] + o2[0], o1[1] + o2[1], o1[2] + o2[2])

    def makeLighter(self):
        r, g, b = self.rgb
        self.rgb = (
            int(max(min((255 - r) * 0.35 + r, 255), 0)),
            int(max(min((255 - g) * 0.35 + g, 255), 0)),
            int(max(min((255 - b) * 0.35 + b, 255), 0)),
        )

    def makeDarker(self):
        r, g, b = self.rgb
        self.rgb = (
            int(max(min(r * 0.65, 255), 0)),
            int(max(min(g * 0.65, 255), 0)),
            int(max(min(b * 0.65, 255), 0)),
        )


makeColor = Color

black = Color(0, 0, 0)
white = Color(255, 255, 255)
blue = Color(0, 0, 255)
red = Color(255, 0, 0)
green = Color(0, 255, 0)
gray = Color(128, 128, 128)
darkGray = Color(64, 64, 64)
lightGray = Color(192, 192, 192)
yellow = Color(255, 255, 0)
pink = Color(255, 175, 175)
magenta = Color(255, 0, 255)
cyan = Color(0, 255, 255)


def makeWindow(*args, **kwargs):
    return GraphWin(*args, **kwargs)


def makeEntry(*args, **kwargs):
    return Entry(*args, **kwargs)


def makePoint(*args, **kwargs):
    return Point(*args, **kwargs)


def makeRectangle(*args, **kwargs):
    return Rectangle(*args, **kwargs)


def makeOval(*args, **kwargs):
    return Oval(*args, **kwargs)


def makeCircle(*args, **kwargs):
    return Circle(*args, **kwargs)


def makeLine(*args, **kwargs):
    return Line(*args, **kwargs)


def makePolygon(*args, **kwargs):
    return Polygon(*args, **kwargs)


def makeText(*args, **kwargs):
    return Text(*args, **kwargs)


class Senses(tkinter.Toplevel):
    def __init__(self, robot=None):
        _tkCall(self.__init_help, _root, robot)

    def __init_help(self, parent=None, robot=None):
        tkinter.Toplevel.__init__(self, parent)
        self.debug = 0
        self._running = 0
        if robot is None:
            self.robot = myro.globvars.robot
        else:
            self.robot = robot
        self.parent = parent
        self.wm_title("Senses")
        moveToTop(self)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.widgets = {}
        self.frame = tkinter.Frame(self, relief=tkinter.RAISED, borderwidth=2)
        items = []
        if self.robot is not None:
            d = self.robot.get("config")
            items = [(key, d[key]) for key in list(d.keys())]
        self.addWidgets(self.frame, *items)
        self.frame.pack(side="bottom", fill="both", expand="y")
        self.translate = 0.0
        self.rotate = 0.0
        self.threshold = 0.10
        self.delay = 0.10  # in seconds
        self.running = 1
        # self.frame.pack()
        self.after(250, self._update_help)

    def _update_help(self, delay=None):
        if self.robot:
            config = self.robot.get("config")
            data = self.robot.getAll()
            for key in config:
                item = data.get(key, [0] * config[key])
                if type(item) not in [list, tuple]:
                    item = [item]
                for i in range(len(item)):
                    self.updateWidget(key, i, item[i])
        self.update()
        if self.running:
            self.after(250, self._update_help)

    def destroy(self):
        self.running = 0
        if self.robot is not None:
            self.robot.lock.acquire()
        tkinter.Toplevel.destroy(self)
        if self.robot is not None:
            self.robot.lock.release()

    def addWidgets(self, window, *items):
        for name, size in items:
            text = name + ":"
            frame = tkinter.Frame(window)
            self.widgets[name + ".label"] = tkinter.Label(frame, text=text, width=10)
            self.widgets[name + ".label"].pack(side="left")
            for i in range(size - 1, -1, -1):
                self.widgets["%s%d.entry" % (name, i)] = tkinter.Entry(
                    frame, bg="white", width=10
                )
                self.widgets["%s%d.entry" % (name, i)].insert(0, "")
                self.widgets["%s%d.entry" % (name, i)].pack(
                    side="right", fill="both", expand="y"
                )
            frame.pack(side="bottom", fill="both", expand="y")

    def updateWidget(self, name, pos, value):
        """
        Updates the device view window.
        """
        try:
            self.widgets["%s%d.entry" % (name, pos)].delete(0, "end")
            self.widgets["%s%d.entry" % (name, pos)].insert(0, str(value))
        except Exception:
            pass

    def minorloop(self, delay=None):  # in milliseconds
        """
        As opposed to mainloop. This is a simple loop that works
        in IDLE.
        """
        if delay is not None:
            self.delay = delay
        self.running = 1
        lastUpdated = 0
        lastData = []
        config = self.robot.get(
            "config"
        )  # {"ir": 2, "line": 2, "stall": 1, "light": 3}
        while self.running:
            # self.focus_set()
            if self.robot:
                data = self.robot.getLastSensors()
                now = time.time()
                if data != lastData or now - lastUpdated > 1:
                    if now - lastUpdated > 1:
                        data = self.robot.getAll()
                    for key in config:
                        item = data.get(key, [0] * config[key])
                        if type(item) not in [list, tuple]:
                            item = [item]
                        for i in range(len(item)):
                            self.updateWidget(key, i, item[i])
                    lastUpdated = time.time()
                    lastData = data
            self.update()
            time.sleep(self.delay)


class Calibrate(tkinter.Toplevel):
    def __init__(self, robot=None):
        _tkCall(self.__init_help, _root, robot)

    def __init_help(self, parent=None, robot=None):
        tkinter.Toplevel.__init__(self, parent)
        self.debug = 0
        self._running = 0

        self.robot = robot

        self._f1, self._f2, self._f3, self._f4 = self.robot.getFudge()
        self._lastFudged = time.time()
        self.parent = parent
        self.wm_title("calibstick")
        moveToTop(self)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.frame = tkinter.Frame(self)
        label = tkinter.Label(self.frame, text="Forward")
        label.pack(side="top")
        label = tkinter.Label(self.frame, text="Reverse")
        label.pack(side="bottom")
        label = tkinter.Label(self.frame, text="Turn\nLeft")
        label.pack(side="left")
        label = tkinter.Label(self.frame, text="Turn\nRight")
        label.pack(side="right")
        self.canvas = tkinter.Canvas(self.frame, width=220, height=220, bg="white")
        self.widgets = {}
        newFrame = tkinter.Frame(self, relief=tkinter.RAISED, borderwidth=2)
        self.addWidgets(
            newFrame,
            ("-1 Tweak", 1),
            ("-0.5 Tweak", 1),
            ("0.5 Tweak", 1),
            ("1 Tweak", 1),
        )
        newFrame.pack(side="bottom", fill="both", expand="y")

        self.initHandlers()
        self.canvas.pack(side=tkinter.BOTTOM)

        # self.circle_dim = (10, 100, 210, 120) #x0, y0, x1, y1
        #
        # self.circle = self.canvas.create_rectangle(self.circle_dim, fill = 'white')

        # Create bars for the 1, 0.5, 0, -0.5, and -1 settings (200 x 20 rect)
        self.canvas.create_rectangle((10, 5, 210, 25), fill="white")  # -1
        self.canvas.create_rectangle((10, 45, 210, 65), fill="white")  # -0.5
        self.canvas.create_rectangle((10, 150, 210, 170), fill="white")  # 0.5
        self.canvas.create_rectangle((10, 195, 210, 215), fill="white")  # 1

        # Create some marks for the 1, 0.5, 0, -0.5, and 1 settings
        self.canvas.create_rectangle(105, 10, 115, 20, fill="black")
        self.canvas.create_rectangle(105, 50, 115, 60, fill="black")
        self.canvas.create_rectangle(105, 105, 115, 115, fill="black")
        self.canvas.create_rectangle(105, 155, 115, 165, fill="black")
        self.canvas.create_rectangle(105, 200, 115, 210, fill="black")

        self.frame.pack()
        self.translate = 0.0
        self.rotate = 0.0
        self.threshold = 0.00
        self.delay = 0.10  # in seconds
        self.running = 0

        self.updateWidget("1 Tweak", 0, self._f1)
        self.updateWidget("0.5 Tweak", 0, self._f2)
        self.updateWidget("-0.5 Tweak", 0, self._f3)
        self.updateWidget("-1 Tweak", 0, self._f4)

        # END OF THE FUNCTION!

    def destroy(self):
        self.running = 0
        tkinter.Toplevel.destroy(self)

    def addWidgets(self, window, *items):
        for name, size in items:
            text = name + ":"
            frame = tkinter.Frame(window)
            self.widgets[name + ".label"] = tkinter.Label(frame, text=text, width=10)
            self.widgets[name + ".label"].pack(side="left")
            for i in range(size):
                self.widgets["%s%d.entry" % (name, i)] = tkinter.Entry(
                    frame, bg="white", width=10
                )
                self.widgets["%s%d.entry" % (name, i)].insert(0, "")
                self.widgets["%s%d.entry" % (name, i)].pack(
                    side="right", fill="both", expand="y"
                )
            frame.pack(side="bottom", fill="both", expand="y")

    def updateWidget(self, name, pos, value):
        """
        Updates the device view window.
        """
        try:
            self.widgets["%s%d.entry" % (name, pos)].delete(0, "end")
            self.widgets["%s%d.entry" % (name, pos)].insert(0, value)
        except Exception:
            pass

    def minorloop(self, delay=None):  # in milliseconds
        """
        As opposed to mainloop. This is a simple loop that works
        in IDLE.
        """
        if delay is not None:
            self.delay = delay
        self.running = 1
        while self.running:
            self.update()
            time.sleep(self.delay)

    def initHandlers(self):
        self.canvas.bind("<ButtonRelease-1>", self.canvas_clicked_up)
        self.canvas.bind("<Button-1>", self.canvas_clicked_down)
        self.canvas.bind("<B1-Motion>", self.canvas_moved)

    def getValue(self, event=None):
        return self.translate, self.rotate

    def move(self, translate, rotate):
        self.translate = translate

        if self.translate < 0.0:
            self.translate += self.threshold
        elif self.translate > 0.0:
            self.translate -= self.threshold
        self.rotate = rotate

        if self.rotate < 0.0:
            self.rotate += self.threshold
        elif self.rotate > 0.0:
            self.rotate -= self.threshold

        if self.debug:
            print(self.translate, self.rotate)

        if self.robot is not None:
            # self.robot.lock.acquire()
            self.robot.move(self.translate, self.rotate)
            # self.robot.lock.release()

    def canvas_clicked_up(self, event):
        self.canvas.delete("lines")
        self.move(0.0, 0.0)

    def drawArrows(self, x, y, trans, rotate):
        if trans != 0:
            self.canvas.create_line(
                110,
                110,
                110,
                (110 - (90 * trans)),
                width=3,
                fill="blue",
                tag="lines",
                arrowshape=(10, 10, 3),
                arrow="last",
            )
        self.canvas.create_line(
            110,
            110,
            x,
            110,
            width=3,
            fill="red",
            tag="lines",
            arrowshape=(10, 10, 3),
            arrow="last",
        )

    def canvas_clicked_down(self, event):
        trans, rotate = self.calc_tr(event.x, event.y)
        self.drawArrows(event.x, event.y, trans, rotate)
        self.move(trans, rotate)

    def canvas_moved(self, event):
        self.canvas.delete("lines")
        trans, rotate = self.calc_tr(event.x, event.y)
        self.drawArrows(event.x, event.y, trans, rotate)
        self.move(trans, rotate)

    def stop(self):
        self.move(0.0, 0.0)

    def calc_tr(self, x, y):
        offCenter = (x - 105.0) / 205.0

        if offCenter > 1.0:
            offCenter = 1.0

        if offCenter < -1.0:
            offCenter = -1.0

        if y < 35:
            speed = 1.0
            self._f1 = 1.0 - offCenter
        elif y < 82:
            speed = 0.5
            self._f2 = 1.0 - offCenter
        elif y < 135:
            speed = 0.0

        elif y < 182:
            speed = -0.5
            self._f3 = 1.0 - offCenter
        else:
            speed = -1.0
            self._f4 = 1.0 - offCenter

        self.updateWidget("1 Tweak", 0, self._f1)
        self.updateWidget("0.5 Tweak", 0, self._f2)
        self.updateWidget("-0.5 Tweak", 0, self._f3)
        self.updateWidget("-1 Tweak", 0, self._f4)
        # Update the fudge values.
        self.robot.setFudge(self._f1, self._f2, self._f3, self._f4)

        trans = speed
        rot = 0.0
        return (trans, rot)


# TODO: Switch everything to np arrays.
# Then use either PIL/CV2 color conversion methods.
def rgb2hsv(red, green, blue):
    """
    Converts red, green, and blue to hue, saturation, and brightness
    """
    return colorsys.rgb_to_hsv(red, green, blue)


def hls2rgb(h, l, s):
    return colorsys.hls_to_rgb(h, l, s)


def hsv2rgb(h, s, v):
    return colorsys.hsv_to_rgb(h, s, v)


def rgb2hls(red, green, blue):
    return colorsys.rgb_to_hls(red, green, blue)


def rgb2yiq(red, green, blue):
    return colorsys.rgb_to_yiq(red, green, blue)


def yiq2rgb(y, i, q):
    return colorsys.yiq_to_rgb(y, i, q)


def yuv2rgb(Y, U, V):
    R = int(Y + (1.4075 * (V - 128)))
    G = int(Y - (0.3455 * (U - 128)) - (0.7169 * (V - 128)))
    B = int(Y + (1.7790 * (U - 128)))
    return [max(min(v, 255), 0) for v in (R, G, B)]


def rgb2yuv(R, G, B):
    Y = int(0.299 * R + 0.587 * G + 0.114 * B)
    U = int(-0.14713 * R - 0.28886 * G + 0.436 * B + 128)
    V = int(0.615 * R - 0.51499 * G - 0.10001 * B + 128)
    return [max(min(v, 255), 0) for v in (Y, U, V)]


# Kill the tk thread at exit
if myro.globvars.runtkthread:
    atexit.register(_tkShutdown)

_functions = (
    "move To Top",
    "distance",
    "ask Question",
    "pick A File",
    "pick A Color",
    "pick A Folder",
    "make Window",
    "make Image",
    "make Entry",
    "make Point",
    "make Rectangle",
    "make Oval",
    "make Circle",
    "make Line",
    "make Polygon",
    "make Text",
    "make Sound",
    "play",
)

globvars.makeEnvironment(locals(), _functions)

_variables = (
    "black",
    "white",
    "blue",
    "red",
    "green",
    "gray",
    "dark Gray",
    "light Gray",
    "yellow",
    "pink",
    "magenta",
    "cyan",
)

globvars.makeEnvironment(locals(), _variables, "variables")
