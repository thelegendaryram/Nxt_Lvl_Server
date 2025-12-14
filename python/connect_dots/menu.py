import nuke

nuke.pluginAddPath("./connect_dots")

shelf = nuke.menu("Nuke").addMenu("connect dots")

# create dot nodes in an angle
import connect_dots

shelf.addCommand(
    "create dot/upper", "connect_dots.createDot_betweenNodes(0,1)", "Alt+Shift+."
)
shelf.addCommand(
    "create dot/lower", "connect_dots.createDot_betweenNodes(1,0)", "Alt+."
)

# connect nodes with a dot node
shelf.addCommand(
    "connect Nodes/upper", "connect_dots.connectNodesWithDots(0,1)", "Shift+Y"
)
shelf.addCommand(
    "connect Nodes/lower", "connect_dots.connectNodesWithDots(1,0)", "Alt+Y"
)
