from PIL import Image
from PIL import ImageDraw
from PIL import GifImagePlugin
from tkinter import Frame,Tk,Label,Text

import statistics
import math
import os
import time
import sys
import shutil
import tkinter

#		TODO
#	Post-processing smoothing
#	Bilinear interpolation for rescaling
#	Dithering instead of thresholding
#	better Gif suport
#	Better charset

#	USAGE
# python3 ASCIIart.py <FileName> [-d, -g, -n, -w]

class Window(Frame):

	def __init__(self, master=None,title="Blank"):
		Frame.__init__(self, master)               
		self.master = master
		

#Show steps of image conversion?
debug = False
gif = False
now = False
window = False

if (len(sys.argv) > 0 and "-d" in str(sys.argv)):
	debug = True

if ("-g" in str(sys.argv)):
	gif = True

if ("-n" in str(sys.argv)):
	now = True

if ("-w" in str(sys.argv)):
	window = True

#Variable which determines the character set the image will be printed with
#[DARK, DARKGRAY, LIGHTGRAY, LIGHT]
#baseCharset = [' ', '/', '1', 'B']
baseCharset = [' ','*','+','/','1','7','B','#']

def getImageInformation():
	#Get file name
	fileName = sys.argv[1] 	
	
	#Try opening the image			
	originalImage = Image.open("Input/"+fileName)
	originalImageMatrix = originalImage.load()
	sizex,sizey = originalImage.size

	#Calculates the compression factor for the image to fit the terminal
	compressionFactor = math.floor(sizex/250) #TODO Retrieve terminal size to calculate compression factor
	
	if compressionFactor == 0:
		compressionFactor = 1 #Support for small images	

	if (debug):
		originalImage.show()
	
	return fileName,originalImageMatrix,sizex,sizey,compressionFactor

def getGifInformation():
	fileName = sys.argv[1]
	
	originalGif = Image.open("Input/"+fileName)
	if (debug):
		print(originalGif.is_animated)
		print(originalGif.n_frames)
	
	sizex,sizey = originalGif.size
	
	terminalSize = shutil.get_terminal_size()

	compressionFactor = math.floor(max(sizex/terminalSize.columns,sizey/terminalSize.columns))

	if compressionFactor == 0:
		compressionFactor = 1

	return fileName,originalGif,sizex,sizey,compressionFactor

def nearestNeighborRescaling(ImageMatrix,sizex,sizey,compressionFactor):
	#Rescales the image by compressionFactor, with the y axis being rescaled by 2*compressionFactor
	#due to characters being printed in 6x3 pixels

	def isRightPixel(sizex,sizey,x,y):
		#Decides if the analyzed pixel goes into the compressed image, based on the compression factor using
		#the nearest neighbor method
		if (y%(compressionFactor*2) == 1 and x%compressionFactor == 1):
			return True
		else:
			return False
	
	#Initialize the new image with compressed size and its drawer
	newSizex = math.floor(sizex/compressionFactor)
	newSizey = math.floor(sizey/(compressionFactor*2))
	compressedImage = Image.new('RGB',[newSizex,newSizey])
	compressedImageMatrix = compressedImage.load()
	compressedImageDrawer = ImageDraw.Draw(compressedImage);
	
	#Copy the pixels that are ported from the original image
	for y in range(sizey-1):
		for x in range(sizex-1):
			if(compressionFactor == 1 or isRightPixel(sizex,sizey,x,y)):
				positionX = math.floor(x/compressionFactor)
				positionY = math.floor(y/(compressionFactor*2))
				compressedImageDrawer.point([positionX,positionY],ImageMatrix[x,y])
	
	if (debug):
		compressedImage.show()
	
	#Reloads the matrix
	compressedImageMatrix = compressedImage.load()
	
	return compressedImageMatrix,compressedImage,newSizex,newSizey
	
def newGrayScaleImage(ImageMatrix,sizex,sizey):
	#Converts the provided image to a grayscale version of it, and returns it
	
	def grayscaleConverter(rgbValues):
		#Given the RGB value of a pixel, converts it to a grayscale value
		grayscaleValue = 0.2126*rgbValues[0] + 0.7152*rgbValues[1] + 0.0722*rgbValues[2]
		return math.floor(grayscaleValue)
	
	#Creates a new image in the small size
	grayscaleImage = Image.new('L',[sizex,sizey])
	grayscaleImageMatrix = grayscaleImage.load()
	grayscaleImageDrawer = ImageDraw.Draw(grayscaleImage)

	#Fills that image converting RGB to grayscale
	for y in range(sizey-1):
		for x in range(sizex-1):
			grayscaleValue = grayscaleConverter(ImageMatrix[x,y])
			#print(grayscaleValue)
			grayscaleImageDrawer.point([x,y],grayscaleValue)
	
	if (debug):
		grayscaleImage.show()
		
	#Reloads the matrix
	grayscaleImageMatrix = grayscaleImage.load()
	
	return grayscaleImageMatrix,grayscaleImage

def unsharpMasking(ImageMatrix,Image,sizex,sizey):
	#Performs unsharp masking to fletch out image borders
	
	def unsharpGaussian(ImageMatrix,x,y,sizex,sizey):
		#Uses the gaussian filter for unsharp masking in this pixel's neighborhood
		#([-1 -1 -1]
		# [-1  8 -1]
		# [-1 -1 -1])
		finalValue = 8*ImageMatrix[x,y]
		#x+1,y
		if (x+1 <= sizex):
			finalValue = finalValue - ImageMatrix[x+1,y]
			#x+1,y+1
			if (y+1 <= sizey):
				finalValue = finalValue - ImageMatrix[x+1,y+1]
			#x+1,y-1
			if (y-1 >= 0):
				finalValue = finalValue - ImageMatrix[x+1,y-1]
		#x-1,y
		if (x-1 >= 0):
			finalValue = finalValue - ImageMatrix[x-1,y]
			#x-1,y+1
			if (y+1 <= sizey):
				finalValue = finalValue - ImageMatrix[x-1,y+1]
			#x-1,y-1
			if (y-1 >= 0):
				finalValue = finalValue - ImageMatrix[x-1,y-1]
		#x,y+1
		if (y+1 <= sizey):
			finalValue = finalValue - ImageMatrix[x,y+1]
		#x,y-1
		if(y-1 >= 0):
			finalValue = finalValue - ImageMatrix[x,y-1]
		
		return finalValue
	
	#Copies the matrix so that changes during processing do not affect next pixel
	grayscaleImageCopy = Image.copy()
	grayscaleImageCopyMatrix = grayscaleImageCopy.load()
	#Creates the drawer for this image
	grayscaleImageDrawer = ImageDraw.Draw(Image)
	
	for y in range(sizey - 1):
		for x in range(sizex - 1):
			newPixelValue = unsharpGaussian(grayscaleImageCopyMatrix,x,y,sizex,sizey)
			grayscaleImageDrawer.point([x,y],ImageMatrix[x,y] + newPixelValue)
			
	if (debug):
		Image.show()
		
	#Reloads the matrix
	ImageMatrix = Image.load()
	
	return ImageMatrix,Image

def thresholding(ImageMatrix,Image,sizex,sizey):
	#Performs thresholding in the image

	def findMedianV(ImageMatrix,sizex,sizey):
		#Returns the median pixel intensity in the given image
		aux = []
		for i in range(sizex):
			for j in range(sizey):
				aux.append(ImageMatrix[i,j])
		
		median = (max(aux)+min(aux))/2
		return median
		
	median = findMedianV(ImageMatrix,sizex,sizey)
	
	ImageDrawer = ImageDraw.Draw(Image)	

	for y in range (1,sizey-1):
		for x in range (1,sizex-1):
			newPixelValue = ImageMatrix[x,y]
			if (newPixelValue >= median):
				if(newPixelValue >= 5*median/8):
					if(newPixelValue >= 6*median/8):
						ImageDrawer.point([x,y],224)
					else:
						ImageDrawer.point([x,y],192)
				else:
					if(newPixelValue >= 4*median/8):
						ImageDrawer.point([x,y],160)
					else:
						ImageDrawer.point([x,y],128)
			else:
				if(newPixelValue >= 2*median/8):
					if(newPixelValue >= 3*median/8):
						ImageDrawer.point([x,y],96)
					else:
						ImageDrawer.point([x,y],64)
				else:
					if(newPixelValue >= 1*median/8):
						ImageDrawer.point([x,y],32)
					else:
						ImageDrawer.point([x,y],0)
	
	if (debug):
		Image.show()
	
	ImageMatrix = Image.load()
	
	return ImageMatrix,Image

def cropping(Image,sizex,sizey):
	#Crops the 1 pixel border left from thresholding
	croppedImage = Image.crop((1,1,sizex,sizey))
	croppedImageMatrix = croppedImage.load()
	newSizex,newSizey = croppedImage.size
	
	return croppedImageMatrix,croppedImage,newSizex,newSizey
	
def smoothing(ImageMatrix,Image,sizex,sizey):
	#NEEDS REDOING (TOO STRONG)
	def meanFilter(ImageMatrix,x,y,sizex,sizey):
		#Gets the mean value of this pixel's neighborhood and adds it to the center
		pixelValuesVector = [ImageMatrix[x,y]]
		#x+1,y
		if (x+1 <= sizex):
			pixelValuesVector.append(ImageMatrix[x+1,y])
			#x+1,y+1
			if (y+1 <= sizey):
				pixelValuesVector.append(ImageMatrix[x+1,y+1])
			#x+1,y-1
			if (y-1 >= 0):
				pixelValuesVector.append(ImageMatrix[x+1,y-1])
		#x-1,y
		if (x-1 >= 0):
			pixelValuesVector.append(ImageMatrix[x-1,y])
			#x-1,y+1
			if (y+1 <= sizey):
				pixelValuesVector.append(ImageMatrix[x-1,y+1])
			#x-1,y-1
			if (y-1 >= 0):
				pixelValuesVector.append(ImageMatrix[x-1,y-1])
		#x,y+1
		if (y+1 <= sizey):
			pixelValuesVector.append(ImageMatrix[x,y+1])
		#x,y-1
		if(y-1 >= 0):
			pixelValuesVector.append(ImageMatrix[x,y-1])
		
		return math.floor(statistics.mean(pixelValuesVector))
		
	ImageDrawer = ImageDraw.Draw(Image)
	imageCopy = Image.copy()
	imageCopyMatrix = imageCopy.load()
	
	for y in range(1,sizey-1):
		for x in range(1,sizex-1):
			newPixelValue = meanFilter(imageCopyMatrix,x,y,sizex,sizey)
			ImageDrawer.point([x,y],newPixelValue)

	if (debug):
		Image.show()
		
	#Reload the matrix
	ImageMatrix = Image.load()
	
	return ImageMatrix,Image
	
def showImage(finalImageMatrix,finalSizex,finalSizey,baseCharset,fileName):
	
	def printImage(ImageMatrix,sizex,sizey,charset):
		os.system('cls' if os.name == 'nt' else 'clear')	
		for y in range(sizey):
			print('')
			for x in range(sizex):
				if   (ImageMatrix[x,y] ==   0):
					print(charset[0],end='')
				elif (ImageMatrix[x,y] ==  32):
					print(charset[1],end='')
				elif (ImageMatrix[x,y] ==  64):
					print(charset[2],end='')
				elif (ImageMatrix[x,y] ==  96):
					print(charset[3],end='')
				elif (ImageMatrix[x,y] == 128):
					print(charset[4],end='')
				elif (ImageMatrix[x,y] == 160):
					print(charset[5],end='')
				elif (ImageMatrix[x,y] == 192):
					print(charset[6],end='')
				elif (ImageMatrix[x,y] == 224):
					print(charset[7],end='')

	def printToWindow(ImageMatrix,sizex,sizey,charset,fileName):
		root = Tk()
		root.title(fileName)
		text = Text(root,height = sizey,width = sizex)
		text.pack()
		text.config(font = ("Courier", 2),bg = 'black',fg = 'green')
		for y in range(0,sizey):
			for x in range(0,sizex):
				if   (ImageMatrix[x,y] ==   0):
					text.insert(tkinter.END,charset[0])
				elif (ImageMatrix[x,y] ==  32):
					text.insert(tkinter.END,charset[1])
				elif (ImageMatrix[x,y] ==  64):
					text.insert(tkinter.END,charset[2])
				elif (ImageMatrix[x,y] ==  96):
					text.insert(tkinter.END,charset[3])
				elif (ImageMatrix[x,y] == 128):
					text.insert(tkinter.END,charset[4])
				elif (ImageMatrix[x,y] == 160):
					text.insert(tkinter.END,charset[5])
				elif (ImageMatrix[x,y] == 192):
					text.insert(tkinter.END,charset[6])
				elif (ImageMatrix[x,y] == 224):
					text.insert(tkinter.END,charset[7])
		root.mainloop()
	
	if (not window):
		printImage(finalImageMatrix,finalSizex,finalSizey,baseCharset)
	else:
		if (not gif):
			printToWindow(finalImageMatrix,finalSizex,finalSizey,baseCharset,fileName)
		if (gif):
			return 0
	
def processFrame(originalImageMatrix,sizex,sizey,compressionFactor):

	#Nearest Neighbor rescaling 
	compressedImageMatrix,compressedImage,sizex,sizey = nearestNeighborRescaling(originalImageMatrix,sizex,sizey,compressionFactor)

	#Grayscale conversion
	grayscaleImageMatrix,grayscaleImage = newGrayScaleImage(compressedImageMatrix,sizex,sizey)

	#Smoothing
	#smoothedImageMatrix,smoothedImage = smoothing(grayscaleImageMatrix,grayscaleImage,sizex,sizey,debug)

	#Unsharp masking
	unsharpedImageMatrix,unsharpedImage = unsharpMasking(grayscaleImageMatrix,grayscaleImage,sizex,sizey)

	#Thresholding
	thresholdedImageMatrix,thresholdedImage = thresholding(unsharpedImageMatrix,unsharpedImage,sizex,sizey)

	#Cropping edges
	croppedImageMatrix,croppedImage,sizex,sizey = cropping(thresholdedImage,sizex,sizey)
		
	return croppedImageMatrix,croppedImage,sizex,sizey
	
def processImage():

	#Get image data
	fileName,originalImageMatrix,sizex,sizey,compressionFactor = getImageInformation()
	
	#Process that image as a frame
	finalImageMatrix,finalImage,finalSizex,finalSizey = processFrame(originalImageMatrix,sizex,sizey,compressionFactor)
	
	#Print that image
	showImage(finalImageMatrix,finalSizex,finalSizey,baseCharset,fileName)
	
def processGif():

	fileName,originalGif,originalSizex,originalSizey,compressionFactor = getGifInformation()

	all_frames = []
	durations = []

	for frame in range(0,originalGif.n_frames):
	
		originalGif.seek(frame)
		frameMatrix = originalGif.load()
	
		finalFrameMatrix,finalFrame,sizex,sizey = processFrame(frameMatrix,originalSizex,originalSizey,compressionFactor)
		
		if (now):
			showImage(finalFrameMatrix,sizex,sizey,baseCharset,fileName)
		else:
			all_frames.append(finalFrameMatrix)
			durations.append(originalGif.info['duration']/9)
			
	if (not now):
		input('\nReady\n')
		i = 0
		for frame in all_frames:
			showImage(frame,sizex,sizey,baseCharset)
			time.sleep(1/durations[i])
			i = i + 1
		
if (gif):
	processGif()	
else:	
	processImage()
	



