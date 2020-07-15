# -*- coding: utf-8 -*-
#!/usr/bin/python2

import sys
import logging
import time
from essp_api import EsspApi


Euros = {0:0, 1:5, 2:10, 3:20}

essp = EsspApi('/dev/ttyACM0', logger_handler=logging.StreamHandler(sys.stdout))
essp.sync()
essp.enable_higher_protocol()
essp.set_inhibits(essp.easy_inhibit([1, 1, 1, 1, 1, 1, 1]), '0')
essp.enable()
while True:
    poll = essp.poll()
    for p in poll:
        #print p
        #if p['status'] == essp.READ_NOTE and p['param'] > 0:
            #for i in range(0, 10):
            #    essp.hold()
            #    print 'Hold...'
            #    time.sleep(0.5)
            #if p['param'] == 2: essp.reject_note()
        if p['status'] == EsspApi.CREDIT_NOTE:
            #print type(p['param'])
            #print 'Credit: %s' % p['param']
            print Euros[p['param']]
    time.sleep(0.5)
