import nuke
import rv_launcher

def icon(name):
    import os
    return os.path.join(os.path.dirname(__file__), "icons", name).replace("\\", "/")

menu = nuke.toolbar("Nodes").addMenu("SmartTools")
menu.addCommand("🎞 Launch RV", "rv_launcher.launch_rv()", "")
