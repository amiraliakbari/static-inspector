#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import time
import socket

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '..', 'inspector'))
from inspector.saql.sams import SAMS


TCP_IP = '127.0.0.1'
TCP_PORT = 6789
BUFFER_SIZE = 102400  # Normally 1024, but we want fast response


if __name__ == '__main__':
    sams = SAMS()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((TCP_IP, TCP_PORT))
    s.listen(1)

    conn, addr = s.accept()
    print "Server Up!"
    while 1:
        data = conn.recv(BUFFER_SIZE)
        if not data:
            break
        print "received data:", data

        qs = data
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
                conn.send(str(result))
            else:
                conn.send('None')
            print('{0:.1f}ms, {1} chars sent'.format(d * 1000, len(result)))

    print('bye!')
    conn.close()
