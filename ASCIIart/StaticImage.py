from PIL import Image
from PIL import GifImagePlugin

from Frame import Frame
from Utils import Utils
import constants

import curses

class StaticImage:
    """An image to be used by the program"""
    
    def __init__(self,fileName, glitch = False, debug = False):
    
        # TODO Maybe attempt to use different extensions?
        self.frame = Frame(filePath = constants.INPUT_PATH + fileName)
        self.glitch = glitch
        self.debug = debug
    
    def show(self):
    
        # Process the only frame
        self.frame.process()

        # Initialize a new curses pad
        screen, pad = Utils.cursesScreenInit(self.frame.sizeX,self.frame.sizeY)
        
        # Print that image
        self.frame.show(self.glitch,screen,pad,False)
        
        # End curses pad
        Utils.cursesScreenEnd(screen)
        
        return
        
    def setGlitch(self,glitch):
        self.glitch = glitch
        
        return
        
    def setDebug(self,debug):
        self.debug = debug
        
        return