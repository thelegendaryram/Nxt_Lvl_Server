import nuke
nodesMenu = nuke.menu('Nodes')
nodesMenu.addCommand('Transform/CardToTrack/CardToTrack', 'nuke.nodes.CardToTrack2()',icon='my.png')
nodesMenu.addCommand('Transform/CardToTrack/CProject', 'nuke.createNode(\'CProject2\')',icon='CornerPin.png')
nodesMenu.addCommand('Transform/CardToTrack/TProject', 'nuke.createNode(\'TProject2\')',icon='Transform.png')
 

