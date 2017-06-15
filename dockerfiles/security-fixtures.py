#!/usr/bin/env python

import socket
import time
import os
from contextlib import closing

def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, port)) == 0:
            return True
        else:
            return False

RELAY_TMP = '/tmp/sig-fixture-with-relays.sql'

relays = ['BigSenseTester', 'GPSTestLocationZero', 'GPSTestLocationNegativeLatLong',
          'GPSTestLocationNegativeLat', 'GPSTestLocationNegativeLong', 'GPSTestAccuracyOnly',
          'GPSTestDeltaOnly', 'GPSTestAllNoClimbTrack', 'GPSTestLocationTen',
          'GPSTestLocationHundred', 'GPSTestLocationThousand', 'GPSTestLocationOnly', 'GPSTestNoLocation']

dbs = { 'mssql': 1433, 'postgres': 5432, 'mysql': 3306 }

with open('sig-fixture.sql', 'r') as template:
    sql = ''.join(template.readlines())

with open(RELAY_TMP, 'w') as out:
    for r in relays:
        out.write(sql.replace('%relay%', r))
        for f in ['XML', 'JSON']:
            out.write(sql.replace('%relay%', '{}{}'.format(r, f)))

for db,port in dbs.iteritems():
    while True:
        if not check_socket('bigsense-db-{}'.format(db), port):
            print('DB/Port {}/{} not ready. Retrying...'.format(db, port))
            time.sleep(1)
        else:
            uclient = 'pgx' if db is 'postgres' else db
            cmd = 'bin/usql {}://bigsense:bigsense@bigsense-db-{}/bigsense --file {}'.format(uclient, db, RELAY_TMP)
            print('Executing: {}'.format(cmd))
            os.system(cmd)
            break
