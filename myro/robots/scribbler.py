import threading
import time

import serial
from PIL import Image

from ..globals import Globals
from ..globals import SerialTimeout


class Scribbler:
    SOFT_RESET = 33
    GET_ALL = 65
    GET_ALL_BINARY = 66
    GET_LIGHT_LEFT = 67
    GET_LIGHT_CENTER = 68
    GET_LIGHT_RIGHT = 69
    GET_LIGHT_ALL = 70
    GET_IR_LEFT = 71
    GET_IR_RIGHT = 72
    GET_IR_ALL = 73
    GET_LINE_LEFT = 74
    GET_LINE_RIGHT = 75
    GET_LINE_ALL = 76
    GET_STATE = 77
    GET_NAME1 = 78
    GET_NAME2 = 64
    GET_STALL = 79
    GET_INFO = 80
    GET_DATA = 81

    GET_PASS1 = 50
    GET_PASS2 = 51

    # a segmented and run-length encoded image
    GET_RLE = 82
    # the entire 256 x 192 image in YUYV format
    GET_IMAGE = 83
    # the windowed image (followed by which window)
    GET_WINDOW = 84
    # number of returned pulses when left emitter is turned on
    GET_DONGLE_L_IR = 85
    # number of returned pulses when center emitter is turned on
    GET_DONGLE_C_IR = 86
    # number of returned pulses when right emitter is turned on
    GET_DONGLE_R_IR = 87
    # average intensity in the user defined region
    GET_WINDOW_LIGHT = 88
    # battery voltage
    GET_BATTERY = 89
    # with the address returns the value in serial memory
    GET_SERIAL_MEM = 90
    # with offset, returns the scribbler program buffer
    GET_SCRIB_PROGRAM = 91
    # with address, returns the camera parameter at that address
    GET_CAM_PARAM = 92

    GET_BLOB = 95

    SET_PASS1 = 55
    SET_PASS2 = 56
    SET_SINGLE_DATA = 96
    SET_DATA = 97
    SET_ECHO_MODE = 98
    SET_LED_LEFT_ON = 99
    SET_LED_LEFT_OFF = 100
    SET_LED_CENTER_ON = 101
    SET_LED_CENTER_OFF = 102
    SET_LED_RIGHT_ON = 103
    SET_LED_RIGHT_OFF = 104
    SET_LED_ALL_ON = 105
    SET_LED_ALL_OFF = 106
    SET_LED_ALL = 107
    SET_MOTORS_OFF = 108
    SET_MOTORS = 109
    SET_NAME1 = 110
    # set name2 byte
    SET_NAME2 = 119
    SET_LOUD = 111
    SET_QUIET = 112
    SET_SPEAKER = 113
    SET_SPEAKER_2 = 114

    # turn binary dongle led on
    SET_DONGLE_LED_ON = 116
    # turn binary dongle led off
    SET_DONGLE_LED_OFF = 117
    # set rle parameters
    SET_RLE = 118
    # set dongle IR power
    SET_DONGLE_IR = 120
    # set serial memory byte
    SET_SERIAL_MEM = 121
    # set scribbler program memory byte
    SET_SCRIB_PROGRAM = 122
    # initiate scribbler programming process
    SET_START_PROGRAM = 123
    # hard reset scribbler
    SET_RESET_SCRIBBLER = 124
    # erase serial memory
    SET_SERIAL_ERASE = 125
    # set dimmer led
    SET_DIMMER_LED = 126
    # set user defined window
    SET_WINDOW = 127
    # set direction of scribbler
    SET_FORWARDNESS = 128
    # turn on white balance on camera
    SET_WHITE_BALANCE = 129
    # diable white balance on camera (default)
    SET_NO_WHITE_BALANCE = 130
    # with address and value, sets the camera parameter at that address
    SET_CAM_PARAM = 131

    GET_JPEG_GRAY_HEADER = 135
    GET_JPEG_GRAY_SCAN = 136
    GET_JPEG_COLOR_HEADER = 137
    GET_JPEG_COLOR_SCAN = 138

    SET_PASS_N_BYTES = 139
    GET_PASS_N_BYTES = 140
    GET_PASS_BYTES_UNTIL = 141

    GET_VERSION = 142

    GET_IR_MESSAGE = 150
    SEND_IR_MESSAGE = 151
    SET_IR_EMITTERS = 152

    # initiate scribbler2 programming process
    SET_START_PROGRAM2 = 153
    # hard reset scribbler2
    SET_RESET_SCRIBBLER2 = 154
    # upload scribbler2 firmware
    SET_SCRIB_BATCH = 155
    GET_ROBOT_ID = 156
    # Format 160 volume (0-100) Percent Volume Level
    SET_VOLUME = 160
    SET_PATH = 161
    # Format 162 type hXByte lXByte hYByte lYByte
    SET_MOVE = 162
    # Format 163 type hXByte lXByte hYByte lYByte hRadByte lRadByte
    SET_ARC = 163
    # Format 164 type hAngleByte lAngleByte
    SET_TURN = 164
    # Format 165
    GET_POSN = 165
    # Format 166 x0Byte x1Byte x2Byte x3Byte y0Byte y1Byte y2Byte y3Byte
    SET_POSN = 166
    GET_ANGLE = 167
    # Format 168 angle0Byte angle1Byte angle2Byte angle3Byte
    SET_ANGLE = 168
    GET_MIC_ENV = 169
    GET_MOTOR_STATS = 170
    GET_ENCODERS = 171

    # Format 172 side type thres
    GET_IR_EX = 172
    # Format 173 side type thres
    GET_LINE_EX = 173
    # Format 175 side
    GET_DISTANCE = 175
    PACKET_LENGTH = 9
    ENCODING_TYPE = "ISO-8859-1"

    # Used with SET_PATH to say beginning of a path
    BEGIN_PATH = 0
    # Used with SET_PATH to say end of a path
    END_PATH = 1
    # Used in movement commands, by means how much you wish to move by
    BY = 4
    # Used in movement commands, to means the heading you want to turn to
    TO = 2
    # Used in movement commands, specifies using degress instead of S2 angle
    DEG = 1

    # Camera
    CAM_PID = 0x0A
    CAM_PID_DEFAULT = 0x76
    CAM_VER = 0x0B
    CAM_VER_DEFAULT = 0x48
    CAM_BRT = 0x06
    CAM_BRT_DEFAULT = 0x80
    CAM_EXP = 0x10
    CAM_EXP_DEFAULT = 0x41
    CAM_COMA = 0x12
    CAM_COMA_DEFAULT = 0x14

    CAM_COMA_WHITE_BALANCE_ON = CAM_COMA_DEFAULT | (1 << 2)
    CAM_COMA_WHITE_BALANCE_OFF = CAM_COMA_DEFAULT & ~(1 << 2)

    CAM_COMB = 0x13
    CAM_COMB_DEFAULT = 0xA3
    CAM_COMB_GAIN_CONTROL_ON = CAM_COMB_DEFAULT | (1 << 1)
    CAM_COMB_GAIN_CONTROL_OFF = CAM_COMB_DEFAULT & ~(1 << 1)
    CAM_COMB_EXPOSURE_CONTROL_ON = CAM_COMB_DEFAULT | (1 << 0)
    CAM_COMB_EXPOSURE_CONTROL_OFF = CAM_COMB_DEFAULT & ~(1 << 0)

    def __init__(self, port: str, baudrate=38400):
        super().__init__()
        self.lock = threading.Lock()

        # Camera Addresses #
        self.height = 0
        self.width = 0

        self.ser = None
        self.requestStop = 0
        self.debug = 0
        self._lastTranslate = 0
        self._lastRotate = 0
        self._volume = 0
        self.emitters = 0x1 | 0x2 | 0x4

        self.ser_port = port
        self.baudrate = baudrate
        self.open()

        Globals.robot = self

    def open(self):
        """Connect to robot"""
        failed = False
        for i in range(3):
            try:
                self.ser = serial.Serial(self.ser_port, timeout=10)
                # For directly connected scribbler 2
                self.ser.setDTR(0)
                self.ser.baudrate = self.baudrate
                break
            except serial.SerialException:
                failed = True

        if failed:
            raise self.ser.SerialException("Connection failed!")

        self.get_info()
        if self.fluke_vers >= [3, 0, 0]:
            self.width = 1280
            self.height = 800
        else:
            self.width = 256
            self.height = 192

    def close(self):
        """Disconnect from robot"""
        self.ser.close()

    def restart(self):
        self._manual_flush()

    def _set_echo_mode(self, value: bool):
        self._set(self.SET_ECHO_MODE, value)
        time.sleep(0.25)
        self._io_flush()

    def _io_flush(self):
        self.ser.flushInput()
        self.ser.flushOutput()

    def _manual_flush(self):
        with SerialTimeout(self.ser, 0.5):
            dummy_read = "foobar"
            dummy_count = 0
            while len(dummy_read) > 0 and dummy_count < 50000:
                dummy_read = self.ser.read(1)
                dummy_count += len(dummy_read)

    def _read(self, num_bytes=1):
        raw_data = self.ser.read(num_bytes).decode(self.ENCODING_TYPE)
        while num_bytes > 1 and len(raw_data) < num_bytes:
            raw_data = raw_data + self.ser.read(num_bytes - len(raw_data))

        # HACK. Somehow the serial interaction with scribbler can't keep up.
        time.sleep(0.01)

        if num_bytes != 1:
            return [ord(i) for i in raw_data]

    def _read_image(self):
        self.lock.acquire()

        data = bytes()
        with SerialTimeout(self.ser, 0.01):
            self.ser.write(bytes(chr(self.GET_IMAGE), self.ENCODING_TYPE))
            size = self.width * self.height

            while len(data) < size:
                data += self.ser.readline()

        self.lock.release()
        return data

    def _write(self, raw_data):
        t = [chr(int(x)) for x in raw_data]
        data = "".join(t) + (chr(0) * (self.PACKET_LENGTH - len(t)))[:9]

        # write packets
        self.ser.write(bytes(data, self.ENCODING_TYPE))

    def _set(self, *values):
        try:
            self.lock.acquire()
            self._write(values)
            self._read(self.PACKET_LENGTH)
        except KeyboardInterrupt:
            self.stop()
            self.lock.release()
        finally:
            self.lock.release()

    def _adjustSpeed(self):
        left = min(max(self._lastTranslate - self._lastRotate, -1), 1)
        right = min(max(self._lastTranslate + self._lastRotate, -1), 1)

        left_power = (left + 1.0) * 100.0
        right_power = (right + 1.0) * 100.0

        self._set(Scribbler.SET_MOTORS, right_power, left_power)

    def get_info(self, *item):
        payload = bytes(chr(self.GET_INFO) + (" " * 8), self.ENCODING_TYPE)
        with SerialTimeout(self.ser, 4):
            self._manual_flush()
            self.ser.write(payload)
            response = self.ser.readline()

            # HACK: Scribbler needs time to catch up.
            time.sleep(0.1)

            self.ser.write(payload)
            response = self.ser.readline().decode(self.ENCODING_TYPE)

        if not response:
            return {}

        if response.lower()[0] == "p":
            response = response[1:]

        info = {}
        for pair in response.split(","):
            key, val = pair.split(":")
            info[key] = val

        # info = self.get_info()["fluke"].split(".")
        fluke_vers = info["fluke"].split(".")
        self.fluke_vers = [int(i) for i in fluke_vers]

        return info

    def move(self, translate, rotate):
        self._lastTranslate = translate
        self._lastRotate = rotate
        self._adjustSpeed()

    def stop(self):
        self._lastTranslate = 0
        self._lastRotate = 0
        return self._set(Scribbler.SET_MOTORS_OFF)

    def forward(self, speed=1, interval=0):
        self.move(speed, 0)
        time.sleep(interval)
        self.stop()

    def backward(self, speed=1, interval=0):
        self.move(-speed, 0)
        time.sleep(interval)
        self.stop()

    def turn_left(self, speed=1, interval=0):
        retval = self.move(0, speed)
        time.sleep(interval)
        self.stop()
        return retval

    def turn_right(self, speed=1, interval=0):
        retval = self.move(0, -speed)
        time.sleep(interval)
        self.stop()
        return retval

    def motors(self, left, right):
        trans = (right + left) / 2.0
        rotate = (right - left) / 2.0
        return self.move(trans, rotate)

    def play_song(self, song, wholeNoteDuration=0.545):
        """ Plays a song [(freq, [freq2,] duration),...] """
        # 1 whole note should be .545 seconds for normal
        for tup in song:
            self.play_note(tup, wholeNoteDuration)

    def play_note(self, tup, wholeNoteDuration=0.545):
        if len(tup) == 2:
            (freq, dur) = tup
            self.beep(dur * wholeNoteDuration, freq)
        elif len(tup) == 3:
            (freq1, freq2, dur) = tup
            self.beep(dur * wholeNoteDuration, freq1, freq2)

    def take_picture(self):
        raw_img = self._read_image()
        im = Image.frombuffer(
            "L", (self.width, self.height), raw_img, decoder_name="raw"
        )
        im = im.rotate(180)

        return im
