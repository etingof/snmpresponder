
Macro substitution
==================

Many configuration options may refer to *macros* that get expanded
in the context of running request. That let you make your configuration
more compact and dynamic.

The syntax of a macro reference resembles `bash` variable syntax: dollar sign
followed by macro name in braces e.g. *${name}*.

.. _system-macros:

System macros
-------------

.. _config-dir-macro:

*config-dir*
++++++++++++

Gets expanded to the directory component of *snmpresponderd* process
configuration file.

Example:

.. code-block:: bash

    example-plugin {
      plugin-module: rewrite
      plugin-options: config=${config-dir}/plugins/example.conf

      plugin-id: example
    }

.. _snmp-macros:

SNMP macros
-----------

These macros get expanded into a value coming from SNMP
message being processed.

.. _snmp-engine-id-macro:

*snmp-engine-id*
++++++++++++++++

`SNMP Engine ID <https://tools.ietf.org/html/rfc3411#section-3.1.1.1>`_ value
from incoming SNMP request. Should match the *snmp-engine-id* configured
to the SNMP engine instance serving this request.

.. _snmp-transport-domain-macro:

*snmp-transport-domain*
+++++++++++++++++++++++

Object Identifier matching the *snmp-transport-domain* value through which
current SNMP request was received.

.. _snmp-peer-address-macro:

*snmp-peer-address*
+++++++++++++++++++

Network address (IPv4/IPv6) from which SNMP message has been received.

.. _snmp-peer-port-macro:

*snmp-peer-port*
++++++++++++++++

Network port number (UDP) from which SNMP message has been received.

.. _snmp-bind-address-macro:

*snmp-bind-address*
+++++++++++++++++++

Network address (IPv4/IPv6) at which SNMP message has been received. Matches
*snmp-bind-address* configured to the SNMP engine instance serving this request.

.. _snmp-bind-port-macro:

*snmp-bind-port*
++++++++++++++++

Network port number (UDP) at which SNMP message has been received. Matches
*snmp-bind-address* configured to the SNMP engine instance serving this request.

.. _snmp-security-model-macro:

*snmp-security-model*
+++++++++++++++++++++

`SNMP Security Model <https://tools.ietf.org/html/rfc3412#section-6.5>`_ value
from incoming SNMP request. Should match the *snmp-security-model* configured
to the SNMP engine instance serving this request.

.. _snmp-security-level-macro:

*snmp-security-level*
+++++++++++++++++++++

`SNMP Security Level <https://tools.ietf.org/html/rfc3411#section-3.4.3>`_ value
from incoming SNMP request. Should match the *snmp-security-level* configured
to the SNMP engine instance serving this request.

.. _snmp-security-name-macro:

*snmp-security-name*
++++++++++++++++++++

`SNMP Security Name <https://tools.ietf.org/html/rfc3411#section-3.2.2>`_ value
from incoming SNMP request. Should match the *snmp-security-name* configured
to the SNMP engine instance serving this request.

.. _snmp-security-engine-id-macro:

*snmp-security-engine-id*
+++++++++++++++++++++++++

`SNMP Security Engine ID <https://tools.ietf.org/html/rfc3412#section-7.1>`_
value from incoming SNMP request.

.. _snmp-context-engine-id-macro:

*snmp-context-engine-id*
++++++++++++++++++++++++

`SNMP Context Engine ID <https://tools.ietf.org/html/rfc3412#section-6.8.1>`_
value from incoming SNMP request. Should match the *snmp-context-id* configured
to the SNMP engine instance serving this request.

.. _snmp-context-name-macro:

*snmp-context-name*
+++++++++++++++++++

`SNMP Context Name <https://tools.ietf.org/html/rfc3412#section-6.8.2>`_ value
from incoming SNMP request. Should match the *snmp-context-name* configured
to the SNMP engine instance serving this request.

Examples
--------

Transparent SNMP proxy configuration implies sending packets spoofing original
network addresses. The spoofing part can be captured by configuring a macro:

.. code-block:: bash

    snmp-credentials {
        # send from source address of original SNMP request
        snmp-bind-address: ${snmp-peer-address}
        snmp-peer-address: 104.236.166.95:161

        snmp-peer-id: snmplabs-v3-original-source

        ... the rest of SNMP options
    }

.. warning::

   For spoofing to succeed *snmp-transport-domain* types should belong to the
   same address family e.g. UDP/IPv4 or UDP/IPv6.
