# bin2hex

@Author: Lok Yan <Lok.Yan@us.af.mil>
@Group: AFRL

## Description:

This is a simple utility that transforms a binary input stream into hexademical outputs. This is designed to be extremely simple and to highlight a common problem in protocols with variable length fields. In this protocol, the first 4 bytes specify the number of bytes that are in the stream and then the rest of the bytes are treated as binary and convered into hex.

 
## Vulnerability Class: 

The vulnerability is a classic buffer overflow [CWE-121: Stack-based Buffer Overflow](http://cwe.mitre.org/data/definitions/121.html)

## Additional Notes:

In this CB, we have decided to add in an extra padding buffer into the main function so that an actual buffer overflow is easier to achieve using the *receive* system call. Essentially, since the main function's frame resides at the top of the memory address space, a call to *receive* with too large of an amount will result in *receive* failing due to an invalid address. This, in turn, leads to the CB terminating. So a successful POV would have needed to have a buffer that is long enough to overwrite sensitive information (e.g. return address) but not too long as to make *receive* fail. To keep things simple we added the padding so that there is less of a chance of hitting this problem.

## Changes from Original YAN01_00013

1. I removed the padding in this version to make overflowing more sensitive
2. I also changed the polls so that they only use 1/2 of the buffer length for the strings
