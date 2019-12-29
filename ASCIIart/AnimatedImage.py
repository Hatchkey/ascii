from PIL import Image
from PIL import GifImagePlugin

from Frame import Frame
from Utils import Utils
import constants

import time
import curses

class AnimatedImage:
    """A gif to be used by the program"""
    
    def __init__(self,fileName):
    
        self.gif = Image.open(constants.INPUT_PATH + fileName)
        self.sizeX, self.sizeY = self.gif.size
        self.compressionFactor = 1 #TODO Calculate based on terminal size  
        self.frames = []
    
    def prepare(self):

        for frameIndex in Utils.progressbar(range(0,self.gif.n_frames), prefix="Processing frames...", size=self.gif.n_frames):
            
            # Locate current frame
            self.gif.seek(frameIndex)
            access = self.gif.load()
            
            # Initialize and process current frame
            frame = Frame(access=access,sizeX=self.sizeX,sizeY=self.sizeY,compFactor=self.compressionFactor,duration=self.gif.info['duration'])
            frame.process()
            
            # Save for later presenting
            self.frames.append(frame)
    
    def show(self):
    
        # Process itself
        self.prepare()
        
        # Wait for user input
        input("\nReady\n")
    
        # Initialize a curses pad
        screen, pad = Utils.cursesScreenInit(self.sizeX,self.sizeY)
        
        # Show every frame available
        control = ord('a')
        
        for frame in self.frames:
            frame.show(False,screen,pad,True)
            time.sleep(constants.PLAY_SPEED*frame.duration)

        # End curses pad
        Utils.cursesScreenEnd(screen)