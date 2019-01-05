
SNMP Responder configuration
============================

SNMP Responder daemon is essentially a versatile SNMP agent listening
on one or many network endpoints and maintaining one or more instances
of MIB trees.

Basic configuration strategy could be:

* Configure SNMP credentials and SNMP agent(s) listening for SNMP
  managers to communicate with. Each SNMP agent is identified by
  `snmp-credentials-id-option`_.

* Configure SNMP contexts. Each SNMP context is identified by
  `snmp-context-id-option`_ option.

* Configure individual SNMP peers (i.e. SNMP managers) or groups of peers
  that you expect to talk to the SNMP responder. Each peer or group is identified
  by the `snmp-peer-id-option`_ option.

* Configure one or more MIB trees along with the MIB modules they accommodate.
  Each tree is identified by the `mib-tree-id-option`_ which is used
  for message routing and other purposes.

* Optionally configure plugins. These are small Python code snippets
  capable to access/modify/block passing SNMP message. You should
  configure each module you intend to use (giving search path, module
  file name, options) and assign it `plugin-id-option`_. Then you could list
  these IDs in the routing section.

* Configure message routing in form of `matching-snmp-credentials-id-list-option`_,
  `matching-snmp-peer-id-list-option`_, `matching-snmp-content-id-list-option`_ and
  `matching-snmp-context-id-list-option`_ options mapped to the contents of
  `using-mib-tree-id-option`_. The latter identifies the MIB tree to apply the received
  SNMP message to.

.. _global-options-chapter:

Global options
--------------

.. _config-version-option:

*config-version*
++++++++++++++++

Configuration file language version. Currently recognized version is *2*.

.. _program-name-option:

*program-name*
++++++++++++++

Program name to consume this configuration file. The only valid value is
*snmpresponderd*.

.. _snmp-agents-options-chapter:

SNMP agents options
-------------------

.. _snmp-engine-id-option:

*snmp-engine-id*
++++++++++++++++

SNMP engine identifier that creates a new, independent instance of SNMP engine.
All other SNMP settings scoped within this *snmp-engine-id* apply to this
SNMP engine instance.

An instance of SNMP Command Responder can have many independent SNMP engine
instances running concurrently.

Example:

.. code-block:: bash

    {
        snmp-engine-id: 0x0102030405070809

        ... other SNMP settings for this SNMP engine
    }
    {
        snmp-engine-id: 0x090807060504030201

        ... other SNMP settings for this SNMP engine
    }

.. _snmp-transport-domain-option:

*snmp-transport-domain*
+++++++++++++++++++++++

Creates listening network socket of specified type under given
name (OID).

Transport type is determined by the OID prefix, while the whole OID
is identified by the endpoint ID.

Recognized transport types i.e. OID prefixes are:

* UDP/IPv4 - *1.3.6.1.6.1.1*
* UDP/IPv6 - *1.3.6.1.2.1.100.1.2*

Any integer value can serve as OID suffix.

Examples:

.. code-block:: bash

    snmp-transport-domain: 1.3.6.1.6.1.1.123
    snmp-bind-address: 127.0.0.1:5555

Where *1.3.6.1.6.1.1* identifies UDP-over-IPv4 transport and *123* identifies
transport endpoint listening at IPv4 address 127.0.0.1, UDP port 5555.

.. code-block:: bash

    snmp-transport-domain: 1.3.6.1.2.1.100.1.2.123
    snmp-bind-address: [::1]:5555

Here *1.3.6.1.2.1.100.1.2* identifies UDP-over-IPv6 transport and *123* identifies
transport endpoint listening at IPv6 address ::1, UDP port 5555.

.. _snmp-transport-options-option:

*snmp-transport-options*
++++++++++++++++++++++++

Enable advanced networking options. Valid values are:

* *transparent-proxy* - enables source IP spoofing for SNMP responses and
  allows reception of SNMP requests destined to any IP address even if no such
  IP interface is present on the system

* *virtual-interface* - makes SNMP responses originating from the same IP
  network interface where the SNMP request has come to

The *transparent-proxy* option can be used to serve many SNMP agents on the IPs
that do not actually exist on the network.

.. note::

    Additional network configuration (perhaps policy routing) is required on
    the network to make SNMP request packets reaching the host where SNMP
    Command Responder is running and accepting them by the host.

.. _snmp-bind-address-option:

*snmp-bind-address*
+++++++++++++++++++

Listen for SNMP packets at this network address. Example:

.. code-block:: bash

    udp-listener-123 {
        snmp-transport-domain: 1.3.6.1.6.1.1.200
        snmp-bind-address: 127.0.0.1:161
        snmp-credentials-id: agent-10
    }


.. note::

    If you want response SNMP messages to have source address of the SNMP request
    destination address (as opposed to primary network interface address when
    *snmp-bind-address* is set to *0.0.0.0*), make sure to enable the
    `snmp-transport-options-option`_ = *virtual-interface* option.

.. _snmp-security-model-option:

*snmp-security-model*
+++++++++++++++++++++

SNMP version to use. Valid values are:

* *1* - SNMP v1
* *2* - SNMP v2c
* *3* - SNMP v3

.. _snmp-security-level-option:

*snmp-security-level*
+++++++++++++++++++++

SNMPv3 security level to use. Valid values are

* *1* - no message authentication and encryption
* *2* - do message authentication, do not do encryption
* *3* - do both authentication and encryption

.. _snmp-security-name-option:

*snmp-security-name*
++++++++++++++++++++

Identifier that logically groups SNMP configuration settings together.

.. note::

    Must be unique within SNMP engine instance (e.g. `snmp-engine-id-option`_).

.. _snmp-security-engine-id-option:

*snmp-security-engine-id*
+++++++++++++++++++++++++

The authoritative (security) SNMPv3 Engine ID to use when receiving SNMPv3
messages from SNMP peers. For receiving SNMP Commands, it is not necessary to
specify *snmp-security-engine-id* engine ID, as *snmp-engine-id* might suffice.

Example:

.. code-block:: bash

    {
        snmp-security-engine-id: 0x0102030405070809
    }

.. _snmp-community-name-option:

*snmp-community-name*
+++++++++++++++++++++

SNMP community string for SNMP v1/v2c.

.. _snmp-usm-user-option:

*snmp-usm-user*
+++++++++++++++

SNMPv3 USM username.

.. _snmp-usm-auth-protocol-option:

*snmp-usm-auth-protocol*
++++++++++++++++++++++++

SNMPv3 message authentication protocol to use. Valid values are:

+--------+----------------+-------------+
| *ID*   |  *Algorithm*   | *Reference* |
+--------+----------------+-------------+
| NONE   | -              | RFC3414     |
+--------+----------------+-------------+
| MD5    | HMAC MD5       | RFC3414     |
+--------+----------------+-------------+
| SHA    | HMAC SHA-1 128 | RFC3414     |
+--------+----------------+-------------+
| SHA224 | HMAC SHA-2 224 | RFC7860     |
+--------+----------------+-------------+
| SHA256 | HMAC SHA-2 256 | RFC7860     |
+--------+----------------+-------------+
| SHA384 | HMAC SHA-2 384 | RFC7860     |
+--------+----------------+-------------+
| SHA512 | HMAC SHA-2 512 | RFC7860     |
+--------+----------------+-------------+

.. _snmp-usm-auth-key-option:

*snmp-usm-auth-key*
+++++++++++++++++++

SNMPv3 message authentication key.

.. note::

    Must be 8 or more characters.

.. _snmp-usm-priv-protocol-option:

*snmp-usm-priv-protocol*
++++++++++++++++++++++++

SNMPv3 message encryption protocol to use. Valid values are:

+------------+------------------------+----------------------+
| *ID*       | *Algorithm*            | *Reference*          |
+------------+------------------------+----------------------+
| NONE       | -                      | RFC3414              |
+------------+------------------------+----------------------+
| DES        | DES                    | RFC3414              |
+------------+------------------------+----------------------+
| AES        | AES CFB 128            | RFC3826              |
+------------+------------------------+----------------------+
| AES192     | AES CFB 192            | RFC Draft            |
+------------+------------------------+----------------------+
| AES256     | AES CFB 256            | RFC Draft            |
+------------+------------------------+----------------------+
| AES192BLMT | AES CFB 192 Blumenthal | RFC Draft            |
+------------+------------------------+----------------------+
| AES256BLMT | AES CFB 256 Blumenthal | RFC Draft            |
+------------+------------------------+----------------------+
| 3DES       | Triple DES EDE         | RFC Draft            |
+------------+------------------------+----------------------+

.. _snmp-usm-priv-key-option:

*snmp-usm-priv-key*
+++++++++++++++++++

SNMPv3 message encryption key.

.. note::

    Must be 8 or more characters.

.. _snmp-credentials-id-option:

*snmp-credentials-id*
+++++++++++++++++++++

Unique identifier of a collection of SNMP configuration options. Used to
assign specific SNMP configuration to a particular SNMP entity. Can also be
used to share the same SNMP configuration among multiple SNMP entities.

This option can contain :ref:`SNMP macros <snmp-macros>`.

Example:

.. code-block:: bash

    my-snmpv3-user {
      snmp-security-level: 3
      snmp-security-name: test-user

      snmp-usm-user: test-user
      snmp-usm-auth-protocol: 1.3.6.1.6.3.10.1.1.2
      snmp-usm-auth-key: authkey1
      snmp-usm-priv-protocol: 1.3.6.1.6.3.10.1.2.2
      snmp-usm-priv-key: privkey1

      snmp-transport-domain: 1.3.6.1.6.1.1.200
      snmp-bind-address: 127.0.0.1:161

      snmp-credentials-id: snmpv3-agent-at-localhost
    }

.. _plugin-options-chapter:

Plugin options
--------------

The plugin options instantiate a :ref:`plugin <plugins>` file with
specific configuration options and assign an identifier to it. You
can have many differently configured instances of the same plugin
module in the system.

.. _plugin-modules-path-list-option:

*plugin-modules-path-list*
++++++++++++++++++++++++++

Directory search path for plugin modules.

This option can reference :ref:`config-dir <config-dir-macro>` macro.

.. _plugin-module-option:

*plugin-module*
+++++++++++++++

Plugin module file name to load and run (without .py).

.. _plugin-options-option:

*plugin-options*
++++++++++++++++

Plugin-specific configuration option to pass to plugin.

This option can reference :ref:`config-dir <config-dir-macro>` macro.

.. _plugin-id-option:

*plugin-id*
+++++++++++

Unique identifier of a plugin module (`plugin-module-option`_) and its
options (`plugin-options-option`_).

This option can reference :ref:`config-dir <config-dir-macro>` macro.

The *plugin-id* identifier is typically used to invoke plugin
in the course of SNMP message processing.

Example:

.. code-block:: bash

    rewrite-plugin {
      plugin-module: rewrite
      plugin-options: config=${config-dir}/plugins/rewrite.conf

      plugin-id: rewrite
    }

    logging-plugin {
      plugin-module: logger
      plugin-options: config=/etc/snmpfwd/plugins/logger.conf

      plugin-id: logger
    }


.. mib-tree-options-chapter:

MIB trees
---------

SNMP Command Responder can build one or more trees of MIB objects read from
MIB modules. The SNMP commands will be executed against one of the MIB
trees as selected by system configuration.

.. note::

    With classical SNMP agent, *SNMP context* is likely to be used for
    similar purpose, however SNMP Command Responder is a bit more flexible
    as practically any aspect of SNMP command could be used for MIB tree
    selection.

.. _mib-text-search-path-list:

*mib-text-search-path-list*
+++++++++++++++++++++++++++

List of URIs where SNMP Command responder should search for ASN.1 MIBs on which
the MIBs being served depend on.

.. _mib-code-modules-pattern-list:

*mib-code-modules-pattern-list*
+++++++++++++++++++++++++++++++

List of regular expressions denoting filesystem paths where SNMP Command
Responder should search for MIB modules expressed in pysnmp MIB/SMI data model.
The matching modules will be loaded, executed and brought on-line by SNMP
Command Responder and served to SNMP managers.

.. note::

   Refer to `MIB implementation <mib-implementation-chapter>`_ chapter for
   information on how to prepare MIB implementation module.

.. _mib-tree-id-option:

*mib-tree-id*
+++++++++++++

Unique identifier of a MIB tree instance. It's used solely for SNMP message routing.

.. code-block:: bash

    mib-tree-group {

        mib-text-search-path-list: http://mibs.snmplabs.com/asn1/

        network-mibs {
            mib-code-modules-pattern-list: conf/generic/managed-objects/(IF-MIB|UDP-MIB).py

            mib-tree-id: network-mibs
        }

        host-mibs {
            mib-code-modules-pattern-list: conf/generic/managed-objects/HOST.*MIB.py

            mib-tree-id: host-mibs
        }
    }

.. note::

   Refer to `MIB implementation <mib-implementation-chapter>`_ chapter for
   information on how to prepare MIB implementation module.

.. _snmp-context-matching-chapter:

SNMP context matching
---------------------

.. _snmp-context-engine-id-pattern-option:

*snmp-context-engine-id-pattern*
++++++++++++++++++++++++++++++++

A regular expression matching SNMPv3 messages by SNMP context engine ID.

.. _snmp-context-name-pattern-option:

*snmp-context-name-pattern*
+++++++++++++++++++++++++++

A regular expression matching SNMPv3 messages by SNMP context name.

.. _snmp-context-id-option:

*snmp-context-id*
+++++++++++++++++

Unique identifier of a collection of SNMP context configuration options. Used for
matching SNMP context options in inbound SNMP messages
(e.g. `snmp-context-engine-id-pattern-option`_,
`snmp-context-name-pattern-option`_) for
message routing purposes.

This option can contain :ref:`SNMP macros <snmp-macros>`.

Example:

.. code-block:: bash

    context-group {
      snmp-context-engine-id-pattern: .*?
      snmp-context-name-pattern: .*?

      snmp-context-id: any-context
    }

.. _snmp-pdu-contents-matching-chapter:

SNMP PDU contents matching
--------------------------

.. _snmp-pdu-type-pattern-option:

*snmp-pdu-type-pattern*
+++++++++++++++++++++++

A regular expression matching SNMPv3 messages by SNMP PDU type.
Recognized PDU types are: *GET*, *SET*, *GETNEXT* and *GETBULK*.

.. code-block:: bash

    content-group {
      snmp-pdu-type-pattern: (GET|GETNEXT)
      snmp-content-id: get-content
    }

.. _snmp-pdu-oid-prefix-pattern-list-option:

*snmp-pdu-oid-prefix-pattern-list*
++++++++++++++++++++++++++++++++++

List of regular expressions matching OIDs in SNMP PDU var-binds.

.. _snmp-content-id-option:

*snmp-content-id*
+++++++++++++++++

Unique identifier of a collection of SNMP content matching options. Used for
matching the contents of inbound SNMP messages (e.g.
`snmp-pdu-type-pattern-option`_, `snmp-pdu-oid-prefix-pattern-list-option`_) for
message routing purposes.

This option can contain :ref:`SNMP macros <snmp-macros>`.

Example:

.. code-block:: bash

    content-group {
      write-pdu-group {
        snmp-pdu-type-pattern: SET
        snmp-content-id: set-content
      }

      oid-subtree-group {
        snmp-pdu-oid-prefix-pattern-list: 1\.3\.6\.1\.2\.1\.2\..*?
        snmp-content-id: oid-subtree-content
      }

      others {
        snmp-content-id: any-content
      }
    }

.. _network-peers-matching-chapter:

Network peers matching
----------------------

.. _snmp-peer-address-pattern-list-option:

*snmp-peer-address-pattern-list*
++++++++++++++++++++++++++++++++

List of regular expressions matching source transport endpoints
of SNMP message.

.. _snmp-bind-address-pattern-list-option:

*snmp-bind-address-pattern-list*
++++++++++++++++++++++++++++++++

List of regular expressions matching destination transport endpoints
of SNMP message.

.. note::

    If you want to receive SNMP messages at secondary network interfaces
    and be able to match them, make sure you enable the
    `snmp-transport-options-option`_ = *virtual-interface*.

.. _snmp-peer-id-option:

*snmp-peer-id*
++++++++++++++

Unique identifier matching pairs of source and destination SNMP transport
endpoints. Most importantly, `snmp-bind-address-pattern-list-option`_ and
`snmp-peer-address-pattern-list-option`_ as well as `snmp-transport-domain-option`_.
The *snmp-peer-id* is typically used for message routing purposes.

This option can contain :ref:`SNMP macros <snmp-macros>`.

Example:

.. code-block:: bash

    peers-group {
      snmp-transport-domain: 1.3.6.1.6.1.1.100
      snmp-peer-address-pattern-list: 10\.113\..*?
      snmp-bind-address-pattern-list: 127\.0\.0\.[2-3]:[0-9]+?

      snmp-peer-id: 101
    }

.. _message-routing-chapter:

Message routing
---------------

The purpose of these settings is to determine:

* plugin ID to pass SNMP message through
* MIB tree ID to apply SNMP message onto

This is done by searching for a combination of matching IDs.

.. _matching-snmp-context-id-list-option:

*matching-snmp-context-id-list*
+++++++++++++++++++++++++++++++

Evaluates to True if incoming SNMP message matches at least one
of `snmp-context-id-option`_ in the list.

.. _matching-snmp-content-id-list-option:

*matching-snmp-content-id-list*
+++++++++++++++++++++++++++++++

Evaluates to True if incoming SNMP message matches at least one
of `snmp-content-id-option`_ in the list.

.. _matching-snmp-credentials-id-list-option:

*matching-snmp-credentials-id-list*
+++++++++++++++++++++++++++++++++++

Evaluates to True if `snmp-credentials-id-option`_ used for processing incoming
SNMP message is present in the list.

.. _matching-snmp-peer-id-list-option:

*matching-snmp-peer-id-list*
++++++++++++++++++++++++++++

Evaluates to True if incoming SNMP message originates from and arrived at
one of the `snmp-peer-id-option`_ in the list.

.. _using-plugin-id-list-option:

*using-plugin-id-list*
++++++++++++++++++++++

Invoke each of the `plugin-id-option`_ in the list in order passing request and response
SNMP PDUs from one :ref:`plugin <plugins>` to the other.

Plugins may modify the message in any way and even block it from further
propagation in which case SNMP message will be dropped.

.. _using-mib-tree-id-option:

*using-mib-tree-id*
+++++++++++++++++++

Unique identifier matching a group of *matching-\** identifiers. Specifically,
these are: `matching-snmp-context-id-list-option`_, `matching-snmp-content-id-list-option`_,
`matching-snmp-credentials-id-list-option`_ and `matching-snmp-peer-id-list-option`_.

Incoming (and possibly modified) SNMP message will be forwarded to each
`mib-tree-id-option`_ present in the list.

Example:

.. code-block:: bash

    routing-map {
      matching-snmp-context-id-list: any-context
      matching-snmp-content-id-list: any-content

      route-1 {
        matching-snmp-credentials-id-list: config-1 config-2 config-121
        matching-snmp-content-id-list: if-subtree-content
        matching-snmp-peer-id-list: 100 111

        using-plugin-id-list: logger rewrite
        using-mib-tree-id: host-mib
      }
    }
