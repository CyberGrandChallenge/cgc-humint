#!/usr/bin/env python

from generator.actions import Actions, Variable
import random
import string
import re


#define BUF_SIZE 128
BUF_SIZE = 128

#define TOKEN_SIZE 4
TOKEN_SIZE = 4

#define TOKEN_START_PAD "123"
#define TOKEN_START_PAD_LEN 3
TOKEN_START_PAD_LEN = 3

#define TOKEN_END_PAD "321"
#define TOKEN_END_PAD_LEN 3
TOKEN_END_PAD_LEN = 3

#define TOKEN_BUF_SIZE (TOKEN_START_PAD_LEN + TOKEN_SIZE + TOKEN_END_PAD_LEN)
TOKEN_BUF_SIZE = TOKEN_START_PAD_LEN + TOKEN_SIZE + TOKEN_END_PAD_LEN

class PalindromMaker(Actions):

    def start(self) :
        self.string = "".join([chr(random.randint(0,255)) for _ in xrange(random.randint(1, (BUF_SIZE / 2) -1))])
        self.nonce = Variable('nonce')
        self.nonce.set_slice(TOKEN_START_PAD_LEN, TOKEN_START_PAD_LEN + TOKEN_SIZE)

    def genpalindrome(self) :
        self.read(length=TOKEN_BUF_SIZE, assign=self.nonce)

        self.write(self.nonce)

        self.write(self.string)
        
        self.read(length=len(self.string)*2, expect=self.string + "".join([_ for _ in reversed(self.string)]))

    def end(self):
        pass



