#!/usr/bin/env python2.7
# encoding: utf-8

"""
    @brief: 
    @author: icejoywoo
    @date: 16/2/23
"""

import types


class Config(object):
    """ Simple config
    """

    def __init__(self, c):

        self._c = c

    def flatten(self, c=None, parent=None):
        """ make a dict to a flatten dict
        for example:
        {
            'common': {
                'a': 5,
                'b': [1, 2, 3, 5],
                'c': 'aa',
            },
            'host': 'xxx.com',
        }
        =>
        {
            'common.a': 5,
            'common.b': [1, 2, 3, 5],
            'common.c': 'aa',
            'host': 'xxx.com',
        }
        @param c: dict
        @param parent: key prefix
        @return:
        """
        if c is None:
            c = self._c

        def concat_parent(p):
            if parent:
                return '%s.%s' % (parent, p)
            else:
                return p
        ret = {}
        for k, v in c.items():
            if isinstance(v, types.DictType):
                ret.update(self.flatten(c=v, parent=concat_parent(k)))
            else:
                ret[concat_parent(k)] = v
        return ret


if __name__ == '__main__':
    c = Config({
        'common': {
            'a': 5,
            'b': [1, 2, 3, 5],
            'c': 'aa',
        },
        'host': 'xxx.com',
    })
    print c.flatten()
