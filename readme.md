# Myro

Myro is a library used to interface with the Scribbler and Scribbler 2 robots.

Disclaimer: This package was formally only supported by Python &lt;= 2.7. Now, some portions, mostly related to Scribbler and Scribbler 2, are compatible with **Python 3.6+**.

## Getting Started

This package should be available in the pip repository:

    pip install myro

Or just install using the `src/setup.py` file.

    pip install .

### Connecting to Scribbler

Pair with the robot via bluetooth.
Locate the COM port (Windows) or run `ls /dev` (Mac/Linux).

Within a python file, to initalize a robot:

    from myro import *
    init("COMX")
    # Test Movement
    forward(1,1)
    backward(1,1)
    turnLeft(1,1)
    turnRight(1,1)

## FAQ

-   When attempting to init() I get: `Serial element not found... Replace if this continues`
    -   This is likely due to an incorrect port number. If this error continues, re-pair wiht the robot forcing a different COM port.
