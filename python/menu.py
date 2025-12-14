import nuke
import os

main_menu = nuke.menu("Nuke")
nxt_menu = main_menu.addMenu("NXT_LVL")
python_menu = nxt_menu.addMenu("Python")




#  W_hotbox------------------------
import W_hotbox, W_hotboxManager
#----------------------------------


#  Connect Dots------------------------
import connect_dots

nuke.menu("Nuke").addCommand("@;Create Dot Upper", "connect_dots.createDot_betweenNodes(0,1)", "Alt+Shift+.", shortcutContext=dagContext)
nuke.menu("Nuke").addCommand("@;Create Dot Lower", "connect_dots.createDot_betweenNodes(1,0)", "Alt+.", shortcutContext=dagContext)
nuke.menu("Nuke").addCommand("@;Connect Nodes Upper", "connect_dots.connectNodesWithDots(0,1)", "Shift+Y", shortcutContext=dagContext)
nuke.menu("Nuke").addCommand("@;Connect Nodes Lower", "connect_dots.connectNodesWithDots(1,0)", "Alt+Y", shortcutContext=dagContext)


#  cardtotrack------------------------
nuke.pluginAddPath('./cardtotrack')


#  Rv Launcher------------------------
import rv_launcher

def icon(name):
    import os
    return os.path.join(os.path.dirname(__file__), "icons", name).replace("\\", "/")

#menu = nuke.toolbar("Nodes").addMenu("SmartTools")
python_menu.addCommand("🎞 Launch RV", "rv_launcher.launch_rv()", "Ctrl+Shift+Alt+Q")


# Stamps------------------------
nuke.pluginAddPath("stamps")

