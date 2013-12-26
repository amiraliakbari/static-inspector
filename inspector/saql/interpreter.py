# -*- coding: utf-8 -*-
import sys
import time
from inspector.saql.sams import SAMS


if __name__ == '__main__':
    sams = SAMS()

    try:
        ind = sys.argv.index('-d')
    except ValueError:
        pass  # no database specified
    else:
        sams.open_project(sys.argv[ind + 1])

    while True:
        try:
            qs = raw_input('SAQL> ').strip()
        except EOFError:
            print('')
            break

        if not qs:
            continue
        if qs == '\q':
            break

        try:
            start_time = time.time()
            result = sams.run(qs)
            d = time.time() - start_time
        except ValueError as e:
            print('ERROR: {0}'.format(e.message))
        else:
            if result is not None:
                print(result)
            print('{0:.1f}ms'.format(d * 1000))
    print('bye!')
