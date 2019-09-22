from PIL import Image
from PIL import ImageDraw

import statistics
import math
import os
import time

'''
		TODO
		Post-processing smoothing
		Bilinear interpolation for rescaling
		Dithering instead of thresholding
		Gif suport
'''

#Show steps of image conversion?
debug = True

#Variable which determines the character set the image will be printed with
#[DARK, DARKGRAY, LIGHTGRAY, LIGHT]
baseCharset = [' ', '/', '1', 'B']

def getUserInputs(debug):
	#Gets the user inputs and returns the image matrix and size, along with the calculated compression factor

	#Get file name from user
	fileName = "Input/" + input("Image name? ")
	
	#Try opening the image
	originalImage = Image.open(fileName)
	originalImageMatrix = originalImage.load()
	sizex,sizey = originalImage.size
	
	#Gets the user-defined compression factor, if stated
	try:
		compressionFactor = int(input("Compression factor? "))
	except:
		compressionFactor = math.floor(sizex/250)
	
	if (debug):
		originalImage.show()
	
	return originalImageMatrix,sizex,sizey,compressionFactor

def nearestNeighborRescaling(ImageMatrix,sizex,sizey,compressionFactor,debug):
	#Rescales the image by compressionFactor, with the y axis being rescaled by 2*compressionFactor
	#due to characters being printed in 6x3

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
	
	return compressedImageMatrix,newSizex,newSizey
	
def newGrayScaleImage(ImageMatrix,sizex,sizey,debug):
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

def unsharpMasking(ImageMatrix,Image,sizex,sizey,debug):
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
	grayscaleImageCopy = grayscaleImage.copy()
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

def thresholding(ImageMatrix,Image,sizex,sizey,debug):
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
				if(newPixelValue >= 3*median/4):
					ImageDrawer.point([x,y],255)
				else:
					ImageDrawer.point([x,y],191)
			else:
				if(newPixelValue >= median/4):
					ImageDrawer.point([x,y],64)
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
	
def smoothing(ImageMatrix,Image,sizex,sizey,debug):
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
		
	ImageDrawer = ImageDraw.Draw(thresholdedImage)
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
	
def printImage(ImageMatrix,sizex,sizey,charset):
	os.system("cls")
	for y in range(sizey):
		print('')
		for x in range(sizex):
			if (croppedImageMatrix[x,y] == 0):
				print(charset[0],end='')
			elif (croppedImageMatrix[x,y] == 64):
				print(charset[1],end='')
			elif(croppedImageMatrix[x,y] == 191):
				print(charset[2],end='')
			else:
				print(charset[3],end='')
				
#Collect input data
originalImageMatrix,sizex,sizey,compressionFactor = getUserInputs(debug)

#Nearest Neighbor rescaling 
compressedImageMatrix,sizex,sizey = nearestNeighborRescaling(originalImageMatrix,sizex,sizey,compressionFactor,debug)

#Grayscale conversion
grayscaleImageMatrix,grayscaleImage = newGrayScaleImage(compressedImageMatrix,sizex,sizey,debug)

#Smoothing
#smoothedImageMatrix,smoothedImage = smoothing(grayscaleImageMatrix,grayscaleImage,sizex,sizey,debug)

#Unsharp masking
unsharpedImageMatrix,unsharpedImage = unsharpMasking(grayscaleImageMatrix,grayscaleImage,sizex,sizey,debug)

#Thresholding
thresholdedImageMatrix,thresholdedImage = thresholding(unsharpedImageMatrix,unsharpedImage,sizex,sizey,debug)

#Cropping edges
croppedImageMatrix,croppedImage,sizex,sizey = cropping(thresholdedImage,sizex,sizey)

#Printing the image
printImage(croppedImageMatrix,sizex,sizey,baseCharset)
