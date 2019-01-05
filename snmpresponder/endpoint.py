#
# This file is part of snmpresponder software.
#
# Copyright (c) 2019, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpresponder/license.html
#
import re

from snmpresponder.error import SnmpResponderError

from pysnmp.carrier.asyncore.dgram import udp
try:
    from pysnmp.carrier.asyncore.dgram import udp6
except ImportError:
    udp6 = None


def parseTransportAddress(transportDomain, transportAddress, transportOptions, defaultPort=0):
    if (('transparent-proxy' in transportOptions or
         'virtual-interface' in transportOptions) and '$' in transportAddress):
        addrMacro = transportAddress

        if transportDomain[:len(udp.domainName)] == udp.domainName:
            h, p = '0.0.0.0', defaultPort
        else:
            h, p = '::0', defaultPort

    else:
        addrMacro = None

        if transportDomain[:len(udp.domainName)] == udp.domainName:
            if ':' in transportAddress:
                h, p = transportAddress.split(':', 1)
            else:
                h, p = transportAddress, defaultPort
        else:
            hp = re.split(r'^\[(.*?)\]:([0-9]+)', transportAddress, maxsplit=1)
            if len(hp) != 4:
                raise SnmpResponderError('bad address specification')

            h, p = hp[1:3]

        try:
            p = int(p)

        except (ValueError, IndexError):
            raise SnmpResponderError('bad port specification')

    return (h, p), addrMacro
