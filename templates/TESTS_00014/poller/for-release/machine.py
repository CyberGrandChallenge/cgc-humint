#!/usr/bin/env python

from generator.actions import Actions
import random
import string
import re

MAX_SIZE = (4096 * 4)

def int2str(i) :
  return "".join([chr(i & 0xFF), chr((i >> 8) & 0xFF), chr((i >> 16) & 0xFF), chr((i >> 24) & 0xFF)])

class bin2hex(Actions):

    def start(self):
        self.string = "".join([chr(random.randint(0,255)) for _ in xrange(random.randint(1,(MAX_SIZE / 2) - 1))])
        self.hexstring = self.string.encode("hex")

    def dowork(self) :
        numBytes = len(self.hexstring)
        self.write(int2str(numBytes))
  
        self.write(self.hexstring)

        self.read(length=len(self.string), expect=self.string)
       
    def end(self):
        pass



