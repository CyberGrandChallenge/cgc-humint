# hex2bin

@Author: Lok Yan <Lok.Yan@us.af.mil>
@Group: AFRL

## Description:

This CB is the dual of the bin2hex CB. It also takes as input 4 bytes that corresponds to the length of data that is expected to be read in followed by the number of bytes that should have been read in. Every two bytes are treated as hex and converted into binary which is written back out to the client.
 
## Vulnerability Class: 

This CB has two vulnerabilities. The main vulnerability is a signed/unsigned type mismatch [CWE-195: Signed to Unsigned Conversion](http://cwe.mitre.org/data/definitions/195.html). By inserting a negative number, the comparison test that ensures the inputted length is within a certain limit will pass. The secondary vulnerability is the failure to check return codes [CWE-252: Unchecked Return Value](http://cwe.mitre.org/data/definitions/252.html). That is, we still use a buffer that was supposed to be allocated even though the allocation fails due to the extremely large (or small) negative value passed in by the user.

## Additional Notes:

This CB has a check to ensure that the length parameter is even. So the triggering mechanism must be an even negative value in 2's complement.
