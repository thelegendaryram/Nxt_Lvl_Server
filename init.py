# init.py
import nuke
import os

ROOT = os.path.dirname(__file__)

nuke.pluginAddPath(ROOT)
nuke.pluginAddPath(os.path.join(ROOT, "gizmos"))
nuke.pluginAddPath(os.path.join(ROOT, "toolsets"))
nuke.pluginAddPath(os.path.join(ROOT, "python"))
nuke.pluginAddPath(os.path.join(ROOT, "icons"))
nuke.pluginAddPath(os.path.join(ROOT, "plugins"))
nuke.pluginAddPath(os.path.join(ROOT, "cattery"))


