
SNMP Command Responder
======================

The SNMP Command Responder tool is a general purpose, cross-platform,
extendable and multi-protocol SNMP agent implementation.

Key features:

* SNMPv1/v2c/v3 operations with built-in protocol and transport translation capabilities
* SNMPv3 USM supports MD5/SHA/SHA224/SHA256/SHA384/SHA512 auth and
  DES/3DES/AES128/AES192/AES256 privacy crypto algorithms
* Supports all SNMP commands
* Maintains multiple independent SNMP engines, network transports and MIB trees
* Offers versatile SNMP PDU routing towards a MIB tree implementation
* Supports asynchronous MIB objects API
* Extension modules supporting SNMP PDU filtering and on-the-fly modification
* Works on Linux, Windows and OS X

.. warning::

   As of January 2019, the SNMP Command Responder tool is being in active development.
   Some configuration options and APIs can change, some features may not work as
   intended.

Architecture
------------

The SNMP Command Responder tool is a daemon implementing one or more SNMP Command
Responders (which is the main part of the
`SNMP agent <https://tools.ietf.org/html/rfc3411#section-3.1.3.2>`_).

The main goal of SNMP is to expose interesting traits of a system being managed
through SNMP in terms of the SNMP/SMI data model. The SNMP responder package
leverages `PySMI <http://snmplabs.com/pysmi>`_ project's ability to build the
boilerplate Python code from ASN.1 MIB files. The generated code should then be
adapted by the user by linking the MIB objects to the actual system objects or
data sources to expose or manage through SNMP. The SNMP responder tool will
consume these Pythonized MIBs serving the objects defined there to the SNMP
clients (managers) on the network.

The SNMP Command Responder daemon can maintain one or more independent MIB trees
hooking up one or more MIB modules onto each tree. Aside from the MIB trees, SNMP
Command Responder can maintain one or more independent SNMP agents each listening
at one or more network endpoints.

The SNMP messages reaching any of the configured SNMP agents could then be routed
to any of the running MIB trees based on virtually any SNMP message property.
For instance, the criterion could be a source address of the incoming SNMP message
or SNMP credentials (e.g. SNMP community name, SNMPv3 user name, SNMP protocol
version etc) or a specific OID present in the message.

Besides SNMP message routing, SNMP Command Responder can modify SNMP PDU messages
before applying them on the MIB tree or on the response message on its way back to
SNMP manager. The logic behind SNMP message modification can be expressed in the
form of isolated `Python <http://www.python.org>`_ snippets of Python code called
:ref:`plugins <plugins>`. Users can implement their own plugins and configure
SNMP Responder to call them.

Configuration
-------------

The system is driven by command-line options and configuration files. Depending
on the desired system's configuration, the complexity of configuration files can
vary. We maintain a collection of use-cases and example configurations implementing
them.

.. toctree::
   :maxdepth: 2

   /configuration/index

MIB implementation
------------------

Ultimately, SNMP Command Responder works with its data backend to fetch or commit
the data SNMP managers instruct it to. The user is expected to interface one or more
SNMP MIB modules with the actual data sources they intend these MIB objects to
work with.

.. toctree::
   :maxdepth: 2

   /mib-implementation/index

Installation
------------

The easiest way to download and install SNMP Responder is via Python `pip` tool:

.. code-block:: bash

   # pip install snmpresponder

Alternatively, you can download the Python package from
`GitHub repo <https://github.com/etingof/snmpresponder/releases>`_ and install is manually.

The tool requires Python 2.6 up to Python 3.7.

Source code
-----------

SNMP Responder is a free and open source tool. It is distributed under highly
permissive :doc:`2-clause BSD license </license>`. You can fork or download source code from
`GitHub <https://github.com/etingof/snmpresponder>`_.

Detailed list of new features and fixes could be read in the :doc:`changelog </changelog>`.

Contact
-------

If something does not work as expected,
`open an issue <https://github.com/etingof/snmpresponder/issues>`_
at GitHub or post your question on
`Stack Overflow <http://stackoverflow.com/questions/ask>`_.
