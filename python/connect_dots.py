import nuke


def deselectAll():
    all_nodes = nuke.allNodes()
    for node in all_nodes:
        node.knob("selected").setValue(False)


def createDot_betweenNodes(xDir, yDir):
    selected_nodes = nuke.selectedNodes()
    deselectAll()

    if len(selected_nodes) != 2:
        nuke.message("Please select exactly two nodes.")
    else:
        input_node = None
        output_node = None
        input_connection = -1

        # Check if the nodes are directly connected
        for i in range(selected_nodes[0].inputs()):
            if selected_nodes[0].input(i) == selected_nodes[1]:
                input_connection = i
                input_node = selected_nodes[1]
                output_node = selected_nodes[0]
                break

        for i in range(selected_nodes[1].inputs()):
            if selected_nodes[1].input(i) == selected_nodes[0]:
                input_connection = i
                input_node = selected_nodes[0]
                output_node = selected_nodes[1]
                break

        if input_node is None or output_node is None:
            nuke.message("The selected nodes are not directly connected.")
        else:
            dot = nuke.createNode("Dot")

            input_node_xpos = input_node.xpos() + (input_node.screenWidth() / 2)
            input_node_ypos = input_node.ypos() + (input_node.screenHeight() / 2)

            output_node_xpos = output_node.xpos() + (output_node.screenWidth() / 2)
            output_node_ypos = output_node.ypos() + (output_node.screenHeight() / 2)

            if xDir == 1 and yDir == 0:
                dot.setXYpos(int(input_node_xpos - 6), int(output_node_ypos - 6))
                dot.setInput(0, input_node)
                output_node.setInput(input_connection, dot)
            elif xDir == 0 and yDir == 1:
                dot.setXYpos(int(output_node_xpos - 6), int(input_node_ypos - 6))
                dot.setInput(0, input_node)
                output_node.setInput(input_connection, dot)
            else:
                pass

            deselectAll()
            nodesToSelect = [input_node, output_node]
            for i in nodesToSelect:
                i.setSelected(True)


def connectNodesWithDots(xDir, yDir):
    nuke.connectNodes(False, False)
    createDot_betweenNodes(xDir, yDir)
