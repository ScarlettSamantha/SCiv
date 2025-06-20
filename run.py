#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from sciv.__main__ import bootstrap  # noqa: E402

if __name__ == "__main__":
    bootstrap()
