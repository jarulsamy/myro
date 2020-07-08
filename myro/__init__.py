from .globals import Globals
from .robots.scribbler import Scribbler


def ensure_init(func):
    """
    Decorator to ensure robot is initialized
    """

    def ensure_and_call(*args, **kwargs):
        if not Globals.robot:
            raise AttributeError("Need to initialize robot first")
        return func(*args, **kwargs)

    return ensure_and_call


def init(port: str):
    Globals.robot = Scribbler(port)
    Globals.mprint(f"Myro version: {Globals.version}")

    for k, v in Globals.robot.get_info().items():
        Globals.mprint(f"{k}: {v}")


@ensure_init
def close():
    Globals.robot.close()


@ensure_init
def restart():
    return Globals.robot.restart()


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
def motors(left, right):
    return Globals.robot.motors(left, right)


@ensure_init
def take_picture():
    return Globals.robot.take_picture()


@ensure_init
def get_angle():
    return Globals.robot.get_angle()


@ensure_init
def set_angle(new_ang):
    return Globals.robot.set_angle(new_ang)


@ensure_init
def turn_by(self, angle, radsOrDegrees="degrees"):
    return Globals.robot.turn_by(angle, radsOrDegrees)


@ensure_init
def turn_to(self, angle, radsOrDegrees="degrees"):
    return Globals.robot.turn_to(angle, radsOrDegrees)


@ensure_init
def get_light(*pos):
    return Globals.robot.get("light", *pos)


@ensure_init
def get_IR(*pos):
    return Globals.robot.get_IR(*pos)


@ensure_init
def get_line(*pos):
    return Globals.robot.get_line(*pos)

# TODO: add get_name into get_info()


@ensure_init
def get_forwardness():
    return Globals.robot.get_forwardness()


@ensure_init
def get_battery():
    return Globals.robot.getBattery()


@ensure_init
def update():
    return Globals.robot.update()


@ensure_init
def setIRPower(value):
    return Globals.robot.setIRPower(value)


@ensure_init
def set_white_balance(value):
    return Globals.robot.set_white_balance(value)


@ensure_init
def set_led(value, position):
    return Globals.robot.set_led(value, position)
