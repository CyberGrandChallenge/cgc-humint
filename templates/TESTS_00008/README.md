# Echo Service

@Author: Lok Yan <Lok.Yan@us.af.mil>
@Group: AFRL

## Description:

This is a simple echo service that has a format string vulnerability as well as a buffer overflow vulnerability. This can be used for internal testing by CRSes to see whether they can support patching multiple vulnerabilities. Since the buffer overflow vulnerability is a rehash of CADET_00001, the only new vulnerability is the format string. 

The format string protocol is also designed so it supports both the standard escape character of % as well as the new escape character of $. Therefore, this challenge binary can also be used by CRSes to determine how well they handle non-standard format string escape sequences.

## Vulnerability Class: 

This challenge binary contains a [CWE-134: Uncontrolled Format String](http://cwe.mitre.org/data/definitions/134.html) vulnerability as well as a [CWE-121: Stack-based Buffer Overflow](http://cwe.mitre.org/data/definitions/121.html) vulnerability.

## Additional Notes:

This vulnerability supports the some of the standard format string escape sequences such as %s and %n to help the competitors determine if they can support the standard sequences. The vulnerability also supports an alternative format string escape sequence of $s and $n as a way for the competitors to see whether their logic can pick up the additional sequences.

