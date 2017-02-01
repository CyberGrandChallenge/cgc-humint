#CBGenerator

The CB Generator is used to randomly generate a new CB given a specific template. The basic idea is to take a CB's source, change important design variables (e.g. buffer sizes, message tokens) into statements that use #define macros, and then have the CBGenerator replace the macros with new values as defined in a configuration file.

##Usage

	usage: cbgen [-h] -t TEMPLATE [-s SEED] [-o OUTDIR] -c CONFIG [-n]
	
	Generates a new CB Source Tree given a template Soruce Tree
	
	optional arguments:
	  -h, --help            show this help message and exit
	  -t TEMPLATE, --template TEMPLATE
	                        The CB template directory
	  -s SEED, --seed SEED  seed to use for random
	  -o OUTDIR, --outdir OUTDIR
	                        Name of directory to output the files. Otherwise
	                        defaults to [template].out
	  -c CONFIG, --config CONFIG
	                        Config file to use
	  -n, --noobfs          Disable Obfuscation
	  -x, --nogen           Disable Generator
	
	
##Creating Templates

Templates contain three major components: the source, the poll generator and the pov (or pre-generated polls). 

### Source

We must go into the source and make sure that the source references a macro for anything that we wish to generate. For example, TESTS_00001 (CADET_00001) has a stack buffer that uses a constant size of 256. We change this to use a macro called BUF_SIZE. In addition to the size of the buffer, we can also change the protocol by changing the messages that are printed out.

### Poll Generator

We must make sure that the poll generator still follows the protocol as set forth in the source. For example, TESTS_00006 (KPRCA_00001) uses the AUTH, SET and CALL tokens (these are already defined in the source as TOKEN_AUTH, TOKEN_SET and TOKEN_CALL respectively). Thus we must go into the machine.py and add in the corresponding definitions and also change any constant references to the original "AUTH" keyword to use the new temporary variable. 

### POV 

Since the POVs are normally not generated, as are some of the POLLs, we must also make sure that we have a way to replace the constant tokens with the generated versions. For example, TESTS_00005 (EAGLE_00004) uses *push* as a token representing the push instruction. We first change the source to use a macro (PUSH_MNEMONIC) in place of the original constant string. Then we must go into every single POLL and POV and create a new .xml.template file that uses <REPLACEME>PUSH_MNEMONIC</REPLACEME> as a place holder for any macros that are to be defined. 

#### POV Template Notes

Not all POVs require a template. This can be seen in TESTS_00007 (YAN01_00001)  where the two POVs contain strings of ~530 bytes, which is long enough to crash the original CB as well as any randomly generated ones. 

The reason is that the configuration file TESTS_00007.cfg has a line

	:BUF_SIZE : M 64 512 16

meaning the maximum size is 512 bytes. Since the input is sufficiently greater than 512 bytes, the buffer overflow works as expected.

On the other hand, we can make a mistake as the one that is demonstrated in TESTS_00008 (YAN01_00005). The configuration file for TESTS_00008.cfg contains:

	:BUF_SIZE : M 64 256 32

However, POV_00000.xml contains an input string of length 168, meaning it is possible for the generator to create a version of the program with a buffer >168 bytes and this POV will no longer POV. 

Not only this, but if obfuscation is turned on, it is certainly possible that we are adding enough local variables that further increases the distance between the buffer and the return address. Thus POV_00000.xml will not always work as expected. 

Fixing this error is left as an exercise. For example one can decrease the generated buffer size as well as remove obfuscations. Another is to control the number of obfuscation variables and then create a template that respects these lower and upper bounds. Perhaps the simplest is to just increase the input length in POV_00000.xml.

## Configuration Files (configParser.py)

The generator must also be supplied with a configuration file that specifies what needs to be generated and how. Right now, all generator configuration options must start with the ':' (colon) character and all obfuscation options start with the '-' (minus) character. Also, all configuration options must be separated by a newline, otherwise it won't get parsed properly (a newline is used in case constant strings are used -- see below).

The generator configuration format is *: MACRO_NAME : TYPE [TYPE_OPTIONS]* where MACRO_NAME is the name of the MACRO (e.g., PUSH_MNEMONIC), TYPE is the generator type and TYPE_OPTIONS are options for the type.

So far we support the following types:

- S #		: Random string of up to # characters
- S #x #y	: Random string between #x and #y characters long (inclusive)
- S # [charset]	: Random string up to # characters long generated based on the *charset* (see below)
- S #x #y [charset]	: Random string between #x and #y characters long based on the *charset*. This option is used to specific a constant size with #x == #y.

Charset is used as a way to specifcy how the string is supposed to look like. We currently support escape based character classes, square brackets defined character classes as well as greedy repetition specifiers such as * and +. For example, *wwww* will always return the string "wwww" since that is what we defined it as. Whereas *w+* will return a string of all "w" characters. *[abc]\w+\n* of length 5 could return "aab1\n", "bab1\n", "aabx\n" ...

- C [charset]	: Random character based on the *charset*
- I #		: An unsigned integral value of size # where # is 8, 16 or 32 bits long
- M #x #y #z	: An unsigned integral value between #x and #y (inclusive) but at intervals of #z. For example M 1 5 2 could result in 1, 3 or 5.
- O [operation] [ref1] [ref2] :
		: The "operation" type allows one MACRO to be created based on others. All operations are assumed to be binary. Furthermore, we use prefix notation. A good example of how this option can be used is found in TESTS_00015.cfg. 
		: [operation] can be '*', '/', '+', '-', '%' which are mathematical operators. e.g. **TOKEN_BUF_SIZE : O + #TOKEN_START_PAD_LEN# + #TOKEN_SIZE# #TOKEN_END_PAD_LEN#** sets TOKEN_BUF_SIZE = TOKEN_START_PAD_LEN + (TOKEN_SIZE + TOKEN_END_PAD_LEN)
		: [operation] can also be 'len' which will store the "length" of another MACRO. e.g. **TOKEN_END_PAD_LEN : O len #TOKEN_END_PAD# 1** which sets TOKEN_END_PAD_LEN = len(TOKEN_END_PAD)
		: [operation] can also be 'int' which will convert the MACRO into an int.
                : [operation] can also be 'fmt' which will apply a format string to the MACRO. The first operand is the format string and the second operand is the reference. e.g. **TOKEN_SIZE_DEC : O fmt %u int #TOKEN_SIZE# 1** will set TOKEN_SIZE_DEC = "%u" % (int(TOKEN_SIZE)). 
- R ...		: Reference type which can also be used as a constant (this can be a multiline constant too. For the reference type anything within #..# will be replaced with another defined configuration option.

##Obfuscations (obfuscator.py)

Currently all obfuscations are made at the source level. We do this so that we can keep a copy of the source code for further tests and debugging if necessary. Currently there are basically three major classes of obfuscation. 1. Simple deadcode insertion that creates new temporary variables for each function or if/else/loop statement that is scoped with braces (i.e., we must find the brace before we insert the new variable definitions). 2. Medium deadcode insertion that inserts deadcode as well as nested conditional statements if/else. 3. Inline deadcode insertion that inserts deadcode into the middle of a function by looking for assignment statements and then inserting deadcode after it. We do this to be safe since assignment statements are self sufficient and a clear indication that it is safe to insert additional statements. 

In addition to where we can insert the deadcode, the obfuscator can also be configured to use inttypes and/or floattypes. automatically generated static functions, as well as trying to automatically identify locally defined variables and use those as part of the deadcode as well. We can use local variables as RVals (which do not change the value) as well as using them as LVals where we create a new temporary variable with the same type as the local variable to store and restore the original value.

**NOTE** While the obfuscator will try to do type coersion, there has been problems where the generated code compiles fine, but the program will crash (see TESTS_00003.cfg). To handle these cases, the obfuscator can also be configured to exclude functions so that these specific functions will never have deadcode inserted as well as exclude variables where certain variables will never be used as either LVals or RVals.

The options for obfuscation are placed into the configuration file, one on each line starting with '-' and in key=value pairs.

-obfs_useInt=True/False		: Generate Int Types
-obfs_useFloat=True/False	: Generate float types
-obfs_useInline=True/False	: Add deadcode to the middle of functions
-obfs_useRVals=True/False	: Use original local variables as RVals
-obfs_useLVals=True/False	: Use original local variables as LVals
-obfs_useFunctions=True/False	: Auto generate functions
-obfs_inlineChance=1..100	: Probability of inserting deadcode at each assignment statement found (should be low)
-obfs_numFunctions=#		: Number of functions to auto-generate
-obfs_minFuncParams=#		: Minimum number of params for each function
-obfs_maxFuncParams=#		: Maximum number of params for each function
-obfs_ifelseLevel=#		: Nesting level for if/else statements. There is a 50% chance of nesting.
-obfs_varTypes=T1,T2,T3,...	: Use the comma separate list of types in generation
-obfs_excludeFuncs=F1,F2,F3,...	: Do not add deadcode to the comma separate list of functions
-obfs_excludeVars=V1,V2,V3,...	: Do not use the comma separate list of variables as LVals or RVals
