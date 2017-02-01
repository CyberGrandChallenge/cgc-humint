#!/usr/bin/python

import sys
import random
import string
import re

_PREFIX_ = "_GEN_"
UINT32_MAX = 0xFFFFFFFF
ALPHA = string.letters + string.digits
WORD = string.letters + string. digits + "_"
DIGITS = string.digits
UPPER = string.uppercase
LOWER = string.lowercase
PRINTABLE = string.printable
WHITESPACE = string.whitespace
PUNC = string.punctuation
HEX = string.hexdigits

validEscapeChars = "ntwdulasph*+\\[]"
escapeCharToCharClass = { 'n' : "\n", 't' : "\t", '\\' : "\\", ']' : ']', '[' : '[', '*' : "*", '+' : "+", 'w' : WORD, 'd' : DIGITS, 'u' : UPPER, 'l' : LOWER, 'a' : PRINTABLE, 's' : WHITESPACE, 'p' : PUNC, 'h' : HEX }

def warn(msg, l) :
  if l == -1 :
    sys.stderr.write("WARNING: " + msg)
  else :
    sys.stderr.write("WARNING: At line #%u:" % l + msg)

def error(msg, l) :
  if l == -1 :
    sys.stderr.write("ERROR: " + msg)
  else :
    sys.stderr.write("ERROR: At line #%u:" % l + msg)
  exit(-1)

def isValidKeyType(keyType) :
  args = keyType.split()
  return ( args[0] == 'S' #str
           or args[0] == 'I' #int
           or args[0] == 'F' #float
           or args[0] == 'C' #character 
           or args[0] == 'M' #multiples in strides
           or args[0] == 'R' #reference
           or args[0] == 'X' #Exclusive use from set
           or args[0] == 'O' #operations
         )

def isStringKeyType(keyType) :
  args = keyType.split()
  return (args[0] == 'S')

def getRandomChar(subKeyType) :
  tempCharClass = ""
  i = 0
  strLen = len(subKeyType)
  while i < strLen :
    if subKeyType[i] == '\\' :
      i += 1
      if i >= strLen :
        error("Parse error in format string - escape char \\ at the end of the string\n", -1)
      if not subKeyType[i] in validEscapeChars :
        error("Parse error in format string - invalid escape sequence \\%c in %s\n" % (subKeyType[i], subKeyType), -1) 
     
      tempCharClass += escapeCharToCharClass[subKeyType[i]]
    else :
      tempCharClass += subKeyType[i]

    i+= 1

  if not tempCharClass :
    tempCharClass = WORD
 
  return (random.choice(tempCharClass))

def getRandomString(stringDef, minLen, maxLen) :
  #first we go through the format stirng to see how many chars 
  # and how many floats - i.e., any char with * is a float
  i = 0
  strLen = len(stringDef)
  temp = [] #use an array of strings to hold the temporary generated string
  optionChars = [] #an array of pairs - to hold the offset into temp and the string to choose from
                     # so we can fill them in later - e.g. optionChar[0] = [1, DIGITS] means that
                     # digits should be inserted into temp[1]
  absoluteChars = [] #another array of pairs for absolute chars
  totalChars = 0

  while i < strLen :

    if stringDef[i] == ']' :
      warn("Mismatched ] in format string %s\n" % stringDef, -1)

    if stringDef[i] == '[' :
      tempCharClass = ""
      bFoundMatch = False
      i += 1
      while not bFoundMatch and i < strLen :
        if stringDef[i] == '\\' :
          i += 1
          if i >= strLen :
            error("Parse error in format string - escape char \\ at the end of the string\n", -1)
          if not stringDef[i] in validEscapeChars :
            error("Parse error in format string - invalid escape sequence \\%c in %s\n" % (stringDef[i], stringDef), -1) 
         
          tempCharClass += escapeCharToCharClass[stringDef[i]]
          
        elif stringDef[i] == ']' :
          bFoundMatch = True
 
        else :
          tempCharClass += stringDef[i]

        i += 1
       
      if not tempCharClass :
        warn("Empty Set specification in %s. Using \\w \n" % stringDef, -1)
        tempCharClass = WORD

      if i < strLen :
        if stringDef[i] == '*' :
          temp.append("")
          optionChars.append([len(temp) - 1, tempCharClass])
          i += 1
          continue
        elif stringDef[i] == '+' :
          temp.append(random.choice(tempCharClass))
          totalChars += 1
          absoluteChars.append([len(temp) - 1, tempCharClass])
          i += 1
          continue
       
      #we just add in the single character
      temp.append(random.choice(tempCharClass))
      totalChars += 1
       

    elif stringDef[i] == '\\' :
      i += 1
      if i >= strLen :
        error("Parse error in format string - escape char \\ at the end of the string\n", -1)
      if not stringDef[i] in validEscapeChars :
        error("Parse error in format string - invalid escape sequence \\%c in %s\n" % (stringDef[i], stringDef), -1) 

      #lets see if we have the * or + specifiers
      if (i + 1) < strLen : #if we are not at the end, - then see if we have a * or +
        if stringDef[i+1] == '*' :
          temp.append("") #append the empty string
          optionChars.append([len(temp) - 1, escapeCharToCharClass[stringDef[i]]])
          i += 2 #move things ahead
          continue 
        elif stringDef[i+1] == '+' :
          temp.append(random.choice(escapeCharToCharClass[stringDef[i]]))
          totalChars += 1
          absoluteChars.append([len(temp) - 1, escapeCharToCharClass[stringDef[i]]])
          i += 2
          continue
      
      #either we are at the end of the string or the escape is not modified
      temp.append(random.choice(escapeCharToCharClass[stringDef[i]]))
      totalChars += 1
      i += 1

    else : #not an escape character so just push it in
      tempCharClass = stringDef[i]
      if (i + 1) < strLen :
        if stringDef[i + 1] == '*' :
          temp.append("")
          optionChars.append([len(temp) - 1, tempCharClass])
          i += 2
          continue
        elif stringDef[i + 1] == '+' :
          temp.append(random.choice(tempCharClass))
          totalChars += 1
          absoluteChars.append([len(temp) - 1, tempCharClass])
          i += 2
          continue

      temp.append(stringDef[i])
      totalChars += 1
      i += 1
 
  #now that we are doing - lets go through the absoluteChars pairs first
  while absoluteChars and totalChars < maxLen :
    for p in absoluteChars :
      if totalChars >= maxLen :
        break

      temp[p[0]] += random.choice(p[1])
      totalChars += 1
     
  while optionChars and totalChars < maxLen :
    for p in optionChars :
      if totalChars >= maxLen :
        break

      temp[p[0]] += random.choice(p[1])
      totalChars += 1

  ret = "".join(temp)

  if totalChars < minLen :
    warn("Format string [%s] does not satisfy minLen [%u] requirement - filling with default\n" % (stringDef, minLen), -1)
    while totalChars < minLen :
      ret += random.choice(WORD)
      totalChars += 1
 
  if totalChars > maxLen :
    warn("Format string [%s] results in more than maxLen characters [%s] - consider adding a minLen\n" % (stringDef, ret), -1)
 
  return (ret) 
     

def parseConfig(filename) :
  conf = {}
  obfs_conf = {}
  key = ""
  keyType = ""
  value = ""
  prevLine = ""
  lineNum = 1
  bStarted = False
  for f in open(filename) :
    g = f.lstrip()
    if g and g[0] == '#' :
      lineNum += 1
      continue

    if f[0] == ':' :
      if prevLine == '\n' :
        if key and value :
          conf[key] = [keyType,value.strip(),None] #save the current key and value pair

        elif key and (not value or value == '\n') :
          warn("Value is empty\n", lineNum)
          #conf[key] = value #save the current key and value pair

        tokens = f[1:].split(':')
        key = tokens[0].strip()
        if len(tokens) < 2 :
          keyType = 'C'
        else :
          keyType = tokens[1].strip()
          if not isValidKeyType(keyType) :
            warn("Keytype [%s] is invalid\n" % keyType, lineNum)
            keyType = 'S'

        value = ""
        if key in conf :
          warn("Key [%s] already exists\n" % key, lineNum)
        if not key :
          error("Key is not defined\n", lineNum)

      else :
        warn("Errant key definition?\n", lineNum)
        value += f
 
    elif f[0] == '-':
      args = f[1:].split("=")
      if len(args) != 2 :
        error("Errant configuration option. Need '- key = value'", lineNum)
      else :
        obfs_conf[args[0].strip()] = args[1].strip()
    else :
      if not key and f.strip() :
        error("Value definition without a key\n", lineNum)

      value += f

    prevLine = f
    lineNum += 1

  if key :
    if not value or value == '\n' :
      warn("Value is empty. Try inserting a newline at the end\n", lineNum - 1)

    conf[key] = [keyType,value.strip(),None] #save the last key value pair if it exists

  return conf,obfs_conf

def getRawData(m, config) :
  #I should really make this a class so I don't have to use these hacks
  if config[m][0].startswith('C') :
    return(config[m][1].strip("'"))
  elif config[m][0].startswith('S') :
    return(config[m][1].strip('"'))
  else :
    return config[m][1]

_VALID_OPS_ = [ "*", "/", "+", "-", "%", "len", "int", "fmt" ]

def calculateOps(args, conf) :


  if len(args) < 3 :
    return None, None #this should be an error

  a0 = args[0]
  a1 = args[1]
  a2 = args[2]
  
  r1 = None
  r2 = None
  leftover = None
  
  ret = None

  if a0 in _VALID_OPS_ :
    if a1 in _VALID_OPS_ :
      r1,r2 = calculateOps(args[1:], conf)
    else :
      r1 = a1
      r2 = args[2:]
    
    if r2[0] in _VALID_OPS_ :
      r2, leftover = calculateOps(r2, conf)
    else :
      leftover = r2[1:]
      r2 = r2[0]
   
    if r1 is None or r2 is None:
      return None,None

    try :
      r1 = int(r1)
    except ValueError :
      try : #not an int so try a float
        r1 = float(r1)
      except ValueError :
        #not a float either so leave it as a string
        mat = re.match("#(.+)#", r1)
        if mat :
          if mat.group(1) not in conf :
            warn("calculateOps: %s does not exist\n" % mat.group(1), -1)
            return None, None
    
          r1 = conf[mat.group(1)][2]
          if r1 is None: #if r1 doesn't exist yet ...
            return None, None

        #if nothing matches then r1 should stay a string
    try :
      r2 = int(r2)
    except ValueError :
      try : #not an int so try a float
        r2 = float(r2)
      except ValueError :
        #not a float either so leave it as a string
        mat = re.match("#(.+)#", r2)
        if mat :
          if mat.group(1) not in conf :
            warn("calculateOps: %s does not exist\n" % mat.group(1), -1)
            return None, None
    
          r2 = conf[mat.group(1)][2]
          if r2 is None: #if r1 doesn't exist yet ...
            return None, None

    #print "%s -- %s, %s" % (" ".join(args), type(r1), type(r2))

    if a0 == "*" :
      ret = r1 * r2
  
    elif a0 == "/" :
      ret = r1 / r2

    elif a0 == "+" :
      ret = r1 + r2

    elif a0 == "-" :
      ret = r1 - r2

    elif a0 == "%" :
      ret = r1 % r2

    elif a0 == "len" :
      ret = len(r1)

    elif a0 == "int" :
      try :
        ret = int(r1)
      except ValueError :
        #do nothing... 
        warn("r1 is NOT an int? [%s]\n" % (" ".join(args), -1))
    elif a0 == "fmt" :
      try :
        ret = r1 % r2
      except Exception as e:
        error("Format specifier [%s] does not work with [%s] .. " % (r1, r2) + str(e), -1)
  else :
    error("Invalid operation [%s]" % " ".join(args), -1)

  return ret,leftover

def randomizeConfig(conf) :
  randomSets = {}
  for d in conf :
    kt = conf[d][0]
    if kt.startswith('R') :# Reference type - so don't do anything yet
      pass
    if kt.startswith('O') : #Operator type - don't do anything yet either
      pass

    elif kt.startswith('I') : #regular int - right now its all uint
      temp = random.randint(0,UINT32_MAX)
      args = kt.split()
      if len(args) > 1 :
        if args[1] == '8' :
          temp = temp & 0xFF
        elif args[1] == '16' :
          temp = temp & 0xFFFF
        elif args[1] == '32' :
          pass
        else : #this is not supposed to happen
          warn("Invalid Key Type [%s]\n" % kt, -1)
      conf[d][1] = "0x%x" % temp
      conf[d][2] = temp

    elif kt.startswith('C') : #A char - the user can present a charset to use
      kt = kt.strip()
      temp = ''
      if len(kt) < 2 :
        temp = getRandomChar('')
      elif kt[1] == ' ':
        if len(kt) > 2 :
          temp = getRandomChar(kt[2:])
        else :
          temp = getRandomChar('')

      conf[d][1] = "'\\x%02x'" % ord(temp) #e.g., '\x41'
      conf[d][2] = temp

    elif kt.startswith('S') : #A random string
      args = kt.strip()
      args = args.split()
      minLen = 1
      maxLen = 10
      stringDef = ""
      if len(args) == 2 :
        maxLen = int(args[1])
      elif len(args) == 3 :
        try :
          maxLen = int(args[2])
          minLen = int(args[1])
        except ValueError as exception :
          maxLen = int(args[1])
          startOfArgs1 = kt.find(args[1])
          startOfArgs2 = kt.find(args[2], startOfArgs1 + len(args[1]))
          stringDef = kt[startOfArgs2 :]

      elif len(args) >= 4 :
        minLen = int(args[1])
        maxLen = int(args[2])
        startOfArgs1 = kt.find(args[1])
        startOfArgs2 = kt.find(args[2], startOfArgs1 + len(args[1]))
        startOfArgs3 = kt.find(args[3], startOfArgs2 + len(args[2]))
        stringDef = kt[startOfArgs3 :]
        
    
      if minLen > maxLen :
        warn("Minimum str len can't be > maxLen. Setting maxLen = minLen\n", -1)
        maxLen = minLen 

      conf[d][2] = getRandomString(stringDef, minLen, random.randint(minLen, maxLen))
      conf[d][1] = '"' + conf[d][2] + '"'


    elif kt.startswith('M') : #A multiple - this is like I, but you specify the min, max and strides
      args = kt.split()
      minVal = 0
      maxVal = 10
      stride = 1

      if len(args) == 4 :
        minVal = int(args[1])
        maxVal = int(args[2])
        stride = int(args[3])
      else :
        warn("Incorrect usage of M minVal maxVal stride in [%s]. Using defaults %u %u %u\n" % (kt, minVal, maxVal, stride), -1)        
   
      if minVal >= maxVal :
        warn("minVal of [%u] is >= maxVal of [%u]. Adjusting maxVal = minVal + 1\n" % (minVal, maxVal), -1)
        maxVal = minVal + 1

      temp = random.randrange(minVal, maxVal, stride) 
      conf[d][2] = temp
      conf[d][1] = "0x%x" % temp

    elif kt.startswith('X') : #exclusive use set -- here we will just get the sets
      args = kt.split()
      setName = ""
      setVals = []
      if len(args) == 2 :
        setName = args[1].strip()
        if setName not in randomSets :
          warn("Referencing an undefined set in [%s].\n" % kt, -1)
      else :
        setName = args[1].strip()
        setVals = [_.strip() for _ in "".join(args[2:]).split(',')]
        if setName in randomSets and set(setVals) != set(randomSets[setName]) :
          warn("Previously defined set and current set don't match\n" % (randomSets[setName], set(setVals)), -1)
        randomSets[setName] = setVals

    else :
      pass #do nothing

  rSetCounts = {}
  for _ in randomSets :
    rSetCounts[_] = len(randomSets[_]) 
    random.shuffle(randomSets[_])
    print "-- %s, %u" % (",".join(randomSets[_]), rSetCounts[_])

  for d in conf : #now process the sets
    kt = conf[d][0]

    if kt.startswith('X') :
      args = kt.split()
      setName = args[1]
      if setName not in rSetCounts :
        error("Are you sure you defined a set for [%s]?\n" % setName, 1)
      if rSetCounts[setName] == 0 :
        error("Not enough values in the exclusive use set... [%s]\n" % setName, -1)
     
      conf[d][1] = randomSets[setName][rSetCounts[setName] - 1] 
      rSetCounts[setName] = rSetCounts[setName] - 1
      conf[d][2] = conf[d][1]
       
      print "-X- %s is now %s" % (d, conf[d][1])
 

  opsLeft = {}
  for d in conf :
    kt = conf[d][0]
    if kt.startswith('O') :
      opsLeft[d] = kt

  beforeLen = len(opsLeft)
  while beforeLen > 0 :
    afterLen = beforeLen
    afterOpsLeft = {}
    for d in opsLeft :
      args = opsLeft[d].split()
      ret,leftover = calculateOps(args[1:], conf)
      if ret != None :
        afterLen -= 1  
        conf[d][2] = ret
        if isinstance(conf[d][2], int) :
          conf[d][1] = "0x%x" % conf[d][2]
        elif isinstance(conf[d][2], float) :
          error("Shouldn't have a float as type\n", 1)
        else :
          conf[d][1] = conf[d][2]

        print "-O- %s is now %s" % (d, conf[d][1])
      else :
        afterOpsLeft[d] = opsLeft[d]
    if afterLen == beforeLen :
      error("Strange.. The operator configurations don't seem to be all right.. Missing reference perhaps?\n", -1)
      break
    beforeLen = afterLen  
    opsLeft = afterOpsLeft
   
  for d in conf : #now that we have figured out everything else process the references
    kt = conf[d][0]
    if kt.startswith('R') : #Reference type that references something else
      #Here we will do replace anything in between # as long as there is
      # a reference to something else in the config
      kt = kt.strip()
      args = ""
      if len(kt) > 1 and kt[1] == ' ' :
        args = kt[2:]

      i = 0
      strLen = len(args)
      temp = ""
      while i < strLen :
        if args[i] == '#' :
          tempRef = ""
          i += 1 
          j = i
          while j < strLen and args[j] != '#' :
            tempRef += args[j]
            j += 1
   
          if args[j] != '#' :
            error("Unmatched replacement char # in %s\n" % args, -1)
 
          if not tempRef :
            error("A config name to reference is needed in between # and #\n", -1)

          if not tempRef in conf :
            error("Invalid reference to %s in this config\n" % tempRef, -1)

          temp += getRawData(tempRef, conf)
          i = j
        else :
          temp += args[i]   
     
        i += 1 
    
      conf[d][1] = temp
      conf[d][2] = conf[d][1]
   
      print "-R- %s is now %s" % (d, conf[d][1])
    else :
      pass #do nothing
