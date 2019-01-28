#!/usr/bin/env python
"""SNMP Command Responder MIBs implementations extension module.

Extension module to SNMP Command Responder tool implementing some
example MIBs.
"""
import sys
import os

classifiers = """\
Development Status :: 3 - Alpha
Environment :: Console
Intended Audience :: Developers
Intended Audience :: Education
Intended Audience :: Information Technology
Intended Audience :: System Administrators
Intended Audience :: Telecommunications Industry
License :: OSI Approved :: BSD License
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Topic :: Communications
Topic :: System :: Monitoring
Topic :: System :: Networking :: Monitoring
"""


def howto_install_setuptools():
    print("""
   Error: You need setuptools Python package!

   It's very easy to install it, just type:

   wget https://bootstrap.pypa.io/ez_setup.py
   python ez_setup.py

   Then you could make eggs from this package.
""")


if sys.version_info[:2] < (2, 6):
    print("ERROR: this package requires Python 2.6 or later!")
    sys.exit(1)

try:
    from setuptools import setup

    params = {
        'install_requires': ['snmpresponder<=0.1.0'],
        'zip_safe': True
    }

except ImportError:
    for arg in sys.argv:
        if 'egg' in arg:
            howto_install_setuptools()
            sys.exit(1)

    from distutils.core import setup

    params = {
        'requires': ['snmpresponder(<=0.1.0)']
    }

doclines = [x.strip() for x in (__doc__ or '').split('\n') if x]

params.update(
    {'name': "snmpresponder-mibs-examples",
     'version':  open(os.path.join('snmpresponder_mibs_examples', '__init__.py')).read().split('\'')[1],
     'description': doclines[0],
     'long_description': ' '.join(doclines[1:]),
     'maintainer': 'Ilya Etingof <etingof@gmail.com>',
     'author': "Ilya Etingof",
     'author_email': "etingof@gmail.com",
     'url': "https://github.com/etingof/snmpresponder",
     'platforms': ['any'],
     'classifiers': [x for x in classifiers.split('\n') if x],
     'packages': ['snmpresponder_mibs_examples'],
     'entry_points': {
         'snmpresponder.mibs': 'examples = snmpresponder_mibs_examples'
     },
     'license': "BSD"}
)

setup(**params)
