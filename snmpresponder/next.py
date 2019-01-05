#
# This file is part of snmpresponder software.
#
# Copyright (c) 2019, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpresponder/license.html
#


class Numbers(object):
    current = 0

    def getId(self):
        self.current += 1
        if self.current > 65535:
            self.current = 0
        return self.current

numbers = Numbers()

getId = numbers.getId
