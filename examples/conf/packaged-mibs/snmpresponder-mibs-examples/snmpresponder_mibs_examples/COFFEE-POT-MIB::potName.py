"""SNMP MIB module (COFFEE-POT-MIB) expressed in pysnmp data model.

This Python module is designed to be imported and executed by the
pysnmp library.

See http://snmplabs.com/pysnmp for further information.

Notes
-----
ASN.1 source http://mibs.snmplabs.com:80/asn1/COFFEE-POT-MIB
Produced by pysmi-0.4.0 at Sat Jan 12 14:01:57 2019
On host igarlic platform Darwin version 17.7.0 by user ilya
Using Python version 3.6.0 (v3.6.0:41df79263a11, Dec 22 2016, 17:23:13)
"""
if 'mibBuilder' not in globals():
    import sys

    sys.stderr.write(__doc__)
    sys.exit(1)


mibBuilder = globals()['mibBuilder']

MibScalarInstance, = mibBuilder.importSymbols(
    'SNMPv2-SMI',
    'MibScalarInstance'
)

# Import Managed Objects to base Managed Objects Instances on

potName, = mibBuilder.importSymbols(
    "COFFEE-POT-MIB",
    "potName"
)


# MIB Managed Objects in the order of their OIDs

class PotnameObjectInstance(MibScalarInstance):
    """Scalar Managed Object Instance with MIB instrumentation hooks.

    User can override none, some or all of the method below interfacing
    them to the data source they want to manage through SNMP.
    Non-overridden methods could just be removed from this class.

    See the SMI data model documentation at `http://snmplabs.com/pysnmp`.
    """
    def readTest(self, varBind, **context):
        cbFun = context['cbFun']
        cbFun(varBind, **context)

    def readGet(self, varBind, **context):
        name, value = varBind

        cbFun = context['cbFun']
        value = self.syntax.clone('mypot')
        cbFun((name, value), **context)

    def readTestNext(self, varBind, **context):
        name, value = varBind

        if name >= self.name:
            MibScalarInstance.readTestNext(self, varBind, **context)

        else:
            cbFun = context['cbFun']
            cbFun((self.name, value), **context)

    def readGetNext(self, varBind, **context):
        name, value = varBind

        if name >= self.name:
            MibScalarInstance.readGetNext(self, varBind, **context)

        else:
            value = self.syntax.clone('mypot')

            cbFun = context['cbFun']
            cbFun((self.name, value), **context)


_potName = PotnameObjectInstance(
     potName.name,
     (0,),
     potName.syntax
)

# Export Managed Objects Instances to the MIB builder

mibBuilder.exportSymbols(
    "__COFFEE-POT-MIB",
    **{"potName": _potName}
)
