
MIB object calls REST API
=========================

In this configuration, SNMP responder serves a scalar MIB object backed by a REST API.

You could test this configuration by running:

.. code-block:: bash

    $ snmpget -v2c -c public 127.0.0.1:1161 SNMPv2-MIB::sysName.0

.. toctree::
   :maxdepth: 2

SNMP Command Responder is configured to:

* listen on UDP socket at localhost
* form a MIB tree out of a few objects of the SNMPv2-MIB module
* respond to SNMPv2c queries
* serve all queries against the configured MIB tree

.. literalinclude:: /../../conf/rest-api-backend/snmpresponderd.conf

:download:`Download </../../conf/rest-api-backend/snmpresponderd.conf>` configuration file.

The only implemented managed object
`SNMPv2-MIB::sysName.0 <http://mibs.snmplabs.com/asn1/SNMPv2-MIB>`_:

* gathers its value from a `REST API call <http://demo.snmplabs.com/redfish/v1/Systems/437XR1138R2>`_
* REST API call is done asynchronously, from separate thread(s)
* only SNMP read operations are implemented
* write operation are allowed, but has no effect

.. literalinclude:: /../../conf/rest-api-backend/managed-objects/SNMPv2-MIB::sysName.py

:download:`Download </../../conf/rest-api-backend/managed-objects/SNMPv2-MIB::sysName.py>` MIB implementation.

For more information on MIB implementation refer to the
`MIB implementation <mib-implementation-chapter>`_ chapter in the documentation.
