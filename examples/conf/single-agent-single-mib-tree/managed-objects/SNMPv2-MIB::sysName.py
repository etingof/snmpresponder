"""SNMP MIB module (SNMPv2-MIB) expressed in pysnmp data model.

This Python module is designed to be imported and executed by the
pysnmp library.

See http://snmplabs.com/pysnmp for further information.

Notes
-----
ASN.1 source file:///usr/share/snmp/mibs/SNMPv2-MIB.txt
Produced by pysmi-0.4.0 at Sun Jan 13 09:39:06 2019
On host igarlic platform Darwin version 17.7.0 by user ilya
Using Python version 3.6.0 (v3.6.0:41df79263a11, Dec 22 2016, 17:23:13) 
"""
import socket


if 'mibBuilder' not in globals():
    import sys

    sys.stderr.write(__doc__)
    sys.exit(1)


MibScalarInstance, = mibBuilder.importSymbols(
    'SNMPv2-SMI',
    'MibScalarInstance'
)

# Import Managed Objects to base Managed Objects Instances on

(sysName,) = mibBuilder.importSymbols(
    "SNMPv2-MIB",
    "sysName"
)


# MIB Managed Objects in the order of their OIDs


class SysnameObjectInstance(MibScalarInstance):
    def readTest(self, varBind, **context):
        # Just confirm that this MIB object instance is available
        cbFun = context['cbFun']
        cbFun(varBind, **context)

    def readGet(self, varBind, **context):
        cbFun = context['cbFun']

        name, value = varBind

        # Initialize response value from *gethostname()* return
        value = self.syntax.clone(socket.gethostname())

        cbFun((name, value), **context)

    def readTestNext(self, varBind, **context):
        name, value = varBind

        if name >= self.name:
            # This object does not qualify as "next*, pass the call
            MibScalarInstance.readTestNext(self, varBind, **context)

        else:
            # Confirm this object is available and report its OID
            cbFun = context['cbFun']
            cbFun((self.name, value), **context)

    def readGetNext(self, varBind, **context):
        name, value = varBind

        if name >= self.name:
            # This object does not qualify as "next*, pass the call
            MibScalarInstance.readGetNext(self, varBind, **context)

        else:
            cbFun = context['cbFun']

            # Initialize response value from *gethostname()* return
            value = self.syntax.clone(socket.gethostname())

            cbFun((self.name, value), **context)

_sysName = SysnameObjectInstance(
     sysName.name,
     (0,),
     sysName.syntax
)

# Export Managed Objects Instances to the MIB builder

mibBuilder.exportSymbols(
    "__SNMPv2-MIB",
    **{"sysName": _sysName}
)
