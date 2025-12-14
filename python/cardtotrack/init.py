
if nuke.NUKE_VERSION_MAJOR > 15:
	nuke.pluginAddPath("./nuke16_and_higher")
else:
	nuke.pluginAddPath("./nuke15_and_lower")

