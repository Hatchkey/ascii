from AnimatedImage import AnimatedImage
from StaticImage import StaticImage
from Utils import Utils

import argparse

class ASCIIart:
    """Converts a given image or gif to ASCII and shows it on the terminal"""

    @staticmethod
    def convert(args):
        
        if (args.gif == True):
        
            AnimatedImage(args.fileName).show()
            
        else:
            
            StaticImage(args.fileName,args.glitch).show()
    
    
def main():
    """Application entrypoint"""
    
    control = Utils.InitParser().parse_args()

    ASCIIart.convert(control)
    
    return
    
if __name__ == "__main__":
    main()

