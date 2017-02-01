import random

_PREFIX_ = "_GEN_"
_RVAL_CHANCE_ = 50
_LVAL_CHANCE_ = 50
_IF_ELSE_CHANCE_ = 10
_ELSE_CHANCE_ = 50

_DEFAULT_OPS_ = ["+", "-", "*", "/"] 
_INT_OPS_ = ["+", "-", "*", "/", "|", "&", "&&", "||"] 
_DOUBLE_OPS_ = ["+", "-", "*", "/", "&&", "||"] 

#_INT_TYPES_ = ["char", "unsigned char", "short", "unsigned short", "int", "unsigned int", "long", "unsigned long", "long int", "unsigned long int", "long long", "unsigned long long", "int8_t", "uint8_t", "int16_t", "uint16_t", "int32_t", "uint32_t", "int64_t", "uint64_t"]
_INT_TYPES_ = ["char", "unsigned char", "short", "unsigned short", "int", "unsigned int", "long", "unsigned long", "long int", "unsigned long int", "int8_t", "uint8_t", "int16_t", "uint16_t", "int32_t", "uint32_t"]
_INT64_TYPES_ = ["long long", "unsigned long long", "uint64_t", "int64_t"]

_FLOAT_TYPES_ = ["float", "double", "long double"]
_ALL_TYPES_ = _INT_TYPES_ + _FLOAT_TYPES_

class CVariable() :
  def __init__(self, _name, _type, _val) :
    self.varName = _name
    self.varType = _type
    self.varVal = _val

  def __str__(self) :
    ret = "%s %s" % (self.varType, self.varName)
    if self.varVal :
      ret += " = %s" % self.varVal
  
    return ret
    

class CFunction() :
  def __init__(self, _name, _returnType, _params) :
    self.funcName = _name
    self.returnType = _returnType
    self.params = _params

  def __str__(self) :
    ret = "%s %s(" % (self.returnType, self.funcName)
    bFirst = True
    for p in self.params:
      if not bFirst :
        ret += ", "
 
      ret += "%s %s" % (p.varType, p.varName)
      bFirst = False

    ret += ")"
    return ret

def typeToZeroVal(typeName) :
  if typeName is None :
    return "0"

  if typeName in _INT_TYPES_ :
    return "0"
  
  if typeName in _FLOAT_TYPES_ : 
    return "0.0"

  return None

def typeToOps(types) :
  opsDict = { 0 : _INT_OPS_, 1 : _DOUBLE_OPS_, 2 : _DEFAULT_OPS_ }

  curLevel = 0

  if not isinstance(types, list) :
    types = [types]

  for i in types :
    if i in _FLOAT_TYPES_ :
      curLevel = 1
      
  return opsDict[curLevel]

 
def genDeadCode(localVars, lVals, rVals,
                ops = None,
                bDeclaration = True,
                bScope = False, 
                bPrefix = True,
                ifelseLevel = 0,
                minTerms = 1,
                maxTerms = 15,
                indentationAmt = 0) :

  if ifelseLevel < 0 :
    ifelseLevel = 0

  v_prefix = _PREFIX_
  if not bPrefix :
    v_prefix = ""

  if not localVars and not (lVals and rVals) :
    return "//FIXME: Error not enough variables to work with\n"
  
  ret = ""
  indentation = "".join([ ' ' for i in xrange(indentationAmt)])

  if bScope :
    ret += indentation + "{\n"
  
  if bDeclaration :
    for lv in localVars:
      if lv.varVal == None :
        ret += indentation + lv.varType + " " + v_prefix + lv.varName + ";\n"
      else :
        ret += indentation + lv.varType + " " + v_prefix + lv.varName + " = " + lv.varVal + ";\n"

  numTerms = random.randint(minTerms, maxTerms)
  for i in xrange(numTerms) :
    if ifelseLevel > 0 and random.randint(0,100) < _IF_ELSE_CHANCE_ :
      condVar = None
      condPrefix = v_prefix
      if rVals and (not localVars or random.randint(0,100) < _RVAL_CHANCE_) :
        condVar = random.choice(rVals) 
        condPrefix = ""
      else :
        condVar = random.choice(localVars)
 
      ret += indentation + "if (" + condPrefix + condVar.varName + ")\n"
      ret += indentation + "{\n"
      ret += genDeadCode(localVars, lVals, rVals, ops, False, False, bPrefix, ifelseLevel - 1, minTerms, maxTerms, indentationAmt + 2)
      ret += indentation + "}\n"
      if random.randint(0,100) < _ELSE_CHANCE_ :
        ret += indentation + "else\n"
        ret += indentation + "{\n"
        ret += genDeadCode(localVars, lVals, rVals, ops, False, False, bPrefix, ifelseLevel - 1, minTerms, maxTerms, indentationAmt + 2)
        ret += indentation + "}\n" 
      continue
 
    l = ""
    l_prefix = v_prefix
    if lVals and (not localVars or random.randint(0,100) < _LVAL_CHANCE_) :
      l = random.choice(lVals)
      l_prefix = "" 
    else :
      l = random.choice(localVars)

    r1 = ""
    r1_prefix = v_prefix
    r2 = ""
    r2_prefix = v_prefix
    if rVals and (not localVars or random.randint(0,100) < _RVAL_CHANCE_) :
      r1 = random.choice(rVals)
      r1_prefix = ""
    else :
      r1 = random.choice(localVars)

    if rVals and (not localVars or random.randint(0,100) < _RVAL_CHANCE_) :
      r2 = random.choice(rVals)
      r2_prefix = ""
    else :
      r2 = random.choice(localVars)

    if ops :
      op = random.choice(ops)
    else :
      op = random.choice(typeToOps([r1.varType, r2.varType]))

    if op == '/' :
      if r2.varType in _INT64_TYPES_ :
        pass 
      else :
        # != will generate an error if variable happens to be constant -1 with -werror
        #ret += indentation + "if ( (" + r2_prefix + r2.varName + " != %s ) && (" % typeToZeroVal(r2.varType) + r1_prefix + r1.varName + " != 0x80000000) )"
        ret += indentation + "if ( (" + r2_prefix + r2.varName + " != %s ) && !(" % typeToZeroVal(r2.varType) + r1_prefix + r1.varName + " != -1) )"
    
    if l.varType != r1.varType or l.varType != r2.varType :
      #this makes sure that we cast the rval prior to assignment to suppress any problems
      ret += indentation + l_prefix + l.varName + " = (%s)(" % l.varType + r1_prefix + r1.varName + " " + op + " " + r2_prefix + r2.varName + ");\n"
    else :
      ret += indentation + l_prefix + l.varName + " = " + r1_prefix + r1.varName + " " + op + " " + r2_prefix + r2.varName + ";\n"
 
  if bScope :
    ret += indentation + "}\n"

  return (ret)

def namesToCVarArray(varNames, varType, initialValues) :
  ret = []

  if not varNames :
    return ret

  if not isinstance(varNames, list) :
    varNames = [varNames]

  initVals = initialValues
  if not isinstance(initialValues, list) :
    initVals = [ initialValues for i in xrange(len(varNames)) ] 
 
  
  if len(varNames) != len(initVals) :
    return None
 
  for i in xrange(len(varNames)) :
    ret.append( CVariable(varNames[i], varType, initVals[i]) )

  return ret

def genDeadCode_simple(varNames, varType = "int", 
                ops = ["+", "-", "*", "/", "|", "&", "&&", "||"],
                lVals = [],
                rVals = [],
                initialValues = "0",
                bDeclaration = True,
                bScope = False, 
                bPrefix = True,
                ifelseLevel = 0,
                minTerms = 1,
                maxTerms = 15,
                indentationAmt = 0) :

  _localVars = namesToCVarArray(varNames, varType, initialValues)
  _lVals = namesToCVarArray(lVals, varType, None)
  _rVals = namesToCVarArray(rVals, varType, None)

  if _localVars is None or _lVals is None or _rVals is None :
    return "//FIXME: Error in initialization values"

  return genDeadCode(_localVars, _lVals, _rVals, ops, bDeclaration, bScope, bPrefix, ifelseLevel, minTerms, maxTerms, indentationAmt)

def genDeadFunction(funcName, returnType, params, minTerms = 5, maxTerms=15, bPrefix=True) :
  #all of these functions are static - to maintain local scope
  f_prefix = _PREFIX_
  if not bPrefix :
    f_prefix = ""

  ret = "static %s %s(" % (returnType, f_prefix + funcName)
  for i in xrange(len(params)) :
    if i > 0 :
      ret += ", "
    p = params[i]
    ret += p.varType + " " + p.varName
  ret += ")\n"
  ret += "{\n"

  varNames = []
  for i in xrange(random.randint(3, 10)) :
    varNames.append(_PREFIX_ + "v%u" % i)

  _localVars = namesToCVarArray(varNames, "int", None)
    
  ret += genDeadCode(_localVars, lVals = params, rVals = params, bDeclaration=True, bScope = False, bPrefix = False, ifelseLevel = 5, minTerms = minTerms, maxTerms = maxTerms, indentationAmt = 2)

  retVar = random.choice(_localVars)

  if returnType != "void" :
    if returnType != retVar.varType :
      ret += "  return ((%s)%s);\n" % (returnType, retVar.varName)
    else :
      ret += "  return (%s);\n" % (retVar.varName)
  
  ret += "}\n"
  ret += "\n"

  return (ret)
  

def genDeadFunction_simple(funcName, returnType = "void",  paramType = "int", numParams = 0, minTerms = 5, maxTerms = 15, bPrefix = True) :

  params = []
  for i in xrange(numParams) :
    p = _PREFIX_ + "param_%u" % i
    params.append(CVariable(p, paramType, None))
  
  return genDeadFunction(funcName, returnType, params, minTerms, maxTerms, bPrefix)



