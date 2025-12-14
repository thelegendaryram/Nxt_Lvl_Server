#----------------------------------------------------------------------------------------------------------
#
# AUTOMATICALLY GENERATED FILE TO BE USED BY W_HOTBOX
#
# NAME: Open In Explorer
# COLOR: #ffffff
# TEXTCOLOR: #111111
#
#----------------------------------------------------------------------------------------------------------

import nuke
import os
import platform
import subprocess


def openPathInExplorer():
  
  operatingSystem = platform.system()
  path1 = nuke.script_directory()
  if nuke.selectedNodes() == []:

        if operatingSystem == "Windows":
            os.startfile(path1)
        elif operatingSystem == "Darwin":
            subprocess.Popen(["open", path1])
        else:
            os.system('xdg-open "%s"' %path1)
     
  
  for i in nuke.selectedNodes():

    path =  os.path.dirname(i.knob('file').value())

    if os.path.exists(path):

        if operatingSystem == "Windows":
            os.startfile(path)
        elif operatingSystem == "Darwin":
            subprocess.Popen(["open", path])
        else:
            os.system('xdg-open "%s"' %path)
            
openPathInExplorer()