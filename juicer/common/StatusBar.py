import os
import sys

class StatusBar(object):
    def __init__(self):
        rows, columns = os.popen('stty size', 'r').read().split()

        self.width = int(columns) - 2
        self.percentage = 0.0

        sys.stdout.write("[%s]" % (" " * self.width))
        sys.stdout.flush()
        sys.stdout.write("\b" * (self.width + 1))
    
    def update(self, chunksize, totalsize):
        if chunksize > totalsize:
            sys.stdout.write("=" * self.columns)
            sys.stdout.flush()
        else:
            sys.stdout.write("=" * int((float(chunksize)*self.width) / float(totalsize)))
            sys.stdout.flush()
        
    def close(self):
        sys.stdout.write("\n")
