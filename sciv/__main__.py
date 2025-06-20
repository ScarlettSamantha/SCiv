#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
os.chdir(SCRIPT_DIR)


def bootstrap():
    from game import OpenCiv

    app = OpenCiv(debug=True)

    try:
        app.run()
    except (SystemExit, AssertionError):
        print("Goodbye :-)")


if __name__ == "__main__":
    bootstrap()
