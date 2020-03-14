# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

setup(
    name="myro",
    version="3.0.0",
    packages=find_packages(),
    install_requires=["pyserial"],
    author="Joshua Arulsamy",
    author_email="joshua.gf.arul@gmail.com",
    description="A robot communication library for Scribbler / Scribbler 2",
    url="https://github.com/jarulsamy/myro",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Licence :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
