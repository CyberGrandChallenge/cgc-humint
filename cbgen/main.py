#!/usr/bin/python

import os
from os.path import join, isdir, islink
import argparse
import random
import sys
import re
from . import configParser
from . import obfuscator

_PREFIX_ = configParser._PREFIX_
_NOOBF_SUFFIX_ = ".noobf"


class ObfsConfig() :
  def __init__(self, config=None) :
    '''
    obfs_useInt = True
    obfs_useFloat = False
    obfs_useInline = False
    obfs_useRVals = False
    obfs_useLVals = False
    obfs_useFunctions = False
    '''
    self.bUseInt = True
    self.bUseFloat = True
    self.bUseInline = True
    self.inlineChance = 10
    self.bUseRVals = True
    self.bUseLVals = True
    self.bUseFunctions = True
    #obfs_varTypes = ["int", "unsigned int", "long", "unsigned long", "long long", "unsigned long long", "double", "float"]
    self.varTypes = ["int", "unsigned int", "long", "unsigned long"]
    self.numFunctions = 5
    self.minFuncParams = 0
    self.maxFuncParams = 3
    self.numVars = 2
    self.ifelseLevel = 0
    self.excludeFunctions = []
    self.excludeVars = []
    
    for k in config :
      if k == "obfs_useInt" :
        if config[k] in ["1", "T", "True", "true", "t"]:
          self.bUseInt = True
        else :
          self.bUseInt = False
        continue
      if k == "obfs_useFloat" :
        if config[k] in ["1", "T", "True", "true", "t"]:
          self.bUseFloat = True
        else :
          self.bUseFloat = False
        continue
      if k == "obfs_useInline" :
        if config[k] in ["1", "T", "True", "true", "t"]:
          self.bUseInline = True
        else :
          self.bUseInline = False
        continue
      if k == "obfs_useRVals" :
        if config[k] in ["1", "T", "True", "true", "t"]:
          self.bUseRVals = True
        else :
          self.bUseRVals = False
        continue
      if k == "obfs_useLVals" :
        if config[k] in ["1", "T", "True", "true", "t"]:
          self.bUseLVals = True
        else :
          self.bUseLVals = False
        continue
      if k == "obfs_useFunctions" :
        if config[k] in ["1", "T", "True", "true", "t"]:
          self.bUseFunctions = True
        else :
          self.bUseFunctions = False
        continue
      if k == "obfs_inlineChance" :
        self.inlineChance = int(config[k])
        continue
      if k == "obfs_numFunctions" :
        self.numFunctions = int(config[k])
        continue
      if k == "obfs_minFuncParams" :
        self.minFuncParams = int(config[k])
        continue
      if k == "obfs_maxFuncParams" :
        self.maxFuncParams = int(config[k])
        continue
      if k == "obfs_ifelseLevel" :
        self.ifelseLevel = int(config[k])
        continue
      if k == "obfs_varTypes" :
        self.varTypes = [_.strip() for _ in config[k].split(",")]
        continue
      if k == "obfs_excludeFuncs" or k == "obfs_excludeFunctions": 
        self.excludeFunctions = [_.strip() for _ in config[k].split(",")]
        print "sef %s" % self.excludeFunctions
        continue
      if k == "obfs_excludeVars": 
        self.excludeVars = [_.strip() for _ in config[k].split(",")]
        continue
      

def error(s, errno=-1) :
  sys.stderr.write("ERROR: " + s)
  exit(errno)

def warn(s) :
  sys.stderr.write("WARNING: " + s)

def mkdir(path) :
  if not os.path.exists(path) :
    try :
      os.makedirs(path)
    except OSError as exception :
      if exception.errno != -EEXIST :
        raise

def escapifyStr(s) :
  #We escape only certain characters on purpose so its more fragile. Errors
  # should show up more readily.
  temp = s
  temp = temp.replace("\n", "\\n")
  temp = temp.replace("\t", "\\t")
  return temp

def copyFile(src, dst) :
  out = open(dst, "w")
  for l in open(src) :
    out.write(l)
  out.close()

def generateMacroDef(m, config) :
  if not m in config :
    return ("")
  d = config[m]

  ret = "#define " + _PREFIX_ + m + " " + escapifyStr(d[1]) + "\n"

  return ret

#starts with a letter or underscore followed by any number of letters digits or underscores
_C_ID_REGEX_ = "[a-zA-Z_][a-zA-Z0-9_]*" 
_C_OP_REGEX_ = "[><=/+*-][=]*" #no escapes needed here

_C_NOT_ID_REGEX_ = "[^a-zA-Z0-9_]"

def findAndReplaceMacro(l, c) :
  begin = l.find(c)
  res = ""
  curStart = 0
  bSub = False
  while begin != -1 :  
    if ( begin == 0 #the macro appears in the beginning of a line
         or ( re.match(_C_NOT_ID_REGEX_, l[curStart + begin - 1]) #or the char before it is not an ID char
              and ( ( (curStart + begin + len(c)) >= len(l) ) #and it is at the end of the line
                    or (re.match(_C_NOT_ID_REGEX_, l[curStart + begin + len(c)])) #it ends with a non-ID char
                  )
            )
       ) :
      res += l[curStart:curStart + begin] + _PREFIX_ + c #substitute the MACRO
      curStart = curStart + begin + len(c) #move current starting point up
      bSub = True
    else : #if the match was a sub-match (e.g., BUF in BUF_SIZE) then just skip it
      res += l[curStart:curStart + begin + len(c)]
      curStart = curStart + begin + len(c)
      
    begin = l[curStart:].find(c) #look for it again 
  
  #now finish off the last parts of the line
  res += l[curStart:]

  l = res #update the working copy of the line with the current result in case there are more macros
  return (l)

def substituteMacros(line, config, commentStart="//", bIsC = True) :
  ret = ""
  l = line #we need a working copy of the line
  for c in config :
    l = findAndReplaceMacro(l, c)

  if not l == line :
    if not bIsC :
      ret = commentStart + line
    else :
      #here we need to see if its a line continuation or not
      _l = line.rstrip()
      ret = "/** " + _l + " **/"
      if _l.endswith('\\') :
        ret += "\\"
      ret += "\n"  
 
  ret += l
  return (ret)

#The basic idea is to go through the file and then do the appropriate substitutions
def processhFile(src, dst, config) :
  out = open(dst, "w")
  for l in open(src) :
    #we are skipping the compilation step - hope it works fine
    toks = re.match("\s*#define\s+(" + _C_ID_REGEX_ + ")\s+", l)
    if toks : #if we have a new definition
      #see if it is part of our config
      out.write(l) #write the original definition out
      m = toks.group(1)
      if m in config : #if its one of the keys
        out.write(generateMacroDef(m, config)) #write the new def out
      continue #we are done with this line 
    else :    
      #if it is not a definition - then we should try to do a search 
      # and substitute
      out.write(substituteMacros(l, config))
  out.close()

def processcFile(src, dst, config) :
  processhFile(src, dst, config)

#NOTE: I am going to make these simple because we should really
# use libclang in the future to get these right
# This is for many reasons including what happens if the function
# declaration takes over multiple lines.
#parses a line of c-code to find function declarations
# the basic idea is that a function declaration should only
# have one pair of parentheses with the function name 
# showing up before the open paren and then the return type
# showing up before the function name separated by whitespace
# the final discerning factor is the presence of the open {
# -- if we don't see the { then that means this could also
# just be a function call.
# There must also not be any assignments. (We can't check < or >
#   because of templates in C++. This is why we need libclang
#Returns type, funcName, params, bBrace
# e.g. unsigned long long fun(unsigned int a, string b) {
#   should return unsigned long long, fun, (unsigned int a, string b), True

#We also can't allow for #defines

_DISALLOWED_FUNC_OPS_REGEX_ = "[\^!=+/};\-#]"

def parseFunctionDefinition(line) :
  retType = None
  funcName = None
  params = None
  bBrace = False

  #if its a macro then skip
  if line.strip().endswith("\\") :
    return retType, funcName, params, bBrace
 
  lp = 0
  rp = 0
  bracep = 0
  lp = line.find('(')
  if (lp == -1) or (lp == 0) or (line.find('(', lp + 1) != -1) :
    return retType, funcName, params, bBrace

  rp = line.find(')')
  if (rp == -1) or (rp <= lp) or (line.find(')', rp + 1) != -1) :
    return retType, funcName, params, bBrace

  if re.search(_DISALLOWED_FUNC_OPS_REGEX_, line) :
    return retType, funcName, params, bBrace
    
  bracep = line.find('{')
  if (bracep != -1) :
    if bracep <= rp or line.find('{', bracep+1) != -1 :
      return retType, funcName, params, bBrace
    else :
      bBrace = True
  
  left = line[0:lp]
  params = line[lp:rp +1]
  right = line[rp+1:] 
  
  ls = left.split()
  rs = right.split()

  if len(ls) < 2 : #if there are less than two items then we quit again
    return retType, funcName, params, bBrace

  funcName = ls[-1] #the last item is the function name
  retType = left[0:len(left) - len(funcName)] #retType is everything else

  return retType, funcName, params, bBrace

  #NOTE: by this time, we can still have false positives but this should
  # be fine for now

#This follows the same idea as parseFunctionDefinition but does it
# for if, else, do, while and for loops - 
# the basic idea is to look for any of these key words followed by a {
# Once again, this is not perfect as an if with a single statement
# won't be captured.
#The heuristic is as follows:
# \s*[if|while|for]\s*(.*).*{
# We don't follow this exactly because we assume that the original code is okay
#   that is we don't have to worry about malformed expressions and so 
#   we simply assume that if we see one of those keywords before a ( we are good
#Returns keyword, condition, end, bBrace
def parseSubblocks(line) :
  keyword = None
  condition = None
  end = None
  bBrace = False

  #if its a macro then skip
  if line.strip().endswith("\\") :
    return keyword, condition, end, bBrace
 
  lp = line.find('(')
  if lp != -1 :
    left = line[0:lp]
    args = left.split()
    if "if" in args :
      keyword = "if"  
    elif "while" in args :
      keyword = "while"
    elif "for" in args :
      keyword = "for"
   
    rp = line.rfind(')')  
    if rp != -1 :
      condition = line[lp:rp+1]
      end = line[rp+1:]

    if line.find('{') != -1 :
      bBrace = True
    
  return keyword, condition, end, bBrace

def parseVarDecls(line) :
  ret = []
  l = line.strip();
  #if its a comment then just return
  if l.startswith("//") or l.startswith("/*") :
    return []
  
  #if its a macro then skip
  if l.endswith("\\") :
    return []
 
  #can't handle multi line ones
  if not l.endswith(";") :
    return []


  #can't handle pointers
  if l.find("*") != -1 :
    return []

  varType = ""

  #we do a greedy match by going in reversed sorted order
  for t in reversed(sorted(obfuscator._ALL_TYPES_)) :
    #if it starts with the type and has a whitespace
    # otherwise we might match unsigned long longNum
    if l.startswith(t) and re.match(t+"\s", l):
      varType = t
      break

  if not varType :
    return []

  rest = l[len(varType):].strip()
  rest = rest[0:rest.find(";")]

  #now we have a type plus a bunch of stuff which may or may not
  # be a variable - it could be a function
  cvars = rest.split(",") #in case there are multiple vars
  for c in cvars :
    temp = c.split("=") #in case there is an initializer
    if len(temp) > 2 :
      return []
 
    if re.match("[a-zA-Z_][\w]*", temp[0]) :

      if re.search("[\[\(]", temp[0]) :
        #There should never be a left parenthesis in a variable declaration
        # - at least not on the variable name side, it is possible on the
        #   intializer side
        #Also we don't handle arrays
        return []
      else :
        val = None
        if len(temp) == 2 :
          val = temp[1]
 
        ret.append(obfuscator.CVariable(temp[0], varType, val))

    else :
      #doesn't look like a valid variable declaration
      return []

  return ret

def genVars(name, numVars, varTypes) :
  _vars = []
  for i in xrange(numVars) :
    _name = obfuscator._PREFIX_ + name + "%u" % i
    _type = random.choice(varTypes)
    _val = obfuscator.typeToZeroVal(_type)
    _vars.append(obfuscator.CVariable(_name, _type, _val))

  return _vars

def genFunctionCall(lval, params, func) :
  c = random.choice(lval)
  ret = "%s = " % (c.varName)
  
  if c.varType != func.returnType :
    ret += "(%s) " % c.varType

  ret += "%s(" % func.funcName

  bFirst = True
  for i in func.params :
    if not bFirst :
      ret += ", "

    c = random.choice(params)
    if (i.varType != c.varType) :
      ret += "(%s)" % i.varType
    
    ret += c.varName 

    bFirst = False
  ret += ");\n"

  return (ret)
  
def obfuscatecFile(src, dst, config, obfs_config, bIsHFile = False) :
  #in this function - what we will do is go through the src file and look for the beginning of 
  # functions as well as the beginning of blocks (e.g., if, else, while, for, do-while) as 
  # well as the end of blocks (functions are little tricky because of the return statement, 
  # but we can just use some simple heuristics). Once found, we will generate some dead code
  # for insertion in place. Also, we will try to capture some variable definitions and use
  # them as rvals. 
  out = open(dst, "w")
  bWaitingOnBrace = False
  bWasFunction = False
  subblockNumber = 0
  lineNum = 0
  indentAmt = 0
  bFunctionsInserted = False
  numFunctionsInserted = 0
  bMultilineComment = False
  bSkipCurrentFunc = False
  prevLine = ""

  #here we will use two arrays to keep track of the items that are currently within scope
  #By default, functions are always in scope within a single file so we don't have to worry
  # much about this
  funcsInScope = [] 
  #The problem with variables is that they are only in scope within the current set of
  # braces. This means we will have to keep a stack of open and close braces.
  # This is difficult without a parser, and so what we will do instead is just use the local
  # variables that are within function scope - we will not reuse the ones within loops
  # or conditionals.
  #Also, as another precaution, we will remove all vars from the scope whenenver we *think*
  # we see the corresponding close brace for the function
  varsInScope = []
  localVarsInScope = []

  genVarsInFunc = []
  genLValNum = 0
  subblockVars = []

  for l in open(src) :
    #replace \r\n if there is one
    if l.endswith("\r\n") :
      l = l[0:len(l)-2] + "\n"

    #FIXME: We should do comment detection first - but those multi-line comments are nasty
    # if the comments are not in their own lines - e.g. int i = 0; //this is a comment
    # and char buf[] = "//this is not a comment";
    _l = l.strip()
    if bMultilineComment :
      out.write(l) #we are still in a comment so just write it out
      if (_l.endswith("*/")) :
        bMultilineComment = False
      elif _l.find("*/") != -1 :
        print "Strange is [%s] in line #%u in %s end of a multiline comment?" % (l, lineNum, src)

      prevLine = l
      continue
  
    if _l.startswith("/*") :
      if _l.find("*/") == -1 :
        bMultilineComment = True
      else :
        bMultilineComment = False
      out.write(l) #comments      
      prevLine = l
      continue

    if _l.startswith("//") :
      out.write(l)
      prevLine = l
      continue

    lineNum += 1
    args = l.split() #split this up based on whitespace
    if not bSkipCurrentFunc and bWaitingOnBrace :
      if len(args) > 0 : #if we are waiting for braces
        if args[0] == '{' :
          if (len(args) == 1) or args[1].startswith('//') or (args[1].startswith('/*') and args[-1].endswith("*/")) :
            out.write(l)
            _localVars = []
            if bWasFunction :
              localVarsInScope = []
              genVarsInFunc = genVars("v", obfs_config.numVars, obfs_config.varTypes)
              #we also update the vars in scope
              varsInScope = genVarsInFunc
              _localVars = genVarsInFunc
              genLValNum = 0
            else :
              subblockVars = genVars("v_s", obfs_config.numVars, obfs_config.varTypes)
              _localVars = subblockVars

            _rVals = []
            if obfs_config.bUseRVals and localVarsInScope:
              _rVals = localVarsInScope

            _lVals = []
            _tempVar = None
            if obfs_config.bUseLVals and localVarsInScope:
              _lVals = [random.choice(localVarsInScope)]
              _tempVar = obfuscator.CVariable(obfuscator._PREFIX_ + "lval_%u" % genLValNum, _lVals[0].varType, _lVals[0].varName)
              out.write((" " * indentAmt) + _tempVar.varType + " " + _tempVar.varName + " = " + _tempVar.varVal + ";\n")
              genLValNum += 1

            out.write(obfuscator.genDeadCode(localVars = _localVars, lVals = _lVals, rVals = _rVals, indentationAmt = indentAmt, bPrefix = False, ifelseLevel = obfs_config.ifelseLevel)) 

            if obfs_config.bUseFunctions and funcsInScope:
              out.write((" " * indentAmt) + genFunctionCall(lval = _localVars + _lVals, params = _localVars + _lVals + _rVals, func = random.choice(funcsInScope)))

            if _tempVar :
              out.write((" " * indentAmt) + _lVals[0].varName + " = " + _tempVar.varName + ";\n")


            bWaitingOnBrace = False
            prevLine = l
            continue #move on to the next thing
          elif bWasFunction:
            warn("Strange - we are looking for a left brace, but found something other than whitespace, or comments in [%s] in line #%u in %s\n" % (l, lineNum, src))

        elif bWasFunction and (not ((args[0].startswith('//') or args[0].startswith('/*')))) :
          warn("Strange - we are looking for a left brace, but found something other than whitespace, or comments in [%s] in line #%u in %s\n" % (l, lineNum, src))
          out.write(l)
          prevLine = l
          continue
        elif not bWasFunction :
          #it wasn't a function so let's just assume that its a if/else/loop statement
          warn("Assuming its a single if/else/loop statement in line #%u in %s. Might be a good idea to use braces: \n" % (lineNum, src))
          warn("  " + prevLine)
          warn("  " + l)
          bWaitingOnBrace = False
          #write it out and skip
          out.write(l)
          prevLine = l
          continue

      else : #waiting on a brace and just see whitespace
        pass
    
    else :    
      retType, funcName, params, bBrace = parseFunctionDefinition(l)
      if retType != None and funcName != None and params != None :
        #print retType
        #print funcName
        #print params
        #print bBrace

        #we have found a function so it is a good time to insert our new function definitions
        #Note that THIS WILL NOT WORK if the first function definition is 
        # within comments because these new functions will also be inserted
        # within the comments
        if not bIsHFile and not bFunctionsInserted and obfs_config.bUseFunctions:
        
          funcsInScope = []
          for i in xrange(obfs_config.numFunctions) :
            _numParams = random.randint(obfs_config.minFuncParams, obfs_config.maxFuncParams)
            _params = []
            for j in xrange(_numParams) :
              _params.append(obfuscator.CVariable(obfuscator._PREFIX_ + "p%u" % j, random.choice(obfs_config.varTypes), None))

            _func = obfuscator.CFunction(obfuscator._PREFIX_ + "func%u" % i, random.choice(obfs_config.varTypes),_params)

            funcsInScope.append(_func)

            out.write(obfuscator.genDeadFunction(_func.funcName, returnType = _func.returnType, params=_params, bPrefix=False))

          bFunctionsInserted = True  

        #we found a function - reset the subblock number
        subblockNumber = 0
        indentAmt = 2 # default indent of 2
        i = 0
        while l[i] not in configParser.WORD :
          if l[i] == "\t" :
            indentAmt += 4
          else :
            indentAmt += 1
          i += 1

        if funcName in obfs_config.excludeFunctions :
          bSkipCurrentFunc = True
          out.write(l)
          prevLine = l
          continue #move on
        else :
          bSkipCurrentFunc = False

        if bBrace :
          #and it already has a left brace, so lets insert our obfuscation
          out.write(l)
          localVarsInScope = []
          genVarsInFunc = genVars("v", obfs_config.numVars, obfs_config.varTypes)
          #we also update the vars in scope
          varsInScope = genVarsInFunc
          _localVars = genVarsInFunc
          genLValNum = 0

          #The following lines are the same as above
          _rVals = []
          if obfs_config.bUseRVals and localVarsInScope:
            _rVals = localVarsInScope

          _lVals = []
          _tempVar = None
          if obfs_config.bUseLVals and localVarsInScope:
            _lVals = [random.choice(localVarsInScope)]
            _tempVar = obfuscator.CVariable(obfuscator._PREFIX_ + "lval_%u" % genLValNum, _lVals[0].varType, _lVals[0].varName)
            out.write((" " * indentAmt) + _tempVar.varType + " " + _tempVar.varName + " = " + _tempVar.varVal + ";\n")
            genLValNum += 1

          out.write(obfuscator.genDeadCode(localVars = _localVars, lVals = _lVals, rVals = _rVals, indentationAmt = indentAmt, bPrefix = False, ifelseLevel = obfs_config.ifelseLevel)) 

          if obfs_config.bUseFunctions and funcsInScope:
            out.write((" " * indentAmt) + genFunctionCall(lval = _localVars + _lVals, params = _localVars + _lVals + _rVals, func = random.choice(funcsInScope)))
          
          if _tempVar :
            out.write((" " * indentAmt) + _lVals[0].varName + " = " + _tempVar.varName + ";\n")
          
          bWaitingOnBrace = False
          bWasFunction = False
          prevLine = l
          continue #move on to the next thing
        else :
          bWaitingOnBrace = True
          bWasFunction = True
      elif not bSkipCurrentFunc:
        keyword, condition, end, bBrace = parseSubblocks(l)
        if keyword != None and condition != None and end != None :
          #we found a subblock so increase the number
          subblockNumber += 1
          #print keyword
          #print condition
          #print end
          indentAmt = 2 # default indent of 2
          i = 0
          while l[i] not in configParser.WORD :
            indentAmt += 1
            i += 1

          if bBrace :
            out.write(l)
          
            subblockVars = genVars("v_s", obfs_config.numVars, obfs_config.varTypes)
            _localVars = subblockVars

            #The following lines are the same as above
            _rVals = []
            if obfs_config.bUseRVals and localVarsInScope:
              _rVals = localVarsInScope
  
            _lVals = []
            _tempVar = None
            if obfs_config.bUseLVals and localVarsInScope:
              _lVals = [random.choice(localVarsInScope)]
              _tempVar = obfuscator.CVariable(obfuscator._PREFIX_ + "lval_%u" % genLValNum, _lVals[0].varType, _lVals[0].varName)
              out.write((" " * indentAmt) + _tempVar.varType + " " + _tempVar.varName + " = " + _tempVar.varVal + ";\n")
              genLValNum += 1
  
            out.write(obfuscator.genDeadCode(localVars = _localVars, lVals = _lVals, rVals = _rVals, indentationAmt = indentAmt, bPrefix = False, ifelseLevel = obfs_config.ifelseLevel)) 

            if obfs_config.bUseFunctions and funcsInScope :
              out.write((" " * indentAmt) + genFunctionCall(lval = _localVars + _lVals, params = _localVars + _lVals + _rVals, func = random.choice(funcsInScope)))
            
            if _tempVar :
              out.write((" " * indentAmt) + _lVals[0].varName + " = " + _tempVar.varName + ";\n")

            bWaitingOnBrace = False
            bWasFunction = False
            prevLine = l
            continue
          else :
            bWaitingOnBrace = True
            bWasFunction = False

        else : #no subblocks either - maybe variables?
          #right now we only look for variables in the main function
          #FIXME: This will not work if they happened to declare
          # variables within braces
          # e.g. void f(void) { int i = 0; { int j = 1; } }
          # will identify both i and j as within function scope which is wrong
          if subblockNumber == 0 :
            localVars = parseVarDecls(l)
            if localVars :
              localVarsInScope += filter(lambda _ : _.varName not in obfs_config.excludeVars, localVars)
              #we found some variables

    out.write(l)
    prevLine = l

    if bSkipCurrentFunc :
      continue

    #if we have a 
    #FIXME: We need a better way of finding a safe place to inline obfuscations
    if obfs_config.bUseInline and random.randint(0,100) < obfs_config.inlineChance+100 and l.strip().endswith(";") :
      #The problem is that ending with a semi-colon is not perfect
      # might be a struct definition for example 
      # so what we do is we limit it to C-statements that are assignments
      if re.match("\s*(\w+)\s*=\s.*", l) :
        #This should not treat the delcarations as valid either
        #print "Found: %s" % l
        _localVars = varsInScope

        #The following lines are the same as above
        _rVals = []
        if obfs_config.bUseRVals and localVarsInScope:
          _rVals = localVarsInScope
  
        _lVals = []
        _tempVar = None
        if obfs_config.bUseLVals and localVarsInScope:
          _lVals = [random.choice(localVarsInScope)]
          _tempVar = obfuscator.CVariable(obfuscator._PREFIX_ + "lval_%u" % genLValNum, _lVals[0].varType, _lVals[0].varName)
          out.write((" " * indentAmt) + _tempVar.varType + " " + _tempVar.varName + " = " + _tempVar.varVal + ";\n")
          genLValNum += 1
  
        out.write(obfuscator.genDeadCode(localVars = _localVars, lVals = _lVals, rVals = _rVals, bDeclaration=False, indentationAmt = indentAmt, bPrefix = False, ifelseLevel = obfs_config.ifelseLevel)) 

        if obfs_config.bUseFunctions and funcsInScope:
          out.write((" " * indentAmt) + genFunctionCall(lval = _localVars + _lVals, params = _localVars + _lVals + _rVals, func = random.choice(funcsInScope)))
            
        if _tempVar :
          out.write((" " * indentAmt) + _lVals[0].varName + " = " + _tempVar.varName + ";\n")

      else :
        #print "Not Found: %s" % l
        pass
  

def generatePythonDef(m, config) :
  ret = _PREFIX_ + m + " = " + escapifyStr(config[m][1]) + '\n' 
  return (ret)

def processpyFile(src, dst, config) :
  out = open(dst, "w")
  for l in open(src) :
    #basically, we find definitions (i.e. with =) and replace them (similar to #define)
    toks = re.match("\s*(" + _C_ID_REGEX_ + ")\s*=\s*[^=]", l) #
    if toks and toks.group(1) in config: #if we have a new assignment
      #This regex is not perfect because it will match any assignment
      # this is why we need to make sure that the lval is in the group
      # as well
      #NOTE: This will NOT work if the constant is used as an lval after
      # definition.
      out.write(l)
      m = toks.group(1)
      if m in config :
        out.write(generatePythonDef(m, config))
      continue
    else :
      out.write(substituteMacros(l, config, commentStart = '#', bIsC = False))
  out.close()
     

XML_TOKEN_START = "<REPLACEME>"
XML_TOKEN_END = "</REPLACEME>"
def processxmlTemplateFile(src, dst, config) :
  extPos = dst.rfind(".template")
  if extPos == -1 :
    copyFile(src, dst)
    return
    
  dst = dst[0:extPos]
  out = open(dst, "w")
  for l in open(src) :
    temp = ""
    cur = 0
    beg = l.find(XML_TOKEN_START, cur)
    end = l.find(XML_TOKEN_END, beg)
    while beg != -1 and end != -1 :
      temp += l[cur : beg]
      m = l[beg + len(XML_TOKEN_START) : end]
      if not m in config :
        error ("In file %s : The configuration parameter used in %s was not found in config\n" % (src, m))
      temp += configParser.getRawData(m, config)
      cur = end + len(XML_TOKEN_END)
      beg = l.find(XML_TOKEN_START, cur)
      end = l.find(XML_TOKEN_END, beg)
    if cur < len(l) :
      temp += l[cur :]
    
    out.write(temp)

  out.close()

def processDir(spath, dpath, config, obfs_config, bNoGen) :
  files = os.listdir(spath)
  for f in files:
    sfpath = join(spath,f)
    dfpath = join(dpath,f)
    if sfpath.endswith(_NOOBF_SUFFIX_) :
      warn("There are already files that ends with %s\n" % _NOOBF_SUFFIX_)

    if islink(sfpath) :
      error("Links are not supported\n")
    elif isdir(sfpath) :
      mkdir(dfpath)
      processDir(sfpath, dfpath, config, obfs_config, bNoGen) #process this subdirectory
    else : #its a file 
      if sfpath.endswith(".c") or sfpath.endswith(".h") :
        bIsHFile = False
        if sfpath.endswith(".h") :
          bIsHFile = True

        if not obfs_config and not bNoGen:
          processcFile(sfpath, dfpath, config)
        else :
          if bNoGen :
            copyFile(sfpath, dfpath + _NOOBF_SUFFIX_)
          else :
            processcFile(sfpath, dfpath + _NOOBF_SUFFIX_, config)

          obfuscatecFile(dfpath + _NOOBF_SUFFIX_, dfpath, config, obfs_config, bIsHFile)
      elif not bNoGen and sfpath.endswith(".py") :
        processpyFile(sfpath, dfpath, config)
      elif not bNoGen and sfpath.endswith(".xml.template") :
        processxmlTemplateFile(sfpath, dfpath, config)
      else :
        copyFile(sfpath, dfpath)

def main() :
  parser = argparse.ArgumentParser(description="Generates a new CB Source Tree given a template Soruce Tree\n")
  parser.add_argument("-t", "--template", type=str, required=True, help="The CB template directory")
  parser.add_argument("-s", "--seed", type=str, required=False, help="seed to use for random")
  parser.add_argument("-o", "--outdir", type=str, required=False, help="Name of directory to output the files. Otherwise defaults to [template].out")
  parser.add_argument("-c", "--config", type=str, required=True, help="Config file to use")
  parser.add_argument("-n", "--noobfs", required=False, default=False, action="store_true", help="Disable Obfuscation")
  parser.add_argument("-x", "--nogen", required=False, default=False, action="store_true", help="Disable Generator")
 
  args = parser.parse_args()

  rFile = open("/dev/urandom", "r")
  _s = rFile.read(4)
  seed = str( (ord(_s[0])) | (ord(_s[1]) << 8) | (ord(_s[2]) << 16) | (ord(_s[3]) << 24) )
  rFile.close()
 
  if args.seed :
    seed = args.seed

  print "SEED = %s" % seed
  random.seed(seed) 
 
  if not args.outdir :
    args.outdir = args.template + ".OUT"

  if not os.path.exists(args.template) :
    error("[%s] is not a valid path\n" % args.template)
  
  config, _obfs_config = configParser.parseConfig(args.config)
  configParser.randomizeConfig(config)
 
  obfs_config = ObfsConfig(_obfs_config)

  if args.noobfs :
    obfs_config = None

  #print config

  mkdir(args.outdir)
  
  processDir(args.template, args.outdir, config, obfs_config, args.nogen)

if __name__ == "__main__" :
  main()
