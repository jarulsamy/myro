from .__version__ import VERSION, AUTHOR
import os


def dummy_print(*args, **kwargs):
    return


class Globals:

    robot = None
    version = VERSION
    author = AUTHOR

    # Silence verbose output based on env var
    mprint = print
    if os.getenv("MYRO_SILENCE") == "1":
        mprint = dummy_print


class SerialTimeout:

    def __init__(self, ser, new_timeout):
        self.ser = ser
        self.old = ser.timeout
        self.new = new_timeout

    def __enter__(self):
        self.ser.timeout = self.new

    def __exit__(self, exception, value, tb):
        self.ser.timeout = self.old
        if not exception:
            return False
