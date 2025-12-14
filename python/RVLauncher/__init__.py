"""
RV Launcher – Standalone Nukepedia Package
"""
import os, sys

PACKAGE_DIR = os.path.dirname(__file__)
if PACKAGE_DIR not in sys.path:
    sys.path.append(PACKAGE_DIR)

import rv_launcher
