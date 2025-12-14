#----------------------------------------------------------------------------------------------------------
#
# AUTOMATICALLY GENERATED FILE TO BE USED BY W_HOTBOX
#
# NAME: Read
#
#----------------------------------------------------------------------------------------------------------

import nuke

def readWrite():
    sel = nuke.selectedNode()

    if sel.Class() == 'Write':
        file_path = sel['file'].getValue()
        read = nuke.createNode('Read', inpanel=False)
        read.setXpos(int(sel['xpos'].getValue() + 0))
        read.setYpos(int(sel['ypos'].getValue() + 110))
        read['file'].setValue(file_path)

        first_frame = int(nuke.Root()['first_frame'].getValue())
        last_frame = int(nuke.Root()['last_frame'].getValue())

        if file_path.lower().endswith('.mov'):
            adj_first = first_frame - 1000
            adj_last = last_frame - 1000

            read['first'].setValue(adj_first)
            read['last'].setValue(adj_last)
            read['origfirst'].setValue(adj_first)
            read['origlast'].setValue(adj_last)

            # Set frame_mode first
            read['frame_mode'].setValue(1)  # 0=expression, 1=start at, 2=offset

            # Defer setting frame to ensure UI update doesn't overwrite it
            nuke.executeDeferred(lambda: read['frame'].setValue(1000))

        else:
            read['first'].setValue(first_frame)
            read['last'].setValue(last_frame)
            read['origfirst'].setValue(first_frame)
            read['origlast'].setValue(last_frame)

        read['colorspace'].setValue(int(sel['colorspace'].getValue()))

    else:
        nuke.message("Please select a Write node.")
        snote = nuke.createNode('StickyNote')
        snote['label'].setValue('Please select Write node. Wrong node selected.')
        snote.setYpos(int(sel['ypos'].getValue() + 60))
        snote.setXpos(int(sel['xpos'].getValue() + 60))

readWrite()