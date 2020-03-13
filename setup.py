# -*- coding: utf-8 -*-
import setuptools

with open("myro/README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="myro",
    version="3.0.0",
    scripts=["myro/"],
    author="Joshua Arulsamy",
    author_email="joshua.gf.arul@gmail.com",
    description="A robot communication library for Scribbler / Scribbler 2",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jarulsamy/myro",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Licence :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
