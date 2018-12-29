# Myro

Myro is a library used to interface with various robots including the Scribbler and Scribbler 2. This package is only compatible with Python 2.7.

## Getting Started

This package should be available in the pip repository:

```
pip install myro
```

### Prerequisites

Myro requires `Pyserial`. The only compatible version is 2.3: 

```
pip install pyserial==2.3
```

### Connecting to Scribbler

Pair with the robot via bluetooth.
Locate the COM port (Windows) or run `ls /dev` (Mac/Linux).

Within a python file, to initalize a robot:
```
from myro import *
init("COMX")

# Test Movement
forward(1,1)
backward(1,1)
turnLeft(1,1)
turnRight(1,1)
```

## Authors

* **Joshua Arulsamy** - *Maintainer* - [JoshuaA9088](https://github.com/JoshuaA9088)

* **Other Contributors** - *There have been many other contrubutors, however, they were never documented. 
## License

This project is licensed under the MIT License

## Acknowledgments

* All members of the IPRE Calico Foundation

## FAQ

* I get an error from pyserial when attmepting to init()
    - This is likely due to an incorrect version of Pyserial. Ensure pyserial 2.3 is installed. 

* When attempting to init() I get: `Serial element not found... Replace if this continues`
    - This is likely due to an incorrect port number. If this error continues, re-pair wiht the robot forcing a different COM port. 