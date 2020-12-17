#!/usr/bin/env python3

import urllib.request
import gpiod
import sys

global pulses
pulses = 0

if __name__ == '__main__':

    with gpiod.Chip('gpiochip0') as chip:

        power = chip.get_lines([22])
        power.request(consumer=sys.argv[0], type=gpiod.LINE_REQ_DIR_OUT, default_vals=[1])
        power.set_values([1])

        lines = chip.get_lines([17])
        lines.request(consumer=sys.argv[0], type=gpiod.LINE_REQ_EV_FALLING_EDGE)
        while True:
            ev_lines = lines.event_wait(nsec=600000000)
            if ev_lines:
                for line in ev_lines:
                    pulses += 1
                    event = line.event_read()
            else:
                if pulses > 0:
                    try:
                        urllib.request.urlopen('http://localhost:8080/%s' % pulses)
                    except:
                        pass
                pulses = 0
