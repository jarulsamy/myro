from setuptools import find_packages
from setuptools import setup

from myro.version import __VERSION__

setup(
    name="myro",
    version=__VERSION__,
    packages=find_packages(),
    install_requires=["pyserial"],
    author="Joshua Arulsamy",
    author_email="joshua.gf.arul@gmail.com",
    description="A robot communication library for Scribbler / Scribbler 2",
    url="https://github.com/jarulsamy/myro",
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        "Development Status :: 4 - Beta",
        # Define that your audience are developers
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        # Specify which pyhton versions that you want to support
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
