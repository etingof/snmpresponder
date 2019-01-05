
.. _mib-implementation-chapter:

MIB implementation
==================

SNMP Command Responder is designed to interface with user data source and serve
it on the network as SNMP agent(s).

The primary way of interfacing user data source with SNMP Command Responder
involves two steps:

* Using the `pysmi <http://snmplabs.com/pysmi>`_ project to compile ASN.1 MIB(s)
  into stubs of Python code
* Interfacing the desired objects with the intended data sources by adding
  custom Pythob code into the hooks

Example workflow
----------------

Let's step through the MIB object implementaton workflow using the
`SNMPv2-MIB::sysName.0 <http://mibs.snmplabs.com/asn1/SNMPv2-MIB>`_ managed
object as an example.

.. _mib-implementation-compilation:

Compile MIB into Python
+++++++++++++++++++++++

The MIB compiler and code generator shipped with the *pysmi* project is driven
by the `Jjinja2 <http://jinja.pocoo.org/docs/2.10/>`_ templates to produce the
desired code. User can use the default templates or extend them to adapt to
their needs.

One of the
`templates <https://github.com/etingof/pysmi/blob/master/pysmi/codegen/templates/pysnmp/mib-instrumentation/managed-objects-instances.j2>`_
*pysmi* ships can generate MIB instrumentation stubs for managed objects instances i.e.
the leaf MIB objects representing the instances of MIB scalars of tabular objects.

We can just call the `mibdump <http://snmplabs.com/pysmi/mibdump.html>`_ tool passing
it the above mentioned template:

.. code-block:: bash

   $ mibdump.py --no-dependencies \
       --destination-directory /etc/snmpresponder/managed-objects \
       --destination-format pysnmp \
       --destination-template pysnmp/mib-instrumentation/managed-objects-instances.j2 \
       SNMPv2-MIB

.. warning::

    Once the compilation is done, make sure to rename produced MIB file into a
    name which is different from MIB module name (*SNMPv2-MIB*) which is reserved
    for MIB definitions, not MIB implementation. For example it could be
    *__SNMPv2-MIB.py* or *SNMPv2-MIB::sysName.py*.

.. _mib-implementation-glue:

Add glue code
+++++++++++++

The produced Python stubs expose the extension points in the MIB managed objects
read, write, create and destroy workflows. On top of that, each of these
operations is performed on each SNMP request variable-binding in isolation from
the other variable-bindings and in a transactional "all or nothing" manner.

For sake of simplicity, let's focus solely on read operation performed in response
to SNMP GET/GETNEXT and GETBULK commands.

.. code-block:: python

    class SysnameObjectInstance(MibScalarInstance):
        """Scalar Managed Object Instance with MIB instrumentation hooks.

        User can override none, some or all of the method below interfacing
        them to the data source they want to manage through SNMP.
        Non-overridden methods could just be removed from this class.

        See the SMI data model documentation at `http://snmplabs.com/pysnmp`.
        """
        def readTest(self, varBind, **context):
            # Put your code here
            MibScalarInstance.readTest(self, varBind, **context)

        def readGet(self, varBind, **context):
            # Put your code here
            MibScalarInstance.readGet(self, varBind, **context)

        def readTestNext(self, varBind, **context):
            # Put your code here
            MibScalarInstance.readTestNext(self, varBind, **context)

        def readGetNext(self, varBind, **context):
            # Put your code here
            MibScalarInstance.readGetNext(self, varBind, **context)

.. note::

    In the above stubs, *readTest* and *readGet* methods are invoked on
    *SNMP GET* commands, while *readTestNext* and *readGetNext* are called
    on *SNMP GETNEXT/GETBULK* requests.

To obtain the value to serve the *SNMPv2-MIB::sysName.0* MIB object we could
simply call *gethostbyname()* from Python:

.. code-block:: pycon

    >>> import socket
    >>>
    >>> socket.gethostname()
    'igarlic'
    >>>

The MIB object API is asynchronous by design, the results should be delivered
via a callback function.

.. code-block:: python

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

.. note::

    MIB objects being implemented must be able to run asynchronously, that is
    they should never block on long-pending operations.

Finally, instantiate and export the newly defined MIB object instance:

.. code-block:: python

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

.. note::

    Unused Python stubs can be safely removed from the produced MIB code.

.. _mib-implementation-configuration:

Bring MIB implementation on-line
++++++++++++++++++++++++++++++++

Once the MIB module is implemented and passes Python syntax check (just
run it from command line):

.. code-block:: bash

    $ python SNMPv2-MIB::sysName.py
    SNMP MIB module (SNMPv2-MIB) expressed in pysnmp data model.

    This Python module is designed to be imported and executed by the
    pysnmp library.

    See http://snmplabs.com/pysnmp for further information.

    Notes
    -----
    ASN.1 source file:///usr/share/snmp/mibs/SNMPv2-MIB.txt
    Produced by pysmi-0.4.0 at Sun Jan 13 09:39:06 2019
    On host igarlic platform Darwin version 17.7.0 by user ietingof
    Using Python version 3.6.0 (v3.6.0:41df79263a11, Dec 22 2016, 17:23:13)

Copy the *SNMPv2-MIB::sysName.py* over to the directory where SNMP Command
Responder could `find it <mib-code-modules-pattern-list>`_ while building the
desired `MIB tree <mib-tree-id-option>`_.

If you place your MIB modules into */etc/snmpresponder/managed-objects*, the
example SNMP Command Responder MIB tree configuration entry could look like
this:

.. code-block:: bash

    snmpv2-mib-objects {
      mib-text-search-path-list: http://mibs.snmplabs.com/asn1/
      mib-code-modules-pattern-list: /etc/snmpresponder/managed-objects/.*py[co]?

      mib-tree-id: managed-objects-1
    }

Once you are done setting things up and restarting *snmpresponderd*, you should
be able to read the hostname via SNMP:

.. code-block:: bash

   $ snmpget -v2c -c public localhost SNMPv2-MIB::sysName.1
   SNMPv2-MIB::sysName.0 = STRING: igarlic
