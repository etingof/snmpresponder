
Single SNMP agent, single MIB tree
==================================

This is probably one of the simplest possible configurations. SNMP Command Responder
hosts just a single SNMP agent serving just a single MIB tree build out of a single
MIB.

You could test this configuration by running:

.. code-block:: bash

    $ snmpwalk -v2c -c public 127.0.0.1:1161 system

.. toctree::
   :maxdepth: 2

SNMP Command Responder is configured to:

* listen on UDP socket at localhost
* form a MIB tree out of a few objects of the SNMPv2-MIB module
* respond to SNMPv2c queries
* serve all queries against the configured MIB tree

.. literalinclude:: /../../conf/single-agent-single-mib-tree/snmpresponderd.conf

:download:`Download </../../conf/single-agent-single-mib-tree/snmpresponderd.conf>` configuration file.

The only implemented managed object
`SNMPv2-MIB::sysName.0 <http://mibs.snmplabs.com/asn1/SNMPv2-MIB>`_:

* gathers its value from a Python call
* only SNMP read operations are implemented
* write operation are allowed, but has no effect

.. literalinclude:: /../../conf/single-agent-single-mib-tree/managed-objects/SNMPv2-MIB::sysName.py

:download:`Download </../../conf/single-agent-single-mib-tree/managed-objects/SNMPv2-MIB::sysName.py>` MIB implementation.

For more information on MIB implementation refer to the
`MIB implementation <mib-implementation-chapter>`_ chapter in the documentation.
