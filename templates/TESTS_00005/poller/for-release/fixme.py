#!/usr/bin/python

import sys
import re

replaceme_dict = { "push" : "PUSH_MNEMONIC", 
                   "pop" : "POP_MNEMONIC", 
                   "mov" : "MOV_MNEMONIC", 
                   "add" : "ADD_MNEMONIC",
                   "sub" : "SUB_MNEMONIC",
                   "mul" : "MUL_MNEMONIC",
                   "div" : "DIV_MNEMONIC",
                   "out" : "OUT_MNEMONIC",
                   "mod" : "MOD_MNEMONIC",
                   "shl" : "SHL_MNEMONIC",
                   "shr" : "SHR_MNEMONIC",
                   "exc" : "EXC_MNEMONIC",
                   "swp" : "SWP_MNEMONIC" }

for arg in sys.argv[1:] :
  print "Processing: %s" % arg
  out = open(arg + ".template", "w")
  for l in open(arg) :
    mat = re.match("(\s*<data>)(\w+)(\s.*\n)$", l)
    o = l
    if mat :
      if mat.group(2) not in replaceme_dict :
        print "[%s] does not exist in dict" % l
      else :
        o = mat.group(1) + "<REPLACEME>" + replaceme_dict[mat.group(2)] + "</REPLACEME>"
        lines = mat.group(3).split("\\n")
        if len(lines) > 2:
          bFirst = True
          for _ in lines :
            mat2 = re.match("(\w+)(\s.*)", _)
            if not bFirst :
              o += "\\n"
            if mat2 :
              o += "<REPLACEME>" + replaceme_dict[mat2.group(1)] + "</REPLACEME>" + mat2.group(2)
            else :
              o += _

            bFirst = False
        else :
          o += mat.group(3)
          
    else :
      #print "[%s] Doesn't match re" % l
      pass
    out.write(o)
  out.close() 
