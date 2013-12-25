# -*- coding: utf-8 -*-
from inspector.saql.sams import SAMS


if __name__ == '__main__':
    sams = SAMS()
    while True:
        qs = raw_input('SAQL> ').strip()
        if qs == '\q':
            break
        try:
            result = sams.run(qs)
        except ValueError as e:
            print('ERROR: {0}'.format(e.message))
        else:
            if result is not None:
                print result
    print('bye!')
