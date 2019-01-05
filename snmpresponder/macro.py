#
# This file is part of snmpresponder software.
#
# Copyright (c) 2019, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpresponder/license.html
#


def expandMacro(option, context):
    for k in context:
        pat = '${%s}' % k
        if option and '${' in option:
            option = option.replace(pat, str(context[k]))
    return option


def expandMacros(options, context):
    options = list(options)
    for idx, option in enumerate(options):
        options[idx] = expandMacro(option, context)
    return options
