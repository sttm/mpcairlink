#!/usr/bin/env python3
"""Regenerate native MPC AirLink UI and preview images."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("make_skin.py")),run_name="__main__")
