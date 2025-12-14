'''
CardToTrack is a nuke group designed to help extract position of the object in 3D space
and represent it as corner pin in a screen space.
Optimized to work with Nuke15 and lower
'''

__author__ = "Alexey Kuchinski"
__copyright__ = "Copyright 2023, Alexey Kuchinski"
__credits__ = ["Adrian Pueyo", "Helge Stang", "Eyal Sirazi", "Marco Meyer", "Tony Lyons", "Mark Joey Tang", "Pete O'Connell", "Ivan Busquets","Ben Dickson","Trixter Folks!!!!!"]
__version__ = "9.2"
__email__ = "lamakaha@gmail.com"
__status__ = "Perpetual Beta"




import threading
import time
import nuke
import math
import re

#######################################################################################
# Main functions of the Group


def set_ref_frame():
    '''
    Set reference frame will find x/y position and freeze the camera to look at this position, 
    later it will be used to find 3d position while we do move an Axis to or from look at target
    '''
    C2Tgroup = nuke.thisGroup()
    C2Tgroup['Zfind'].setValue(0)
    C2Tgroup.begin()
    #nuke.toNode("Switch1")['disable'].setValue(0)
    nuke.toNode("ScanlineRender1")['disable'].setValue(0)
    nuke.toNode("StabFrameHold")['first_frame'].setValue(C2Tgroup['refFrame'].value())
    if C2Tgroup['S'].value() == 1:
        C2Tgroup['Stabilize'].execute()
        #n = a.input(1) 
    camera_connected = C2Tgroup.input(1)
    bg_connected = C2Tgroup.input(0)

    if not camera_connected:
        nuke.message('Could you please connect some Camera if you do not mind.')
    if not bg_connected:
        nuke.message('No connectd BG footage, will use the project resolution instead')

    # C2Tgroup.end()       
    # C2Tgroup.begin()

    nuke.toNode("NoOp1")['pick'].execute()
    C2Tgroup['refFrame'].setValue(nuke.frame())
    nuke.toNode("Switch")['which'].setValue(0)

    r=nuke.toNode("Perspective")
    r.setSelected(False)
    r.hideControlPanel()
    r['rotate'].setValue(0)
    r['translate'].setValue(0)
    r['scaling'].setValue(1)
    r['uniform_scale'].setValue(C2Tgroup['scene'].value())
    C2Tgroup.end()
        
    if C2Tgroup['extraHelper'].value() in [0]:
        C2Tgroup['findZ'].clearFlag(1)
        for one in ['happyGroup','goGroup','goGroup']:
            C2Tgroup[one].setFlag(1)
    if C2Tgroup['extraHelper'].value() in [1,2,3,4]:
        C2Tgroup['Adjust'].execute()


def stabilize():
    '''
    add stabilization to card in order to find its position in 3d space in easier way
    '''
    node = nuke.thisGroup() 
    t = node['S']

    if t.value() == 0:
       nuke.thisKnob().setLabel('<font color="Red"><b>Stabilized')
       t.setValue(1)
       nuke.toNode("StabFrameHold")['disable'].setValue(0)
       nuke.toNode("StabFrameHold")['first_frame'].setValue(node['refFrame'].value())
       nuke.toNode("StabRef")['first_frame'].setValue(node['refFrame'].value())
       nuke.toNode("StabSwitch")['disable'].setValue(0)
    else:
       nuke.thisKnob().setLabel('Stabilize')
       t.setValue(0)
       node['HighPass'].setValue(0)
       node['HighPass_1'].setValue(0)
       nuke.toNode("StabFrameHold")['disable'].setValue(1)
       nuke.toNode("StabSwitch")['disable'].setValue(1)


def happy():
    ''' 
    bake position we did find in previous step in temporary Axis, this axis will be later used
    to get corner pin from 3d position.
    '''
    C2Tgroup=nuke.thisNode()
    nuke.toNode("Switch")['which'].setValue(1)
    axisNode = nuke.toNode('Z_finder')
    perspective_axis = nuke.toNode('Perspective')
    refFrame = C2Tgroup['refFrame'].value()
    matrixVal = axisNode['world_matrix'].valueAt(refFrame)

    perspective_axis['translate'].setValue([matrixVal[3],matrixVal[7],matrixVal[11]])
    #nuke.show((perspective_axis), True)
    perspective_axis.setSelected(True)
    r=nuke.toNode("look_at_Axis")
    r.setSelected(False)
    r.hideControlPanel() 

    if C2Tgroup['S'].value() == 1:
        C2Tgroup['Stabilize'].execute()
        C2Tgroup['HighPass'].setValue(0)
    if C2Tgroup['extraHelper'].value() in [0,2,3,4]:
        C2Tgroup['findZ'].setFlag(1)
        C2Tgroup['happyGroup'].clearFlag(1)
        C2Tgroup['goGroup'].clearFlag(1)
    C2Tgroup['setGroup'].setFlag(1)


def show_grid_axis():
    ''' 
    set selected perspective axis in order to show in in viewer
    '''
    C2Tgroup=nuke.thisNode()
    with C2Tgroup:
        perspective_axis = nuke.toNode('Perspective')
        perspective_axis.setSelected(True)   
        nuke.show(perspective_axis)


def go():
    ''' 
    Build a Tab and knobs, extract corner pin information and set in in corner pin knobs, 
    save the card information as well
    '''

    import nuke
    import math

    C2Tgroup=nuke.thisNode()

    modes = ['MatchMove','3D Locator(card or axis)','Geometry',"WorldPosition","Deep"]
    mode = modes[int(C2Tgroup['extraHelper'].value())]
    if mode == '3D Locator(card or axis)':
        if C2Tgroup.input(2):
            axisNode = C2Tgroup.input(2)
            try:
                if 'world_matrix' in axisNode.knobs():
                    axis_matrix = axisNode['world_matrix']
                else:
                    axis_matrix = axisNode['matrix']
            except:
                nuke.message("Check that you are connected directly and do not have\na dot or any other node between your Locator and CardToTrack group.\nSupported nodes are an Axis,Card or any Other 3D node with world_matrix")
                return
        else:
            nuke.message("It looks like you did not connect an Axis or a Card to the <b>Extra</b> input.")
            return




    if C2Tgroup['S'].value() == 1:
        C2Tgroup['Stabilize'].execute()
        C2Tgroup['HighPass'].setValue(0)
    for one in ['happyGroup','C2T','scene_settings','cameraExchange','goGroup','findZ']:
        C2Tgroup[one].setFlag(1)
    first_frame_v, last_frame_v = check_first_last_frame(C2Tgroup)
    x=int(C2Tgroup['xpos'].value())
    y=int(C2Tgroup['ypos'].value())

    with C2Tgroup:
        nuke.toNode("Perspective").setSelected(False)


    with nuke.Root():


        def C2T(dialog):

            # initialize tool values for auto-creation
            ref = int(nuke.frame())
            first = first_frame_v
            last = last_frame_v
            bg = C2Tgroup.input(0)
            recalculate = False

            if dialog == True:
                #panel
                panel = nuke.Panel("C2T")
                panel.addSingleLineInput("label:", "")
                panel.addSingleLineInput("firstFrame:", str(first))
                panel.addSingleLineInput("lastFrame:", str(last))
                panel.addSingleLineInput("ref frame:", str(ref))
                if panel.show():
                    first = int(panel.value("firstFrame:"))
                    last = int(panel.value("lastFrame:"))
                    ref = int(panel.value("ref frame:"))
                    if ref>last or ref<first:
                        ref = first
                    raw_label = panel.value("label:")
                    label = re.sub(r'[^\w]', '_', raw_label)

                else:
                    nuke.message('canceled')
                    nuke.delete(bg) # clean the mess up
                    return
            else:
                print ('no dialog, use auto-created input values')
            
            # Create a TabKnob and all content
            if '_X_'+label not in C2Tgroup.knobs(): # if we do create this object first time we will create knobs

                tab_knob        = nuke.Tab_Knob('_X_'+label, label)
                refFrame        = nuke.Int_Knob('ReferenceFrame_X_'+label,'Reference Frame')
                refFrame.setTooltip("Reference frame is a frame in which there is not difference between 'from' and 'to' in a cornerpin. It can be changed later in CProject settings")
                firstFrame      = nuke.Int_Knob('FirstFrame_X_'+label, 'First Frame')
                firstFrame.setTooltip("First frame of extracted animation")
                lastFrame       = nuke.Int_Knob('LastFrame_X_'+label, 'Last Frame')
                lastFrame.setTooltip("Last frame of extracted animation")
                baked           = nuke.Boolean_Knob('Baked_X_'+label, "Baked", True)
                baked.setTooltip("If enabled nodes that will be created will have the animation baked, otherwise it will be linked to the CardToTrack node. Important - it is currently impossible to link roto shape")
                card            = nuke.PyScript_Knob('Card_X_'+label, '3d object')
                card.setTooltip("Create a Card or other primitive")
                corner          = nuke.PyScript_Knob('CornerPin_X_'+label, 'CornerPin')
                corner.setTooltip("Create CProject node, which is a simple CornerPin node with additional functionalities")
                roto            = nuke.PyScript_Knob('Roto_X_'+label, 'Roto')
                roto.setTooltip("Create tracked Roto Node, tracking information is saved in the Matrix on the root level of the roto")
                transform       = nuke.PyScript_Knob('Transform_X_'+label, 'Transform')
                transform.setTooltip("Create a tracked Transform node with translate information only (similar to one point tracking)")
                translate       = nuke.XYZ_Knob('Translate_X_'+label, 'translate')
                rotate          = nuke.XYZ_Knob('Rotate_X_'+label, 'rotate')
                scale           = nuke.XYZ_Knob('Scale_X_'+label, 'scale')
                uniform_scale   = nuke.Double_Knob('Uniform_scale_X_'+label, 'uniform scale')
                to1             = nuke.XY_Knob('to1_X_'+label, 'to1')
                to2             = nuke.XY_Knob('to2_X_'+label,'to2')
                to3             = nuke.XY_Knob('to3_X_'+label, 'to3')
                to4             = nuke.XY_Knob('to4_X_'+label, 'to4')
                translateT      = nuke.XY_Knob('TranslateT_X_'+label, 'translate')
                centerT         = nuke.XY_Knob('centerT_X_'+label, 'center')
                matrix          = nuke.Array_Knob('matrix_X_'+label, 'matrix',16)
                bGCard          = nuke.Tab_Knob('CardKnobs_X_'+label, 'card knobs', nuke.TABBEGINCLOSEDGROUP)
                bGMatrix        = nuke.Tab_Knob('MatrixKnobs_X_'+label, 'matrix knobs', nuke.TABBEGINCLOSEDGROUP)
                bGTransform     = nuke.Tab_Knob('TransformKnobs_X_'+label, 'transform knobs', nuke.TABBEGINCLOSEDGROUP)
                bGCorner        = nuke.Tab_Knob('CornerPinKnobs_X_'+label, 'corner pin knobs', nuke.TABBEGINCLOSEDGROUP)
                eGMatrix        = nuke.Tab_Knob('MatrixKnobs_close_X_'+label, None, nuke.TABENDGROUP)
                eGTransform     = nuke.Tab_Knob('TransformKnobs_close_X_'+label, None, nuke.TABENDGROUP)
                eGCorner        = nuke.Tab_Knob('CornerPinKnobs_close_X_'+label, None, nuke.TABENDGROUP)
                eGCard          = nuke.Tab_Knob('CardKnobs_close_X_'+label, None, nuke.TABENDGROUP)
                delete            = nuke.PyScript_Knob('Delete_X_'+label, "<b><font color=#A40000>Delete Tab")

                delete.setTooltip("Delete Current Tab and all its knobs ")

                flags = [card, corner, roto, transform]
                for one in flags:
                    one.clearFlag(nuke.STARTLINE)

                card.setFlag(nuke.STARTLINE)

                knobs = [tab_knob, refFrame, firstFrame, lastFrame, 
                        card, corner, roto, transform,
                        baked,
                        bGCard, translate, rotate, scale, uniform_scale, eGCard, 
                        bGCorner, to1, to2, to3, to4, eGCorner,
                        bGTransform, translateT, centerT, eGTransform , 
                        bGMatrix, matrix, eGMatrix, delete]

                for one in knobs:
                    C2Tgroup.addKnob(one)

            else:

                tab_knob        = C2Tgroup['_X_'+label]
                refFrame        = C2Tgroup['ReferenceFrame_X_'+label]
                firstFrame      = C2Tgroup['FirstFrame_X_'+label]
                lastFrame       = C2Tgroup['LastFrame_X_'+label]
                baked           = C2Tgroup['Baked_X_'+label]
                card            = C2Tgroup['Card_X_'+label]
                corner          = C2Tgroup['CornerPin_X_'+label]
                roto            = C2Tgroup['Roto_X_'+label]
                transform       = C2Tgroup['Transform_X_'+label]
                translate       = C2Tgroup['Translate_X_'+label]
                rotate          = C2Tgroup['Rotate_X_'+label]
                scale           = C2Tgroup['Scale_X_'+label]
                uniform_scale   = C2Tgroup['Uniform_scale_X_'+label]
                to1             = C2Tgroup['to1_X_'+label]
                to2             = C2Tgroup['to2_X_'+label]
                to3             = C2Tgroup['to3_X_'+label]
                to4             = C2Tgroup['to4_X_'+label]
                translateT      = C2Tgroup['TranslateT_X_'+label]
                centerT         = C2Tgroup['centerT_X_'+label]
                matrix          = C2Tgroup['matrix_X_'+label]

 
            refFrame.setValue(ref)
            firstFrame.setValue(int(first))
            lastFrame.setValue(int(last))
            card.setValue('import card_to_track; card_to_track.card_code()')
            corner.setValue('import card_to_track; card_to_track.corner_code()')
            roto.setValue('import card_to_track; card_to_track.roto_code()')
            transform.setValue('import card_to_track; card_to_track.transform_code()')
            delete.setValue('import card_to_track; card_to_track.delete_tab()')

            
            cardknobs = [translate, rotate, scale, uniform_scale]
            toes = [to1, to2, to3, to4]

            # # run with threading
            global stop_event 
            stop_event = threading.Event()
            threading.Thread(target=calculate_corner_pin, kwargs=dict(C2Tgroup=C2Tgroup,label=label,recalculate = recalculate)).start()
            while not stop_event.is_set():
                time.sleep(0.02)


            # point expressions of internal nodes back to 'Perspective' node, not able to make it threaded.
            with C2Tgroup:
                am = nuke.toNode('aM')
                a1 = nuke.toNode('a1')
                a2 = nuke.toNode('a2')
                a3 = nuke.toNode('a3')
                a4 = nuke.toNode('a4')
                am['translate'].setExpression('parent.Perspective.translate')
                am['rotate'].setExpression('parent.Perspective.rotate')

                a1['translate'].setExpression('-0.5*Perspective.uniform_scale*Perspective.scaling.x',0)
                a1['translate'].setExpression('input0.pixel_aspect*-0.5*Perspective.uniform_scale*Perspective.scaling.y',1)

                a2['translate'].setExpression('0.5*Perspective.uniform_scale*Perspective.scaling.x',0)
                a2['translate'].setExpression('input0.pixel_aspect*-0.5*Perspective.uniform_scale*Perspective.scaling.y',1)

                a3['translate'].setExpression('0.5*Perspective.uniform_scale*Perspective.scaling.x',0)
                a3['translate'].setExpression('input0.pixel_aspect*0.5*Perspective.uniform_scale*Perspective.scaling.y',1)

                a4['translate'].setExpression('-0.5*Perspective.uniform_scale*Perspective.scaling.x',0)
                a4['translate'].setExpression('input0.pixel_aspect*0.5*Perspective.uniform_scale*Perspective.scaling.y',1)


            #kill animation in all knobs that not animated, not able to make it threaded, it crashes nuke.
            kill_animation([to1, to2, to3, to4, translate, rotate, scale, uniform_scale])

            #find if the curve has issues
            issues = []
            for one in toes:
                issue = check_curve(one,first,last,ref)
                issues.append(issue)

            if True in issues:
                if nuke.ask("Perspective problem detected! would you like to fix it? \n\nYour card did pass the Camera backplate, this causes the track to break, we can try and fix the problem. If our fix will not succeed you should use a bit smaller card so corners of the card will not cross the camera so fast.\n\nYou can just move your card further away from the camera - remember it is just a plane anyway!"):
                    for one in issues:
                        if one == True:
                            knob = toes[issues.index(one)]
                            fix_curves(knob,first,last,ref)
            tab_knob.setFlag(0)


        C2T(True)


def recalculate_camera():
    '''
    Recalculate card to track tabs in case camera was updated
    '''
    recalculate = True
    C2Tgroup=nuke.thisNode()
    bg = C2Tgroup.input(0)
    cardTabs = []

    #find all cards we already precalculated
    for label in C2Tgroup.knobs():
        if label.startswith('_X_'):
            cardTabs.append(label.rpartition('_X_')[2])

    #create progress bar.
    iterations = len(cardTabs)
    if iterations > 1:
        progress_bar = nuke.ProgressTask("Frame")

    for label in cardTabs:
        with nuke.Root():

            global stop_event

            refFrame        = C2Tgroup['ReferenceFrame_X_'+label]
            firstFrame      = C2Tgroup['FirstFrame_X_'+label]
            lastFrame       = C2Tgroup['LastFrame_X_'+label]
            translate       = C2Tgroup['Translate_X_'+label]
            rotate          = C2Tgroup['Rotate_X_'+label]
            scale           = C2Tgroup['Scale_X_'+label]
            uniform_scale   = C2Tgroup['Uniform_scale_X_'+label]
            to1             = C2Tgroup['to1_X_'+label]
            to2             = C2Tgroup['to2_X_'+label]
            to3             = C2Tgroup['to3_X_'+label]
            to4             = C2Tgroup['to4_X_'+label]
            translateT      = C2Tgroup['TranslateT_X_'+label]
            matrix          = C2Tgroup['matrix_X_'+label]


            ref = refFrame.value()
            first,last = int(firstFrame.value()), int(lastFrame.value())

            # to1x,to1y = to1.valueAt(ref)[0],to1.valueAt(ref)[1]
            # to2x,to2y = to2.valueAt(ref)[0],to2.valueAt(ref)[1]
            # to3x,to3y = to3.valueAt(ref)[0],to3.valueAt(ref)[1]
            # to4x,to4y = to4.valueAt(ref)[0],to4.valueAt(ref)[1]
            # to_before_x = to1x+to2x+to3x+to4x
            # to_before_y = to1y+to2y+to3y+to4y

            # recalculate cornerpin threaded
            stop_event = threading.Event()
            threading.Thread(target=calculate_corner_pin, kwargs=dict(C2Tgroup=C2Tgroup,label=label,recalculate=recalculate)).start()
            while not stop_event.is_set():
                time.sleep(0.02)

            # to1x,to1y = to1.valueAt(ref)[0],to1.valueAt(ref)[1]
            # to2x,to2y = to2.valueAt(ref)[0],to2.valueAt(ref)[1]
            # to3x,to3y = to3.valueAt(ref)[0],to3.valueAt(ref)[1]
            # to4x,to4y = to4.valueAt(ref)[0],to4.valueAt(ref)[1]
            # to_after_x = to1x+to2x+to3x+to4x
            # to_after_y = to1y+to2y+to3y+to4y

            # offset_x =  to_after_x - to_before_x
            # offset_y =  to_after_y - to_before_y
            # print (offset_x,offset_y)

            # recalculate transform threaded
            if translateT.isAnimated():
                stop_event = threading.Event()
                threading.Thread(target=calculate_translate, kwargs=dict(C2Tgroup=C2Tgroup,label=label)).start()
                while not stop_event.is_set():
                    time.sleep(0.02)


            # recalculate matrix threaded
            if matrix.isAnimated():
                stop_event = threading.Event()
                threading.Thread(target=calculate_matrix, kwargs=dict(C2Tgroup=C2Tgroup,label=label)).start()
                while not stop_event.is_set():
                    time.sleep(0.02)


            # point expressions of internal nodes back to 'Perspective' node, not able to make it threaded.
            with C2Tgroup:

                am = nuke.toNode('aM')
                am['translate'].setExpression('parent.Perspective.translate')
                am['rotate'].setExpression('parent.Perspective.rotate')

                a1 = nuke.toNode('a1')
                a1['translate'].setExpression('-0.5*Perspective.uniform_scale*Perspective.scaling.x',0)
                a1['translate'].setExpression('input0.pixel_aspect*-0.5*Perspective.uniform_scale*Perspective.scaling.y',1)

                a2 = nuke.toNode('a2')
                a2['translate'].setExpression('0.5*Perspective.uniform_scale*Perspective.scaling.x',0)
                a2['translate'].setExpression('input0.pixel_aspect*-0.5*Perspective.uniform_scale*Perspective.scaling.y',1)

                a3 = nuke.toNode('a3')
                a3['translate'].setExpression('0.5*Perspective.uniform_scale*Perspective.scaling.x',0)
                a3['translate'].setExpression('input0.pixel_aspect*0.5*Perspective.uniform_scale*Perspective.scaling.y',1)

                a4 = nuke.toNode('a4')
                a4['translate'].setExpression('-0.5*Perspective.uniform_scale*Perspective.scaling.x',0)
                a4['translate'].setExpression('input0.pixel_aspect*0.5*Perspective.uniform_scale*Perspective.scaling.y',1)


            #kill animation in all knobs that not animated, not able to make it threaded, it crashes nuke.
            kill_animation([to1, to2, to3, to4,translate, rotate, scale, uniform_scale])


        # display progress bar
        if iterations > 1:
            if progress_bar.isCancelled():
                break
            percent1 = int(100*(float(cardTabs.index(label)) / (iterations-1)))
            progress_bar.setProgress(percent1)
            progress_bar.setMessage("Recalculating "+label)
            time.sleep(0.1)
    # delete progress bar and display success message
    if iterations > 1:
        del progress_bar
        #nuke.message("It is Done my friend, all Tabs are recalculated!!!!!")
    else:
        pass
        #nuke.message("It is Done my friend, all Tabs are recalculated!!!!!")


def select_associated_nodes():
    '''
    Select all nodes created by this Group.
    '''
    C2Tgroup = nuke.thisGroup()
    group_name = C2Tgroup.name()
    cardTabs = []

    #find all cards we already precalculated
    for label in C2Tgroup.knobs():
        if label.startswith('_X_'):
            cardTabs.append(label.rpartition('_X_')[2])


    with nuke.Root():
        nan = nuke.allNodes()
        
        for node in nan:
            node.setSelected(False)

        for node in nan:
            if 'card_to_track' in node.knobs() and "CardToTrack" not in node.name():
                if group_name+":" in node['card_to_track'].value():
                    node.setSelected(True)


def update_baked():

    '''
    Recalculate selected nodes to match updated camera.
    '''
    C2Tgroup = nuke.thisGroup()
    group_name = C2Tgroup.name()
    cardTabs = []

    #find all cards we already precalculated
    for label in C2Tgroup.knobs():
        if label.startswith('_X_'):
            cardTabs.append(label.rpartition('_X_')[2])


    with nuke.Root():
        c2t_nodes = nuke.selectedNodes()
        for node in c2t_nodes:
            identificator = node['card_to_track'].value()
            label = identificator.rpartition(": ")[2]
            nodetype = identificator.split(':')[1]

            if '_X_'+label not in C2Tgroup.knobs():
                nuke.message('looks like <b>'+node.name() +"</b> is not a part of the <b>" +C2Tgroup.name()+"</b> anymore.\nCould be you erased the tab with it?\nPlease deselect this node and run Update Selected Nodes again.")
                return
            if nodetype == 'card':
                if C2Tgroup['Translate_X_'+label].isAnimated():
                    node['translate'].copyAnimations(C2Tgroup['Translate_X_'+label].animations())
                else:
                    node['translate'].setValue(C2Tgroup['Translate_X_'+label].value())

                if C2Tgroup['Rotate_X_'+label].isAnimated():
                    node['rotate'].copyAnimations(C2Tgroup['Rotate_X_'+label].animations())
                else:
                    node['rotate'].setValue(C2Tgroup['Rotate_X_'+label].value())

                if C2Tgroup['Scale_X_'+label].isAnimated():
                    node['scaling'].copyAnimations(C2Tgroup['Scale_X_'+label].animations())
                else:
                    node['scaling'].setValue(C2Tgroup['Scale_X_'+label].value())

                if C2Tgroup['Uniform_scale_X_'+label].isAnimated():
                    node['uniform_scale'].copyAnimations(C2Tgroup['Uniform_scale_X_'+label].animations())
                else:
                    node['uniform_scale'].setValue(C2Tgroup['Uniform_scale_X_'+label].value())

            elif nodetype == 'cornerpin':

                node['to1'].copyAnimations(C2Tgroup['to1_X_'+label].animations())
                node['to2'].copyAnimations(C2Tgroup['to2_X_'+label].animations())
                node['to3'].copyAnimations(C2Tgroup['to3_X_'+label].animations())
                node['to4'].copyAnimations(C2Tgroup['to4_X_'+label].animations())


            elif nodetype == 'transform':
                if C2Tgroup['TranslateT_X_'+label].isAnimated():
                    node['translate'].copyAnimations(C2Tgroup['TranslateT_X_'+label].animations())
                    #tr['center'].copyAnimations(centerT.animations())
                else:
                    node['translate'].setValue(C2Tgroup['TranslateT_X_'+label].value())
                node['center'].setValue(C2Tgroup['centerT_X_'+label].value())

            elif nodetype == 'roto':
                nuke.show(node)
                node['transform_matrix'].copyAnimations(C2Tgroup['matrix_X_'+label].animations())
                node['curves'].changed()


#######################################################################################
# Helpers, secondary functions used in other functions


def check_first_last_frame(C2Tgroup):

    '''
    check if camera has animation and if yes collect first and last frame of it
    '''
    with nuke.Root():
        how = C2Tgroup['extraHelper'].value()
        try:
            with C2Tgroup:
                # get first and last animation frames of camera
                tr = nuke.toNode('DummyCam')['translate'].getKeyList()
                first_frame_v = min(tr)
                last_frame_v = max(tr)

            if how == 1:
                # try to get animation from animated card or an axis and take minimum and maximum from camera and card animation
                translateKeys = C2Tgroup.input(2)['translate'].getKeyList()
                first_frame_v = min([first_frame_v,min(translateKeys)])
                last_frame_v = max([last_frame_v,max(translateKeys)])


        except:
            first_frame_v = int(nuke.toNode('root')['first_frame'].value())
            last_frame_v = int(nuke.toNode('root')['last_frame'].value())


        if C2Tgroup['S'].value() == 1:   
            C2Tgroup['Stabilize'].execute()

        return first_frame_v, last_frame_v


def bake_expressions(knob, start, end, views=None):
    '''
    Bakes all expression-driven Array_Knob-derived knob components to keyframes
    over a given input frame range and list of views.
    'views': Optional list of views to bake. If omitted, all script views will
    be used.
    '''

    if views is None:
        views = nuke.views()
    elif not views:
        nuke.message('No views to bake')
        return
    elif not set(views).issubset(nuke.views()):
        nuke.message('Not all views in %s exist in script' % views)
        return



    for view in views:
        # There's currently no way to ask a knob if it has an
        # expression at a given view, so we have to check the
        # AnimationCurve objects for that. However, we can still
        # use knob.isAnimated() to partially optimize this.
        if knob.isAnimated(view=view):
            aSize = 1 if knob.singleValue(view) else knob.arraySize()
            for index in range(aSize):
                anim = knob.animation(index, view=view)
                if anim is None or anim.noExpression():
                    continue
                for f in range(start, end + 1):
                    #knob.setValueAt(anim.evaluate(f), f, index)
                    anim.setKey(f, anim.evaluate(f))
                knob.setExpression('curve', channel=index, view=view)
                # Even if the expression would have evaluated to a
                # constant (flat) curve, we can't tell until after
                # it has been baked and the expression is gone.
                if anim.constant():
                    knob.clearAnimated(index, view=view)


def offset_nodes(x,y):
    '''
    find how far newly created node should be created.
    '''
    allNodes = nuke.allNodes()
    for step in range(1,10):
        step = abs(10-step)
        for node in allNodes:
            if node['xpos'].value() == x+110*step and node['ypos'].value() == y:
                x = x+110*step
                break
    return x


def kill_animation(knobs):
    '''
    Kill animation in knobs if knobs are animated but animation is constant.
    '''
    for knob in knobs:
        if knob.isAnimated():
            aSize = 1 if knob.singleValue() else knob.arraySize()
            for index in range(aSize):
                anim = knob.animation(index)
                if anim and anim.constant():
                    knob.clearAnimated(index)


def check_curve(knob,first,last,ref):
    '''
    Check if a curve has Euler flip issue and warn about it
    Returns True if issue is detected and False if the curve is healthy
    '''
    import math
    problem = False
    timeline = ["beginning","end"]#######looping to fix stuff before and after ref frame
    for side in timeline:
        if side == "beginning":
            firstT = first
            lastT = last
        if side == "end":
            firstT = ref
            lastT = last

        curveXUp,curveXDown,curveYUp,curveYDown = 0,0,0,0
        fuckedFrames = []
        valsx = [];valSortx =[]
        valsy = [];valSorty =[]
        for i in range(firstT,lastT+1):
            valsx.append(knob.valueAt(i,0))
            valSortx.append(knob.valueAt(i,0))
            valsy.append(knob.valueAt(i,1))
            valSorty.append(knob.valueAt(i,1))
        valSortx.sort()
        valSorty.sort()
        minX = valSortx[0]
        maxX = valSortx[-1]
        minY = valSorty[0]
        maxY = valSorty[-1]
        if math.fabs(valsx.index(maxX)-valsx.index(minX)) == 1:
            problem = True
    return problem


def fix_curves(one,first,last,ref):
    '''
    If broken curve was detected, this function will attempt to fix it, it is old ugly code, but it somehow works
    and i do not want to touch it anymore. Just believe - it works.

    '''

    import math
    problem = 0
    timeline = ["beginning","end"]#######looping to fix stuff before and after ref frame
    lastB = last
    firstB = first
    for side in timeline:
        if side == "beginning":
            last = ref
        if side == "end":
            first = ref
            last = lastB
        curveXUp,curveXDown,curveYUp,curveYDown = 0,0,0,0
        fuckedFrames = []
        valsx = [];valSortx =[]
        valsy = [];valSorty =[]
        for i in range(first,last+1):
            valsx.append(one.valueAt(i,0))
            valSortx.append(one.valueAt(i,0))
            valsy.append(one.valueAt(i,1))
            valSorty.append(one.valueAt(i,1))
        valSortx.sort()
        valSorty.sort()
        minX = valSortx[0]
        maxX = valSortx[-1]
        minY = valSorty[0]
        maxY = valSorty[-1]
        if math.fabs(valsx.index(maxX)-valsx.index(minX)) == 1:
            problem = 1
            if valsx.index(maxX)-valsx.index(minX) < 0:    ###############checking if the curve going up or down
                curveXUp = 1
            else:
                curveXDown = 1
            if valsy.index(maxY)-valsy.index(minY) < 0:    ###############checking if the curve going up or down
                curveYUp = 1
            else:
                curveYDown = 1
            if valsx.index(maxX)+first > ref:                                  ##### kill tail X
                if curveXDown == 1: ##### curve X is going down####################################################################################FIXEDforEnd
                    lastGoodX= one.valueAt(valsx.index(minX)+first,0)
                    prelastGoodX= one.valueAt(valsx.index(minX)+first-1,0)
                    diffX= abs(lastGoodX) - abs(prelastGoodX)
                    offsetX = abs(lastGoodX)+maxX+diffX*2
                    for i in range(valsx.index(maxX)+first,last+1):
                        val = one.valueAt(i)[0]
                        one.setValueAt(val-offsetX,i,0)
                if curveXUp == 1: ##### curve X is going up####################################################################################FIXEDforEnd
                    lastGoodX = one.valueAt(valsx.index(maxX)+first,0) 
                    prelastGoodX= one.valueAt(valsx.index(maxX)+first-1,0) 
                    diffX= abs(lastGoodX)- abs(prelastGoodX)
                    offsetX= maxX+abs(minX)+diffX*2
                    for i in range(valsx.index(minX)+first,last+1):
                        val = one.valueAt(i)[0]
                        one.setValueAt(val+offsetX,i,0)
            if valsy.index(maxY)+first > ref:                                  ##### kill tail Y
                if curveYDown == 1: ##### curve Y is going down#####################################################################################FIXEDforEnd
                    lastGoodY= one.valueAt(valsy.index(minY)+first,1)
                    prelastGoodY= one.valueAt(valsy.index(minY)+first-1,1)
                    diffY= abs(lastGoodY) - abs(prelastGoodY) 
                    offsetY = abs(lastGoodY)+maxY+diffY*2
                    for i in range(valsy.index(maxY)+first,last+1):
                        val = one.valueAt(i)[1]
                        one.setValueAt(val-offsetY,i,1)
                if curveYUp == 1: ##### curve Y is going up####################################################################################FIXEDforEnd
                    lastGoodY = one.valueAt(valsy.index(maxY)+first,1) 
                    prelastGoodY= one.valueAt(valsy.index(maxY)+first-1,1) 
                    diffY=abs(lastGoodY) - abs(prelastGoodY) 
                    offsetY= maxY+abs(minY)+diffY*2
                    for i in range(valsy.index(minY)+first,last+1):
                        val = one.valueAt(i)[1]
                        one.setValueAt(val+offsetY,i,1)
            if valsx.index(maxX)+first < ref:                                  ##### kill head X-------------------------------------------------------------------------------------
                if curveXDown == 1: ##### curve X is going down#####################################################################################FIXEDforBeginning
                    firstGoodX= one.valueAt(valsx.index(maxX)+first,0)
                    prefirstGoodX= one.valueAt(valsx.index(maxX)+first+1,0)
                    diffX= abs(firstGoodX) - abs(prefirstGoodX) 
                    offsetX = abs(firstGoodX)+abs(minX)+diffX*2
                    for i in range(first,valsx.index(maxX)+first):
                        val = one.valueAt(i)[0]
                        one.setValueAt(val+offsetX,i,0)
                if curveXUp == 1: ##### curve X is going up#####################################################################################FIXEDforBeginning
                    firstGoodX = one.valueAt(valsx.index(minX)+first,0) 
                    prefirstGoodX= one.valueAt(valsx.index(minX)+first+1,0) 
                    diffX= abs(firstGoodX) - abs(prefirstGoodX) 
                    offsetX= abs(firstGoodX)+maxX+diffX*2
                    for i in range(first,valsx.index(minX)+first):
                        val = one.valueAt(i)[0]
                        one.setValueAt(val-offsetX,i,0)
            if valsy.index(maxY)+first < ref:                                  ##### kill head Y
                if curveYDown == 1: ##### curve Y is going down#####################################################################################FIXEDforBeginning
                    firstGoodY = one.valueAt(valsy.index(maxY)+first,1)
                    prefirstGoodY =  one.valueAt(valsy.index(maxY)+first+1,1)
                    diffY =  abs(firstGoodY) - abs(prefirstGoodY)
                    offsetY =  abs(firstGoodY)+abs(minY)+diffY*2
                    for i in range(first,valsy.index(maxY)+first):
                        val = one.valueAt(i)[1]
                        one.setValueAt(val+offsetY,i,1)
                if curveYUp == 1: ##### curve Y is going up#####################################################################################FIXEDforBeginning
                    firstGoodY = one.valueAt(valsy.index(minY)+first,1)
                    prefirstGoodY = one.valueAt(valsy.index(minY)+first+1,1)
                    diffY = abs(firstGoodY) - abs(prefirstGoodY)
                    offsetY = abs(firstGoodY)+maxY+diffY*2
                    for i in range(first,valsy.index(minY)+first):
                        val = one.valueAt(i)[1]
                        one.setValueAt(val-offsetY,i,1)


def delete_tab():
    '''
    deleting all knobs of stecific tab
    '''
    if nuke.ask("This will delete currect Tab and all nodes inside of it\nAre you very sure you want to do so?\n"):
        node = nuke.thisGroup()
        tab_knob_name = nuke.thisKnob().name().replace('Delete','')
        tabs = ["MatrixKnobs","TransformKnobs","CornerPinKnobs","CardKnobs",
                "MatrixKnobs_close","TransformKnobs_close","CornerPinKnobs_close","CardKnobs_close"]
        in_user_tab = False
        to_remove = []
        subgroups = []

        for n in range(node.numKnobs()):
            cur_knob = node.knob(n)

            # Track is-in-tab state
            if tab_knob_name in cur_knob.name():
                to_remove.append(cur_knob)

        #print (to_remove)
        for element in to_remove:
            if isinstance(element, nuke.Tab_Knob):
                to_remove.remove(element)
                to_remove.append(element)

        for k in to_remove:
            node.removeKnob(k)

        #Select first tab
        node['card_to_track'].setFlag(1)


#######################################################################################
# Functions that are calculating the values for Corner pin, transform node and Matrix


def calculate_corner_pin(C2Tgroup,label,recalculate):
    '''
    Take information from 3D scene and create 4 points, each point is corresponding
    to the corner of the card.
    '''
    modes = ['MatchMove','3D Locator(card or axis)','Geometry',"WorldPosition","Deep"]
    mode = modes[int(C2Tgroup['extraHelper'].value())]

    refFrame        = C2Tgroup['ReferenceFrame_X_'+label]
    first      = int(C2Tgroup['FirstFrame_X_'+label].value())
    last      = int(C2Tgroup['LastFrame_X_'+label].value())
    translate       = C2Tgroup['Translate_X_'+label]
    rotate          = C2Tgroup['Rotate_X_'+label]
    scale           = C2Tgroup['Scale_X_'+label]
    uniform_scale   = C2Tgroup['Uniform_scale_X_'+label]
    matrix          = C2Tgroup['matrix_X_'+label]

    cardknobs = [translate, rotate, scale, uniform_scale]
    toes = [C2Tgroup['to1_X_'+label], C2Tgroup['to2_X_'+label], C2Tgroup['to3_X_'+label], C2Tgroup['to4_X_'+label]]

    if recalculate:
        '''
        Recalculation of all tabs in case we do have update to our camera.
        '''
        
        with C2Tgroup:
            #point temporary expressions of internal nodes to newly generated Card knobs
            am = nuke.toNode('aM')
            am['translate'].setExpression('parent.'+'Translate_X_'+label)
            am['rotate'].setExpression('parent.'+'Rotate_X_'+label)

            all_scale_x = 'parent.Scale_X_'+label+'.x*parent.Uniform_scale_X_'+label
            all_scale_y = 'parent.Scale_X_'+label+'.y*parent.Uniform_scale_X_'+label
            a1 = nuke.toNode('a1')
            a1['translate'].setExpression('-0.5*'+all_scale_x,0)
            a1['translate'].setExpression('input0.pixel_aspect*-0.5*'+all_scale_y,1)

            a2 = nuke.toNode('a2')
            a2['translate'].setExpression('0.5*'+all_scale_x,0)
            a2['translate'].setExpression('input0.pixel_aspect*-0.5*'+all_scale_y,1)

            a3 = nuke.toNode('a3')
            a3['translate'].setExpression('0.5*'+all_scale_x,0)
            a3['translate'].setExpression('input0.pixel_aspect*0.5*'+all_scale_y,1)

            a4 = nuke.toNode('a4')
            a4['translate'].setExpression('-0.5*'+all_scale_x,0)
            a4['translate'].setExpression('input0.pixel_aspect*0.5*'+all_scale_y,1)

    else:

        '''
        Initial calculation and creation of Corner pin information based on the Camera and card position
        '''  
        if mode == '3D Locator(card or axis)':

            axisNode = C2Tgroup.input(2)
            if 'world_matrix' in axisNode.knobs():
                axis_matrix = axisNode['world_matrix']
            else:
                axis_matrix = axisNode['matrix']
            nuke.thisGroup().end()
            math_matrix = nuke.math.Matrix4()

            for tknob in cardknobs:
                tknob.setExpression('curve')


            scale_anim = scale.animations()
            rotate_anim = rotate.animations()
            translate_anim = translate.animations()
            

            # generate card transformation values based on matrix transformation
            for i in range(int(first), int(last+1)):
                k_time_aware = axis_matrix.getValueAt(i)
                for y in range(axis_matrix.height()):
                    for x in range(axis_matrix.width()):
                        math_matrix[x+(y*axis_matrix.width())] = k_time_aware[y + axis_matrix.width()*x]
            
                    transM =nuke.math.Matrix4(math_matrix)
                    transM.translationOnly()
                    rotM = nuke.math.Matrix4(math_matrix)
                    rotM.rotationOnly()
                    scaleM = nuke.math.Matrix4(math_matrix)
                    scaleM.scaleOnly()
                    scale = (scaleM.xAxis().x, scaleM.yAxis().y, scaleM.zAxis().z)
                    rot = rotM.rotationsZXY()
                    rotDegrees = ( math.degrees(rot[0]), math.degrees(rot[1]), math.degrees(rot[2]) )
                    trans = (transM[12], transM[13], transM[14])
                    for s in range(3):
                        scale_anim[s].setKey(i, scale[s])
                        rotate_anim[s].setKey(i, rotDegrees[s])
                        translate_anim[s].setKey(i, trans[s])


            #point temporary expressions of internal nodes to newly generated Card knobs
            with C2Tgroup:
                am = nuke.toNode('aM')
                a1 = nuke.toNode('a1')
                a2 = nuke.toNode('a2')
                a3 = nuke.toNode('a3')
                a4 = nuke.toNode('a4')

                am['translate'].setExpression('parent.'+'Translate_X_'+label)
                am['rotate'].setExpression('parent.'+'Rotate_X_'+label)

                a1['translate'].setExpression('-0.5*parent.Scale_X_'+label+'.x',0)
                a1['translate'].setExpression('input0.pixel_aspect*-0.5*parent.Scale_X_'+label+'.y',1)

                a2['translate'].setExpression('0.5*parent.Scale_X_'+label+'.x',0)
                a2['translate'].setExpression('input0.pixel_aspect*-0.5*parent.Scale_X_'+label+'.y',1)

                a3['translate'].setExpression('0.5*parent.Scale_X_'+label+'.x',0)
                a3['translate'].setExpression('input0.pixel_aspect*0.5*parent.Scale_X_'+label+'.y',1)

                a4['translate'].setExpression('-0.5*parent.Scale_X_'+label+'.x',0)
                a4['translate'].setExpression('input0.pixel_aspect*0.5*parent.Scale_X_'+label+'.y',1)

            uniform_scale.setValue(1)
        else :

            translate.setExpression('Perspective.translate.x',0)
            translate.setExpression('Perspective.translate.y',1)
            translate.setExpression('Perspective.translate.z',2)
            rotate.setExpression('Perspective.rotate.x',0)
            rotate.setExpression('Perspective.rotate.y',1)
            rotate.setExpression('Perspective.rotate.z',2)
            scale.setExpression('Perspective.scaling.x',0)
            scale.setExpression('Perspective.scaling.y',1)
            scale.setExpression('Perspective.scaling.z',2)
            uniform_scale.setExpression('Perspective.uniform_scale')


    for one in toes:
        idx = "a" + str(toes.index(one) + 1)
        ratio = "input0.width*DummyCam.focal/DummyCam.haperture"
        one.setExpression(
            f"({idx}.world_matrix.3/-{idx}.world_matrix.11) * {ratio}+input0.width/2 - DummyCam.win_translate.u*input0.width/2",
            0,
        )
        one.setExpression(
            f"({idx}.world_matrix.7/-{idx}.world_matrix.11)*input0.pixel_aspect*{ratio}+input0.height/2-DummyCam.win_translate.v*input0.width/2",
            1,
        )

    runMe = True
    while runMe == True:
        
        # we need this loop in order to temporarily kill the expression in the Dummy Cameras focal length knob.
        # the reason for that is that in following code we do bake the corner pin knobs and when we do that 
        # the values are incorrect if we do not pre-bake the focal lenght (if focal length is animated)
        # we will revert the focal length to use expression again after we finish baking the cornerpin values
        with C2Tgroup:
            focal_knob = nuke.toNode("DummyCam")['focal']
            if focal_knob.isAnimated():
                anim = focal_knob.animation(0)
                if not anim.constant():
                    for f in range(first, last + 1):
                        anim.setKey(f, anim.evaluate(f))
                    focal_knob.setExpression('curve')

        # bake expressions in card and cornerpin knobs
        for knob in toes+cardknobs:
            if knob.isAnimated():
                aSize = 1 if knob.singleValue() else knob.arraySize()
                for index in range(aSize):
                    anim = knob.animation(index)
                    if anim is None or anim.noExpression():
                        continue
                    for f in range(first, last + 1):
                        anim.setKey(f, anim.evaluate(f))
                    knob.setExpression('curve', channel=index)
                    #ISSUE: ABOVE LINE IS KILLING THE FOCAL LENSE CHANGES, LOOKS LIKE IT DOES NOT LIKE THE DUMMYCAM BEING EXPRESSION LINKED AS WELL
                    #       IF I REPLACE DUMMYCAM WITH A NORMAL CAMERA THE ISSUE IS GONE.

        # reverting back to use expression in focal lenght
        with C2Tgroup:
            focal_knob.setExpression("[expression [value the_cam]focal([value the_frame])]")


        stop_event.set()
        runMe = False
        break


def calculate_translate(C2Tgroup,label):
    '''
    Calculate translate position as an average of 4 cornerpin points.
    '''
    bg = C2Tgroup.input(0)
    first = C2Tgroup['FirstFrame_X_'+label].value()
    last = C2Tgroup['LastFrame_X_'+label].value()
    frame = first
    to1,to2,to3,to4 = C2Tgroup['to1_X_'+label], C2Tgroup['to2_X_'+label], C2Tgroup['to3_X_'+label], C2Tgroup['to4_X_'+label]

    runMe = True
    while runMe == True:

        while frame<last+1:
            to1x,to1y = to1.valueAt(frame)[0],to1.valueAt(frame)[1]
            to2x,to2y = to2.valueAt(frame)[0],to2.valueAt(frame)[1]
            to3x,to3y = to3.valueAt(frame)[0],to3.valueAt(frame)[1]
            to4x,to4y = to4.valueAt(frame)[0],to4.valueAt(frame)[1]

            C2Tgroup['TranslateT_X_'+label].setValueAt((to1x+to2x+to3x+to4x)/4-bg.width()/2,frame,0)
            C2Tgroup['TranslateT_X_'+label].setValueAt((to1y+to2y+to3y+to4y)/4-bg.height()/2,frame,1)
            C2Tgroup['centerT_X_'+label].setValue([bg.width()/2,bg.height()/2])
            frame = frame + 1
        stop_event.set()
        runMe = False
        break


def calculate_matrix(C2Tgroup,label):
    '''
    Collect information from corner pin knob and transpose it to matrix knob.
    '''
    to1             = C2Tgroup['to1_X_'+label]
    to2             = C2Tgroup['to2_X_'+label]
    to3             = C2Tgroup['to3_X_'+label]
    to4             = C2Tgroup['to4_X_'+label]
    matrix          = C2Tgroup['matrix_X_'+label]
    width = C2Tgroup.input(0).width()
    height = C2Tgroup.input(0).height()

    ref = C2Tgroup['ReferenceFrame_X_'+label].value()
    first = int(C2Tgroup['FirstFrame_X_'+label].value())
    last = int(C2Tgroup['LastFrame_X_'+label].value())

    runMe = True
    while runMe == True:
        

        projectionMatrixTo = nuke.math.Matrix4()
        projectionMatrixFrom = nuke.math.Matrix4()
        frame = first
        while frame<last+1:
            to1x = to1.valueAt(frame)[0]
            to1y = to1.valueAt(frame)[1]
            to2x = to2.valueAt(frame)[0]
            to2y = to2.valueAt(frame)[1]
            to3x = to3.valueAt(frame)[0]
            to3y = to3.valueAt(frame)[1]
            to4x = to4.valueAt(frame)[0]
            to4y = to4.valueAt(frame)[1]


            projectionMatrixTo.mapUnitSquareToQuad(to1x,to1y,to2x,to2y,to3x,to3y,to4x,to4y)
            projectionMatrixFrom.mapUnitSquareToQuad(0,0,width,0,width,height,0,height)
            theCornerpinAsMatrix = projectionMatrixTo*projectionMatrixFrom.inverse()
            theCornerpinAsMatrix.transpose()

            for i in range(0,16):
                matrix.setValueAt(theCornerpinAsMatrix[i],frame,i)

            frame = frame + 1

        stop_event.set()
        runMe = False
        break


#######################################################################################
# Functions that creating nodes


def card_code():
    '''
    Create baked Card node containing all transformations
    '''
    panel = nuke.Panel("Choose your 3D object")
    panel.addEnumerationPulldown("objects:", "Card Axis Cube Sphere Cylinder Light TransformGeo Camera2")
    if panel.show(): 
        object_3d = panel.value("objects:")
        if object_3d in ['Card','Camera']:
            object_3d == object_3d+'2'
        C2Tgroup = nuke.thisNode()
        label = nuke.thisKnob().name().rpartition('_X_')[2]
        ask = C2Tgroup['Baked_X_'+label].value()
        x = C2Tgroup['xpos'].value()
        y = C2Tgroup['ypos'].value()
        with nuke.Root():

            x = offset_nodes(x,y)
            #card = nuke.nodes.Card2(xpos = x+110, ypos = y)
            card = nuke.createNode(object_3d)
            card.setInput(0,None)
            card.setXYpos(int(x+110), int(y))
            card.setName(panel.value("objects:")+"_"+label)
            knob = nuke.Text_Knob('card_to_track', '')
            knob.setValue(C2Tgroup.name()+":card: "+label)
            card.addKnob(knob)
            if object_3d == 'Card':
                card['image_aspect'].setValue(0)

            if ask:

                if C2Tgroup['Translate_X_'+label].isAnimated():
                    card['translate'].copyAnimations(C2Tgroup['Translate_X_'+label].animations())
                else:
                    card['translate'].setValue(C2Tgroup['Translate_X_'+label].value())

                if C2Tgroup['Rotate_X_'+label].isAnimated():
                    card['rotate'].copyAnimations(C2Tgroup['Rotate_X_'+label].animations())
                else:
                    card['rotate'].setValue(C2Tgroup['Rotate_X_'+label].value())

                if C2Tgroup['Scale_X_'+label].isAnimated():
                    card['scaling'].copyAnimations(C2Tgroup['Scale_X_'+label].animations())
                else:
                    card['scaling'].setValue(C2Tgroup['Scale_X_'+label].value())

                if C2Tgroup['Uniform_scale_X_'+label].isAnimated():
                    card['uniform_scale'].copyAnimations(C2Tgroup['Uniform_scale_X_'+label].animations())
                else:
                    card['uniform_scale'].setValue(C2Tgroup['Uniform_scale_X_'+label].value())

            else:

                card['translate'].setExpression("parent."+C2Tgroup.name()+'.Translate_X_'+label)
                card['rotate'].setExpression("parent."+C2Tgroup.name()+'.Rotate_X_'+label)
                card['scaling'].setExpression("parent."+C2Tgroup.name()+'.Scale_X_'+label)
                card['uniform_scale'].setExpression("parent."+C2Tgroup.name()+'.Uniform_scale_X_'+label) 

            card.showControlPanel()


def corner_code():
    '''
    Create animated baked CornerPin node containing all transformations and matching the card position
    '''
    C2Tgroup = nuke.thisNode()
    label = nuke.thisKnob().name().rpartition('_X_')[2]
    ask = C2Tgroup['Baked_X_'+label].value()
    ref_frame = int(C2Tgroup['ReferenceFrame_X_'+label].value())
    x = C2Tgroup['xpos'].value()
    y = C2Tgroup['ypos'].value()
    with nuke.Root():
        x = offset_nodes(x,y)

        try :
            cp = nuke.nodes.CProject2(xpos = x+110, ypos = y)
            cp.setName("CP_"+label)
            cp['refFrame'].setValue(ref_frame)
            cp['label'].setValue("Matchmove\n"+str(ref_frame))
            cp['card_to_track'].setValue(C2Tgroup.name()+":cornerpin: "+label)
        except Exception as e:
            print (e)
            cp = nuke.nodes.CornerPin2D(label = label +' ('+str(ref_frame)+')', xpos = x+110, ypos = y)

        if ask:
            cp['to1'].copyAnimations(C2Tgroup['to1_X_'+label].animations())
            cp['to2'].copyAnimations(C2Tgroup['to2_X_'+label].animations())
            cp['to3'].copyAnimations(C2Tgroup['to3_X_'+label].animations())
            cp['to4'].copyAnimations(C2Tgroup['to4_X_'+label].animations())
            cp['from1'].setValue(C2Tgroup['to1_X_'+label].getValueAt(float(ref_frame)))
            cp['from2'].setValue(C2Tgroup['to2_X_'+label].getValueAt(float(ref_frame)))
            cp['from3'].setValue(C2Tgroup['to3_X_'+label].getValueAt(float(ref_frame)))
            cp['from4'].setValue(C2Tgroup['to4_X_'+label].getValueAt(float(ref_frame)))
        else:
            cp['to1'].setExpression("parent.parent."+C2Tgroup.name()+'.to1_X_'+label)
            cp['to2'].setExpression("parent.parent."+C2Tgroup.name()+'.to2_X_'+label)
            cp['to3'].setExpression("parent.parent."+C2Tgroup.name()+'.to3_X_'+label)
            cp['to4'].setExpression("parent.parent."+C2Tgroup.name()+'.to4_X_'+label)
            cp['from1'].setValue(C2Tgroup['to1_X_'+label].getValueAt(ref_frame))
            cp['from2'].setValue(C2Tgroup['to2_X_'+label].getValueAt(ref_frame))
            cp['from3'].setValue(C2Tgroup['to3_X_'+label].getValueAt(ref_frame))
            cp['from4'].setValue(C2Tgroup['to4_X_'+label].getValueAt(ref_frame))
        cp.showControlPanel()


def transform_code():
    '''
    Create baked Transform node containing translation of the card but without rotation and or scale.
    '''
    C2Tgroup = nuke.thisNode()
    label = nuke.thisKnob().name().rpartition('_X_')[2]
    translateT = C2Tgroup['TranslateT_X_'+label]
    centerT = C2Tgroup['centerT_X_'+label]
    translateT.setAnimated()
    #centerT.setAnimated()


    # # run transpose operation with threading
    global stop_event 
    stop_event = threading.Event()
    threading.Thread(target=calculate_translate, kwargs=dict(C2Tgroup=C2Tgroup,label=label)).start()
    while not stop_event.is_set():
        time.sleep(0.02)

    ask = C2Tgroup['Baked_X_'+label].value()
    ref_frame = str(int(C2Tgroup['ReferenceFrame_X_'+label].value()))
    x,y = C2Tgroup['xpos'].value(),C2Tgroup['ypos'].value()

    with nuke.Root():
        x = offset_nodes(x,y)
        try:
            tr = nuke.nodes.TProject2(xpos = x+110, ypos = y)
            tr.setName("TP_"+label)
            tr['label'].setValue("Matchmove\n"+str(ref_frame))
            tr['card_to_track'].setValue(C2Tgroup.name()+":transform: "+label)
        except Exception as e:
            print (e)
            tr = nuke.nodes.Transform(label = label+' transform ('+str(ref_frame)+')',xpos = x+110, ypos = y)

        if ask:
            if C2Tgroup['TranslateT_X_'+label].isAnimated():
                tr['translate'].copyAnimations(translateT.animations())
                #tr['center'].copyAnimations(centerT.animations())
            else:
                tr['translate'].setValue(translateT.value())
            tr['center'].setValue(centerT.value())
        else:
            tr['translate'].setExpression("parent.parent."+C2Tgroup.name()+'.TranslateT_X_'+label)
            tr['center'].setExpression("parent.parent."+C2Tgroup.name()+'.centerT_X_'+label)
        tr.showControlPanel()
    tr['setCurrentAsRefFrame'].execute()
    with tr:
        pall = nuke.toNode("refPall")
        papa = nuke.toNode("Transform1")
        pall['disable'].setValue(False)
        knobs = ["translate","rotate","scale","center"]
        for one in knobs:
            pall[one].setValue(papa[one].value())

def roto_code():
    '''
    Creating roto node with corresponding animation.
    '''
    message = '''Looks like Nuke does not support linking of the transformation matrix in roto nodes - please bake instead.

    Since we are able to recalculate nodes if camera is updated - i will generally recommend to bake and not to link nodes while using CardToTrack.'''

    C2Tgroup = nuke.thisNode()
    label = nuke.thisKnob().name().rpartition('_X_')[2]
    ask = C2Tgroup['Baked_X_'+label].value()
    if ask:



        ref = C2Tgroup['ReferenceFrame_X_'+label].value()
        x = C2Tgroup['xpos'].value()
        y = C2Tgroup['ypos'].value()
        first = C2Tgroup['FirstFrame_X_'+label].value()
        last = C2Tgroup['LastFrame_X_'+label].value()

        ref = C2Tgroup['ReferenceFrame_X_'+label].value()

        to1 = C2Tgroup['to1_X_'+label]
        to2 = C2Tgroup['to2_X_'+label]
        to3 = C2Tgroup['to3_X_'+label]
        to4 = C2Tgroup['to4_X_'+label]
        matrix = C2Tgroup['matrix_X_'+label]
        matrix.setAnimated()



        # # run transpose operation with threading
        global stop_event 
        stop_event = threading.Event()
        threading.Thread(target=calculate_matrix, kwargs=dict(C2Tgroup=C2Tgroup,label=label)).start()
        while not stop_event.is_set():
            time.sleep(0.02)

        #create roto node and copy animation from matrix to roto root matrix
        with nuke.Root():

            panel = nuke.Panel("Roto or RotoPaint")
            panel.addEnumerationPulldown("Roto Type:", "Roto RotoPaint")
            if panel.show(): 
                rototype = panel.value("Roto Type:")
                x = offset_nodes(x,y)
                if rototype =="Roto":
                    roto = nuke.nodes.Roto( xpos = x+110, ypos = y)
                else:
                    roto = nuke.nodes.RotoPaint( xpos = x+110, ypos = y)
                roto.setName(roto['name'].value().replace('Roto','R')+"_"+label)
                roto['cliptype'].setValue("no clip")
                nuke.show(roto)
                knob = nuke.Text_Knob('card_to_track', '')
                knob.setValue(C2Tgroup.name()+":roto: "+label)
                roto.addKnob(knob)
                if ask:
                    roto['transform_matrix'].copyAnimations(C2Tgroup['matrix_X_'+label].animations())
                    roto['curves'].changed()
                else:
                    nuke.message(message)

                # apply format to the roto node
                group_format = C2Tgroup.format()
                name = group_format.name()
                if name:
                    roto['format'].setValue(name)
                else:
                    width = str(group_format.width())
                    height = str(group_format.height())
                    aspect = str(group_format.pixelAspect())
                    name = "temp_"+width+"x"+height
                    new_format = width+" "+height+" "+aspect+" "+name
                    nuke.addFormat(new_format)
                    roto['format'].setValue(name)
    else:
        nuke.message(message)


def object_only():
    '''
    create only 3D object
    '''
    C2Tgroup=nuke.thisGroup()

    t = C2Tgroup['translate'].value()
    r = C2Tgroup['rotate'].value()
    s = C2Tgroup['scaling'].value()
    u = C2Tgroup['uniform_scale'].value()
    C2Tgroup.end()
    
    panel = nuke.Panel("object")
    panel.addSingleLineInput("Object Name:","")
    panel.addEnumerationPulldown("objects:", "Card Axis Cube Sphere Cylinder Light TransformGeo Camera")

    if panel.show(): 
        ob = panel.value("objects:")
        name = panel.value("Object Name:")
        obj = nuke.createNode(ob)
        x = C2Tgroup['xpos'].value()
        y = C2Tgroup['ypos'].value()
        obj.setInput(0,None)
        obj['xpos'].setValue(int(x))
        obj['ypos'].setValue(int(y+100))
        obj['translate'].setValue(t)
        obj['rotate'].setValue(r)
        obj['scaling'].setValue(s)
        obj['uniform_scale'].setValue(u)
        obj.setName(name)


########################################################################################
# Functions used in CProject and TProject


def set_ref_frame_cp(frame,node):
    '''
    set reference frame for corner pin node
    '''

    ntn = nuke.thisNode()
    if node == 'cornerpin':
        set_to_input_label_toggle(ntn,unset=True)
        for one in range(1,5):
           ntn['from'+str(one)].setValue(ntn['to'+str(one)].valueAt(frame)) 
    elif node == 'translate':
        #nuke.toNode('refPall')["translate"].setValue([ntn["translate"].getValueAt(0,frame)*-1,ntn["translate"].getValue(1,frame)*-1]) 

        pall = nuke.toNode("refPall")
        papa = nuke.toNode("Transform1")
        pall['disable'].setValue(False)
        knobs = ["translate","rotate","scale","center"]
        for one in knobs:
            pall[one].setValue(papa[one].value())

    ntn['label'].setValue(ntn['mode_toggle'].label().rpartition(">")[2]+"\n"+str(frame))
    ntn['refFrame'].setValue(frame)
    nuke.toNode("FHold")['first_frame'].setValue(frame)

stored=[]
def recurseUpSelect(node):
    global stored
    if node != None and node not in stored:
        for i in range(node.inputs()):
            recurseUpSelect(node.input(i)) 
            stored.append(node.input(i))
    return stored


def toggle_matchmove_stabilise(node):
    '''
    Toggle matchmove vs stabilise in CProject or TProject
    '''
    ntn = nuke.thisNode()
    ntk = nuke.thisKnob()
    ref_frame = str(int(ntn['refFrame'].value()))
    lab = ntk.label()

    mm = "<h1 style = 'font-size:30'><b><font color=#9667D1>Matchmove"
    stab = "<h1 style = 'font-size:30'><b><font color=#797BFF>Stabilize"

    if lab == mm:
        ntk.setLabel(stab)
        ntn['invert'].setValue(True)
        ntn['tile_color'].setValue(1834205695)

        if node == 'translate':
            ntn['label'].setValue("Stabilize\n"+ref_frame)
            with ntn:
                nuke.toNode('refPall')['disable'].setValue(False)
        else:
            if ntn['set_to_input_1'].label() == "<h1 style = 'font-size:10'><b>Set To Input":
                ntn['label'].setValue("Stabilize\ninput")
            else:
                ntn['label'].setValue("Stabilize\n"+ref_frame)
            pass

    elif lab == stab:
        ntk.setLabel(mm)
        ntn['invert'].setValue(False)
        ntn['tile_color'].setValue(2051246591)

        if node == 'translate':
            ntn['label'].setValue("Matchmove\n"+ref_frame)
            with ntn:
                nuke.toNode('refPall')['disable'].setValue(True)
        else:
            if ntn['set_to_input_1'].label() == "<h1 style = 'font-size:10'><b>Set To Input":
                ntn['label'].setValue("Matchmove\ninput")
            else:
                ntn['label'].setValue("Matchmove\n"+ref_frame)
            pass

    if node != 'translate':
        # adding auto toggle for second CProject to check input or output aspect checkboxes according to upstream CProject node
        global stored
        stored =[]
        upstreamNodes = recurseUpSelect(ntn.input(0))
        for one in upstreamNodes:
            if one:
                if 'card_to_track' in one.knobs():
                    image_aspect = one['image_aspect'].value()
                    image_aspect_out = one['image_aspect_out'].value()
                    if image_aspect_out: 
                        ntn['image_aspect'].setValue(True)
                        ntn['image_aspect_out'].setValue(False)
                        break
                    elif image_aspect: 
                        ntn['image_aspect_out'].setValue(True) 
                        ntn['image_aspect'].setValue(False)
                        break
                    else:
                        ntn['image_aspect_out'].setValue(False) 
                        ntn['image_aspect'].setValue(False)
                        break
                else:
                    ntn['image_aspect_out'].setValue(False) 
                    ntn['image_aspect'].setValue(False)
                    #break


def set_to_input_label_toggle(ntn,unset):
    ntk = ntn['set_to_input_1']
    lab = ntk.label()
    input_set = "<h1 style = 'font-size:10'><b>Set To Input"
    ref_frame_set = "Set To Input"
    if unset:
        ntk.setLabel(ref_frame_set)
        return
    if lab == input_set:
        ntk.setLabel(ref_frame_set)
    else:
        ntk.setLabel(input_set)


def set_to_input_cp():
    '''
    Set 'From' values of the Corner pin to the input footage canvas.
    '''
    ntn = nuke.thisNode()
    set_to_input_label_toggle(ntn,unset=False)
    #ntn['image_aspect_out'].setValue(1)
    with ntn:
        nuke.toNode("CornerPin2D2")["set_to_input"].execute()
        ntn['label'].setValue(ntn['mode_toggle'].label().rpartition(">")[2]+"\ninput")


def knob_changed_cp():
    nn = nuke.thisNode()
    k = nuke.thisKnob()
    kn = k.name()

    if kn == "cropP":

        if nn['cropP'].value() in ["Hard Crop"]:
            nn["growBbox"].setVisible(False)
            nn["text"].setValue("Image is cropped to Input, Concatenation preserved.")

        elif nn['cropP'].value() in ["Adjustable Crop"]:
            nn["growBbox"].setVisible(True)
            nn["text"].setValue("Adjust your Bbox , Downward <b><font color='Dark Red'>Concatenation is broken<b>.")

        elif nn['cropP'].value() in ["No Crop"]:
            nn["growBbox"].setVisible(False)
            nn["text"].setValue("No Crop applied, Concatenation preserved.")