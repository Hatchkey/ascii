from PIL import Image
from PIL import ImageDraw
from PIL import GifImagePlugin

import constants

import numpy as np
import math
import statistics
import curses


class Frame:
    """A frame of an image or gif"""

    def __init__(self, filePath = None, access = None, sizeX = None, sizeY = None, compFactor = None, duration = None):
        
        if (filePath == None):
            # Initialize from data (for gifs)
            
            self.access = access
            self.sizeX = sizeX
            self.sizeY = sizeY
            self.compressionFactor = compFactor
            self.duration = duration

        else:
            # Initialize from a file (for images)
            
            try:
                self.img = Image.open(filePath)
                self.access = self.img.load()
                self.sizeX, self.sizeY = self.img.size
                self.compressionFactor = max(1,math.floor(self.sizeX/250)) # TODO

            except FileNotFoundError as error:
                print(error)
            
    def rescale(self):
        # Performs nearest-neighbor rescaling on the image to fit the provided compression factor

        def correctPixel(i,j):
            return (j% (self.compressionFactor*2) == 1 and i % self.compressionFactor == 1) or self.compressionFactor == 1
        
        # Calculate new size for the image
        newSizeX = math.floor(self.sizeX/self.compressionFactor)
        newSizeY = math.floor(self.sizeY/(2*self.compressionFactor))
        
        # Generate a new compressed image with the calculated size
        compImg = Image.new('RGB',[newSizeX,newSizeY])
        compImgAccess = compImg.load() # TODO Not needed?
        compImgDrawer = ImageDraw.Draw(compImg)
        
        # Port nearest pixels from the original image
        for y in range(self.sizeY - 1):
            for x in range(self.sizeX - 1):
                if (correctPixel(x,y)):
                    positionX = math.floor(x/self.compressionFactor)
                    positionY = math.floor(y/(2*self.compressionFactor))
                    compImgDrawer.point([positionX,positionY],self.access[x,y])

        # Update access value
        compImgAccess = compImg.load()
        
        # Update access matrix, image and size
        self.img = compImg
        self.access = compImgAccess
        self.sizeX = newSizeX
        self.sizeY = newSizeY

        return 

    def grayscale(self):
        # Converts this frame to grayscale in 8 bits

        def toGrayscale(rgbValues):
            # Convert an rgb value to the corresponding grayscale value
            return math.floor(0.2126*rgbValues[0] + 0.7152*rgbValues[1] + 0.0722*rgbValues[2])

        # Generate new grayscale image for the converted frame
        grayImg = Image.new('L',[self.sizeX,self.sizeY])
        grayImgAccess = grayImg.load() # TODO Not needed?
        grayImgDrawer = ImageDraw.Draw(grayImg)

        # Convert each pixel of the frame
        for y in range(self.sizeY - 1):
            for x in range(self.sizeX - 1):
                grayValue = toGrayscale(self.access[x,y])
                grayImgDrawer.point([x,y],grayValue)

        # Update access value
        grayImgAccess = grayImg.load()

        # Update image and access matrix
        self.img = grayImg
        self.access = grayImgAccess

        return

    def unsharp(self):
        # Perform unsharp masking using gaussian filter on the frame

        def gaussian(imgAccess,x,y):
            # Gaussian filter:
            # -1 -1 -1
            # -1  8 -1
            # -1 -1 -1

            finalValue = 8*imgAccess[x,y]

            # X+1 , Y
            if (x+1 <= self.sizeX):
                finalValue = finalValue - imgAccess[x+1,y]
                
                # X+1 , Y+1
                if (y+1 <= self.sizeY):
                    finalValue = finalValue - imgAccess[x+1,y+1]
                # X+1 , Y-1
                if (y-1 >= 0):
                    finalValue = finalValue - imgAccess[x+1,y-1]

            # X-1 , Y
            if (x - 1 >= 0):
                finalValue = finalValue - imgAccess[x-1,y]

                # X-1 , Y+1
                if (y+1 <= self.sizeY):
                    finalValue = finalValue - imgAccess[x-1,y+1]

                # X-1, Y-1
                if (y-1 >= 0):
                    finalValue = finalValue - imgAccess[x-1,y-1]

            # X , Y+1
            if (y+1 <= self.sizeY):
                finalValue = finalValue - imgAccess[x,y+1]

            # X , Y-1
            if (y-1 >= 0):
                    finalValue = finalValue - imgAccess[x,y-1]

            return finalValue


        # Copies the image so that changes during processing do not affect next pixel
        imgCopy = self.img.copy()
        imgCopyAccess = imgCopy.load()
        imgDrawer = ImageDraw.Draw(self.img)

        # Process each pixel
        for y in range(self.sizeY - 1):
            for x in range(self.sizeX - 1):
                newPixAdd = gaussian(imgCopyAccess,x,y)
                imgDrawer.point([x,y],imgCopyAccess[x,y] + newPixAdd)

        # Update access matrix
        self.access = self.img.load()

        return
        
    def threshold(self):
        # Performs thresholding on the image into x classes

        def medianValue():
            # Returns the median pixel intensity
            aux = []
            for i in range(self.sizeX):
                for j in range(self.sizeY):
                    aux.append(self.access[i,j])

            median = (max(aux)+min(aux))/2
            return median

        med = medianValue()

        # Generate image drawer
        imgDrawer = ImageDraw.Draw(self.img)

        # Classify pixels
        for y in range(self.sizeY - 1):
            for x in range(self.sizeX - 1):
                
                pixelValue = self.access[x,y]
                if (pixelValue >= med):
                    if (pixelValue >= 5*med/8):
                        if (pixelValue >= 6*med/8):
                            imgDrawer.point([x,y],224)
                        else:
                            imgDrawer.point([x,y],192)
                    else:
                        if (pixelValue >= 4*med/8):
                            imgDrawer.point([x,y],160)
                        else:
                            imgDrawer.point([x,y],128)
                else:
                    if (pixelValue >= 2*med/8):
                        if (pixelValue >= 3*med/8):
                            imgDrawer.point([x,y],96)
                        else:
                            imgDrawer.point([x,y],64)
                    else:
                        if (pixelValue >= 1*med/8):
                            imgDrawer.point([x,y],32)
                        else:
                            imgDrawer.point([x,y],0)

        # Update access
        self.access = self.img.load()
               
        return

    def crop(self):
        # Crops a 1 pixel border from the frame
        cropImg = self.img.crop((1,1,self.sizeX,self.sizeY))
        cropAccess = cropImg.load()
        newSizeX,newSizeY = cropImg.size

        self.img = cropImg
        self.access = cropAccess
        self.sizeX = newSizeX
        self.sizeY = newSizeY

        return

    def process(self):
        # Apply every filter to the frame
        
        self.rescale()
        self.grayscale()
        self.unsharp()
        self.threshold()
        self.crop()
        
        return
    
    def showGlitchy(self,screen,pad):

        mask = np.random.rand(self.sizeX,self.sizeY)

        glitchCounter = 0.01 # Starting glitch effect counter
        glitchRate = 0.15	 # Rate at which the image will change

        c = ord('z')

        while (c != ord('q')):


            glitchCounter = glitchCounter + glitchRate

            if (glitchCounter <= 0 or glitchCounter >= 0.5):

                if (glitchCounter >= 0.5 and glitchCounter <= 1):
                    pass
                else:
                    glitchRate = - glitchRate

            for i in range(0,self.sizeX-1):
                for j in range(0,self.sizeY-1):
                    if (mask[i,j] < glitchCounter):
                        pad.addch(j,i,constants.CHAR_SET[self.access[i,j]])
                    else:
                        pad.addch(j,i,np.random.randint(low=1,high=127))

            pad.refresh(0,0, 0,0, curses.LINES-1,curses.COLS-1)
            
            c = screen.getch()
        
        return
        
    def showDefault(self,screen,pad,gif):     	
        if (gif):
        
            for i in range(0,self.sizeX-1):
                for j in range(0,self.sizeY-1):					
                    pad.addch(j,i,constants.CHAR_SET[self.access[i,j]])

            pad.refresh(0,0, 0,0, curses.LINES-1,curses.COLS-1)
            
        else:

            c = ord('z')

            while(c != ord('q')):
            
                for i in range(0,self.sizeX-1):
                    for j in range(0,self.sizeY-1):					
                        pad.addch(j,i,constants.CHAR_SET[self.access[i,j]])

                pad.refresh(0,0, 0,0, curses.LINES-1,curses.COLS-1)

                c = screen.getch()
                
        return

    def show(self,glitch,screen,pad,gif):
        
        if (glitch):
            self.showGlitchy(screen,pad)
        else:
            self.showDefault(screen,pad,gif)
        
        return
