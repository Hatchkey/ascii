import argparse
import curses
import sys

class Utils:
    """General utilities"""
    @staticmethod
    def cursesScreenInit(sizeX,sizeY):

        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        stdscr.keypad(True)
            
        pad = curses.newpad(sizeY,sizeX)
        stdscr.nodelay(True)
        pad.nodelay(True)

        return stdscr,pad
    
    @staticmethod
    def cursesScreenEnd(stdscr):

        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

        return 

    @staticmethod
    def InitParser():
        parser = argparse.ArgumentParser(description="Convert an image or gif to ASCII text-art.")
        parser.add_argument('fileName', metavar='FILENAME', help = 'name of the file to be converted.' )
        # parser.add_argument('-d', dest ='debug' , action = 'store_true', default = False, help = 'debug (not currently implemented).')
        parser.add_argument('-g', dest ='gif'   , action = 'store_true', default = False, help = 'signal that a gif was passed as input.')
        parser.add_argument('-l', dest ='glitch', action = 'store_true', default = False, help = 'enable glitchy effects for images.')
      
        return parser

    @staticmethod
    def progressbar(it, prefix="", size=60, file=sys.stdout):
        count = len(it)
        def show(j):
            x = int(size*j/count)
            file.write("%s[%s%s] %i/%i\r" % (prefix, "#"*x, "."*(size-x), j, count))
            file.flush()        
        show(0)
        for i, item in enumerate(it):
            yield item
            show(i+1)
        file.write("\n")
        file.flush()