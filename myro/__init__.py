from .globals import Globals
from .robots.scribbler import Scribbler


def init(port: str):
    Globals.robot = Scribbler(port)
    Globals.mprint(f"Myro version: {Globals.version}")

    for k, v in Globals.robot.get_info().items():
        Globals.mprint(f"{k}: {v}")


def ensure_init(func):
    """
    Decorator to ensure robot is initialized
    """

    def ensure_and_call(*args, **kwargs):
        if not Globals.robot:
            raise AttributeError("Need to initialize robot first")
        return func(*args, **kwargs)

    return ensure_and_call


@ensure_init
def translate(amount):
    return Globals.robot.translate(amount)


@ensure_init
def rotate(amount):
    return Globals.robot.rotate(amount)


@ensure_init
def move(translate, rotate):
    return Globals.robot.move(translate, rotate)


@ensure_init
def forward(speed=1, seconds=0):
    return Globals.robot.forward(speed, seconds)


@ensure_init
def backward(speed=1, seconds=0):
    return Globals.robot.backward(speed, seconds)


@ensure_init
def turn_right(speed=1, seconds=0):
    return Globals.robot.turn_right(speed, seconds)


@ensure_init
def turn_left(speed=1, seconds=0):
    return Globals.robot.turn_left(speed, seconds)


@ensure_init
def stop():
    return Globals.robot.stop()


@ensure_init
def take_picture():
    return Globals.robot.take_picture()
