#!/usr/bin/env python

from generator.actions import Actions
import copy
import random
import struct

_INT_MAX_ = 0x000FFFFF
PUSH = 0x0
POP = 0x1
PUSHPC = 0x2
JMPZ = 0x3
SWAP = 0x4
DUP = 0x5
ADD = 0x6
SUB = 0x7
_END_ = 0xFFFFFFFF
FILLER = 0
_OPCODE_MASK_ = 0xFF
_OP_MASK_ = 0x00FFFFFF

_STACK_OVERFLOW_EXCP_MSG_ = "SOE\n"
_STACK_UNDERFLOW_EXCP_MSG_ = "SUE\n"
_INSNS_OVERFLOW_EXCP_MSG_ = "IOE\n"
_ILLEGAL_INSN_EXCP_MSG_ = "IIE\n"
_PC_EXCP_MSG_ = "IPE\n"

_MAX_STACK_SIZE_IN_BYTES_ = (4096)
_MAX_INSNS_SIZE_IN_BYTES_ = (8192)
_MAX_STACK_SIZE_ = (_MAX_STACK_SIZE_IN_BYTES_/4)
_MAX_INSNS_SIZE_ = (_MAX_INSNS_SIZE_IN_BYTES_/4)

def _INSN_TO_OPCODE_(insn) :
    return (insn & _OPCODE_MASK_)

def _INSN_TO_IMM_(insn) :
    return (insn >> 8)
    
def encodeInsn(opcode, op) :
    return ( (opcode & _OPCODE_MASK_) | ((op & _OP_MASK_) << 8) )

def toLittleEndian(i) :
    return (struct.pack("<I", i))

class StackMachine(Actions):

    def send_insn(self, opcode, op):
        if len(self.insns) >= _MAX_INSNS_SIZE_ :
          if not self.excp :
            self.excp = _INSNS_OVERFLOW_EXCP_MSG_
        else :
          insn = encodeInsn(opcode, op)
          self.insns.append(insn)
          self.write(toLittleEndian(insn))
        
    def start(self):
        self.stack = []
        self.insns = []
        self.excp = ""

    def generate_work(self):
        pass

    def gen_push(self):
        if len(self.stack) >= _MAX_STACK_SIZE_ :
          return
          if not self.excp :
            self.excp = _STACK_OVERFLOW_EXCP_MSG_ 
        op = random.randint(0,_INT_MAX_)
        self.send_insn(PUSH, op)
        self.stack.append(op)

    def gen_pop(self):
        if self.stack :
          self.stack.pop()
        else :
          if not self.excp :
            self.excp = _STACK_UNDERFLOW_EXCP_MSG_
  
        self.send_insn(POP, FILLER)

    def gen_add(self):
        if len(self.stack) >= 2 :
          self.stack[-2] += self.stack[-1]
          self.stack[-2] &= 0xFFFFFFFF
          self.stack.pop()
        else :
          if not self.excp :
            self.excp = _STACK_UNDERFLOW_EXCP_MSG_
        
        self.send_insn(ADD, FILLER)

    def gen_sub(self):
        if len(self.stack) >= 2 :
          self.stack[-2] -= self.stack[-1]
          self.stack[-2] &= 0xFFFFFFFF
          self.stack.pop()
        else :
          if not self.excp :
            self.excp = _STACK_UNDERFLOW_EXCP_MSG_

        self.send_insn(SUB, FILLER)

    def gen_swap(self):
        if self.stack :
          op = random.randint(0,len(self.stack)) #note that this can cause an underflow - which is good
          if (op >= len(self.stack)) :
            if not self.excp :
              self.excp = _STACK_UNDERFLOW_EXCP_MSG_
          else :
            temp = self.stack[-1] 
            self.stack[-1] = self.stack[len(self.stack) - 1 - op]
            self.stack[len(self.stack) - 1 - op] = temp

          self.send_insn(SWAP, op) #note that this can cause an underflow - which is good

    def gen_dup(self):
        if self.stack :
          op = random.randint(0,len(self.stack)) #note that this can cause an underflow - which is good
          if (op >= len(self.stack)) :
            if not self.excp :
              self.excp = _STACK_UNDERFLOW_EXCP_MSG_
          else :
            if len(self.stack) >= _MAX_STACK_SIZE_ :
              return

            self.stack.append(self.stack[len(self.stack) - 1 - op])

          self.send_insn(DUP, op) #note that this can cause an underflow - which is good

    def gen_loop(self):
        c = random.randint(0,10) 
        if not c :
          if not self.excp :
            self.send_insn(PUSH, _INT_MAX_)
            self.send_insn(PUSH, 0)
            self.send_insn(JMPZ, FILLER)
            self.excp = _PC_EXCP_MSG_
        elif c > 5 :
          self.send_insn(PUSHPC, FILLER)
          self.send_insn(PUSH, 5)
          self.send_insn(ADD, FILLER)
          self.send_insn(PUSH, 0)
          self.send_insn(JMPZ, FILLER)
        else :
          self.send_insn(PUSHPC, FILLER)
          self.send_insn(PUSH, 1)
          self.send_insn(JMPZ, FILLER)

    def end(self):
        if self.excp == _INSNS_OVERFLOW_EXCP_MSG_ :
          self.read(length=len(self.excp), expect=self.excp)
        else :
          self.write(toLittleEndian(_END_))
          if self.excp :
            self.read(length=len(self.excp), expect=self.excp)
          else :
            if self.stack :
                self.read(length=4, expect=toLittleEndian(self.stack[-1]))
            else :
              self.read(length=len(_STACK_UNDERFLOW_EXCP_MSG_), expect=_STACK_UNDERFLOW_EXCP_MSG_)
           

