
Example MIB implementation
--------------------------

The [SNMP Command Responder](http://snmplabs.com/snmpresponder) tool runs one
or more SNMP agents and maintains one or more trees of SNMP managed objects
(i.e. MIBs). Users can interface those managed objects with the data they
are willing to serve over SNMP.

User MIBs can be handed over to SNMP Command Responder as stand-alone files
or as `pip`-installable Python packages. In the latter case SNMP Command
Responder will discover those MIBs and serve them (if configured to do so).

The `snmpresponder-mibs-examples` Python package contains a blueprint though
functional MIB implementation aiming at guiding the user to package their own
MIB implementations.

How to implement MIBs
---------------------

MIB implementation is not dependent on the way how Python MIB modules
are distributed, the same MIB module can be shipped as a stand-alone
Python file or within an installable Python package.

Please, refer to SNMP Command Responder
[documentation](http://snmplabs.com/snmpresponder/mib-implementation/index.html)
for more information on MIB implementation workflow.

How to use MIB implementation
-----------------------------

First you need to [configure](http://snmplabs.com/snmpresponder/configuration/index.html)
SNMP Command Responder to stand up at least one SNMP agent. Proceed by
`pip`-installing packaged MIB implementation of your choice and configuring
the desired MIB(s) from the installed package by means of the
[mib-code-packages-pattern-list](http://snmplabs.com/snmpresponder/configuration/snmpresponderd.html#mib-trees)
option:

```
managed-objects-group {
  mib-text-search-path-list: http://mibs.snmplabs.com/asn1/

  # Load up and serve all MIBs from "snmpresponder-mibs-examples" package
  mib-code-packages-pattern-list: examples\..*

  mib-tree-id: managed-objects-1
}
```

Getting help
------------

If something does not work as expected or we are missing an interesting feature,
[open an issue](https://github.com/etingof/snmpresponder/issues) at GitHub or
post your question [on Stack Overflow](https://stackoverflow.com/questions/ask).

Copyright (c) 2019, [Ilya Etingof](mailto:etingof@gmail.com). All rights reserved.
