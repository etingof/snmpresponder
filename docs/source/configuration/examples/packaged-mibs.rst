
Packaged MIBs
=============

SNMP command responder discovers `pip <https://en.wikipedia.org/wiki/Pip_(package_manager)>`_-installed
packages extending the *snmpresponder.mibs*
`entry point <https://packaging.python.org/specifications/entry-points/>`_.

The main advantage of packaged MIBs is easier distribution. That might make more sense for
generally useful and reusable MIB implementations such as
`HOST-RESOURCES-MIB <http://mibs.snmplabs.com/asn1/HOST-RESOURCES-MIB>`_.

This example configuration includes
`example Python package <https://github.com/etingof/snmpresponder/tree/master/examples/conf/packaged-mibs/snmpresponder-mibs-examples>`_,
which could be used as a blueprint for packaging other MIB implementations.

You could test this configuration by running the following command (you may need to have
`COFFEE-POT-MIB <http://mibs.snmplabs.com/asn1/COFFEE-POT-MIB>`_ installed
locally):

.. code-block:: bash

    $ snmpget -v2c -c public 127.0.0.1:1161 COFFEE-POT-MIB::potName.0

.. toctree::
   :maxdepth: 2

SNMP Command Responder is configured to:

* listen on UDP socket at localhost
* form a MIB tree out of all objects imported from the *examples* extension point
  (provided by installed *snmpresponder-mibs-examples* package)
* respond to SNMPv2c queries
* serve all queries against the configured MIB tree

.. literalinclude:: /../../examples/conf/packaged-mibs/snmpresponderd.conf

:download:`Download </../../examples/conf/packaged-mibs/snmpresponderd.conf>` configuration file.

The only implemented, read-only managed object is
`COFFEE-POT-MIB::potName.0 <http://mibs.snmplabs.com/asn1/COFFEE-POT-MIB>`_:

* serves a static value for *COFFEE-POT-MIB::potName.0* object
* only SNMP read operations are implemented
* write operation are allowed, but has no effect

.. literalinclude:: /../../examples/conf/packaged-mibs/snmpresponder-mibs-examples/snmpresponder_mibs_examples/COFFEE-POT-MIB::potName.py

:download:`Download </../../examples/conf/packaged-mibs/snmpresponder-mibs-examples/snmpresponder_mibs_examples/COFFEE-POT-MIB::potName.py>` MIB implementation.

For more information on MIB implementation refer to the
`MIB implementation <mib-implementation-chapter>`_ chapter in the documentation.
