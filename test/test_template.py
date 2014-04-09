#!/bin/env python
# ^_^ encoding: utf-8 ^_^
# @date: 14-4-9

__author__ = 'icejoywoo'

import os
from simutils import template

# template必须有后缀名
t = template.render(loc=os.path.join(os.path.dirname(__file__), "templates"))

print t.simple_template(name="John", xx=xrange(10))