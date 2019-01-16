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
import concurrent.futures
import urllib.request
import json

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


# Persistent threaded executor

executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)


def load_url(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as conn:
        return json.loads(conn.read())


# MIB Managed Objects in the order of their OIDs

class SysnameObjectInstance(MibScalarInstance):

    REDFISH_SYSTEM_URL = 'http://demo.snmplabs.com/redfish/v1/Systems/437XR1138R2'

    def readTest(self, varBind, **context):
        # Just confirm that this MIB object instance is available
        cbFun = context['cbFun']
        cbFun(varBind, **context)

    def _callRestApi(self, varBind, **context):
        cbFun = context['cbFun']

        name, value = varBind

        future = executor.submit(load_url, self.REDFISH_SYSTEM_URL, 5)

        def done_callback(future):
            rsp = future.result()

            value = self.syntax.clone(rsp.get('Name', ''))

            cbFun((name, value), **context)

        future.add_done_callback(done_callback)

    def readGet(self, varBind, **context):
        self._callRestApi(varBind, **context)

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
            self._callRestApi((self.name, value), **context)


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
