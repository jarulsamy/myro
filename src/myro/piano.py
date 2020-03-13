# -*- coding: utf-8 -*-
import tkinter


class Piano(tkinter.Toplevel):
    def __init__(self, parent=None, robot=None):
        tkinter.Toplevel.__init__(self, parent)
        self._running = 0
        self.robot = robot
        self.parent = parent
        self.wm_title("Piano")
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.frame = tkinter.Frame(self)
        self.canvas = tkinter.Canvas(self.frame, width=15 * 88, height=220, bg="white")
        self.initHandlers()
        self.canvas.pack(side=tkinter.BOTTOM)
        self.frame.pack()
        for i in range(88):
            self.canvas.create_line(i * 15, 0, i * 15, 220, fill="black", tag="lines")

    def initHandlers(self):
        self.canvas.bind("<ButtonRelease-1>", self.canvas_clicked_up)
        self.canvas.bind("<Button-1>", self.canvas_clicked_down)
        self.canvas.bind("<B1-Motion>", self.canvas_moved)

    def canvas_clicked_up(self, event):
        pass

    def canvas_clicked_down(self, event):
        pass

    def canvas_moved(self, event):
        pass

    def destroy(self):
        """Hides the device view window."""
        self.withdraw()
        if self._running:
            if "quit" in dir(self.parent):
                self.parent.quit()
            if "destroy" in dir(self.parent):
                self.parent.destroy()


if __name__ == "__main__":
    app = tkinter.Tk()
    app.withdraw()
    piano = Piano(parent=app)
    app._running = 1
    app.mainloop()
