# -*- coding: utf-8 -*-
#!/usr/bin/python2

import os
import re
import sys
import json
import serial
import atexit
import logging
import argparse
import datetime
from signal import SIGTERM
from wsgiref.simple_server import make_server
from webob import Request, exc
from time import sleep
from multiprocessing import Process, Queue
from essp_api import EsspApi

RESP_HEADERS = [('Access-Control-Allow-Origin', '*')]

class App(object):
    def __init__(self, params):
        self.params = params
        self.child = None
        self.routes = []
        self.queue_request = Queue()
        self.queue_response = Queue()
        self.credit = 0.0
        self.credit_coin = 0.0

    @staticmethod
    def _template_to_regex(template):
        regex = ''
        last_pos = 0
        var_regex = re.compile(r'\{(\w+)(?::([^}]+))?\}', re.VERBOSE)
        for match in var_regex.finditer(template):
            regex += re.escape(template[last_pos:match.start()])
            var_name = match.group(1)
            expr = match.group(2) or '[^/]+'
            expr = '(?P<%s>%s)' % (var_name, expr)
            regex += expr
            last_pos = match.end()
        regex += re.escape(template[last_pos:])
        regex = '^%s$' % regex
        return regex

    def add_route(self, template, view, **kwargs):
        self.routes.append((re.compile(self._template_to_regex(template)), view, kwargs))

    def __call__(self, environ, start_response):
        if not self.child or not self.child.is_alive():
            self.child = Process(
                target=note_acceptor_worker,
                args=(self.queue_request, self.queue_response, self.params)
            )
            self.child.daemon = True
            self.child.start()
        req = Request(environ)
        for regex, controller, kwvars in self.routes:
            match = regex.match(req.path_info)
            if match:
                req.urlvars = match.groupdict()
                req.urlvars.update(kwvars)
                res = json.dumps(controller(req))
                headers = RESP_HEADERS[:]
                headers.append(('Content-Length', str(len(res))),)
                start_response('200 OK', headers)
                return [res]
        return exc.HTTPNotFound()(environ, start_response)

    def index(self, req):
        return 'Usage: GET /start, /enable, /notes, /poll, /disable'


    def simple_cent(self, req):
        cmd = req.urlvars['cmd']
        if cmd == '5c':  self.credit_coin += 0.05
        if cmd == '10c': self.credit_coin += 0.1
        if cmd == '20c': self.credit_coin += 0.2
        if cmd == '50c': self.credit_coin += 0.5
        if cmd == '1e' : self.credit_coin += 1
        if cmd == '2e' : self.credit_coin += 2
        return 'ok'

    def simple_cmd(self, req):
        cmd = req.urlvars['cmd']
        if cmd in ('start', 'disable', 'enable'):
            self.credit = 0.0
            self.credit_coin = 0.0
        self.queue_request.put({'cmd': cmd})
        return 'ok'

    def poll(self, req):
        data = []
        while True:
            try:
                response = self.queue_response.get(block=False)
                try:
                    if response['credit']:
                        self.credit = response['credit']
                        #self.credit += self.credit_coin
                except:
                    pass
                data.append(response)
            except Exception:
                break
        return data

    def notes(self, req):
        self.poll(None)
        return '%.2f' % float(self.credit + self.credit_coin)


Euros = {0:0, 1:5, 2:10, 3:20, 4:50, 5:100, 6:200}
#   *   *   *   *   *   NOTE ACCEPTOR   *   *   *   *   *   *
def note_acceptor_worker(queue_request, queue_response, params):

    verbose = params.verbose
    lh = logging.FileHandler(params.logfile) if params.daemon else logging.StreamHandler(sys.stdout)
    essp = EsspApi(params.device, logger_handler=lh, verbose=(verbose and verbose > 1))
    logger = essp.get_logger()
    essp_state = 'disabled'
    
    logger.info('[WORKER] Start')
    cmds = {    'sync':         lambda: essp.sync,
                'enable':       lambda: essp.enable,
                'disable':      lambda: essp.disable,
                'hold':         lambda: essp.hold,
                'display_on':   lambda: essp.display_on,
                'display_off':  lambda: essp.display_off }
    
    credit = 0
    while True:
        try: cmd = queue_request.get(block=False)['cmd']
        except:
            pass
        else:
            res = {'cmd': cmd, 'result': False}
            logger.info('[WORKER] command: %s' % cmd)

            if cmd in ('start', 'disable'):
                credit = 0
                essp_state = 'disabled'
                
            elif cmd == 'enable':

                essp.sync()
                essp.enable_higher_protocol()
                #essp.disable()
                essp.set_inhibits(essp.easy_inhibit([1, 1, 1, 1, 1, 1, 1]), '0')

                credit = 0
                essp_state = 'enabled'
                    
            if cmd in cmds:
                res['result'] = cmds[cmd]()()
            
            elif cmd == 'start':
                credit = 0
                res['result'] = bool(
                    essp.sync() and
                    essp.enable_higher_protocol() and
                    essp.disable() and
                    essp.set_inhibits(essp.easy_inhibit([1, 1, 1, 1, 1, 1, 1]), '0'))
                
            queue_response.put(res)
            continue
        
        if essp_state == 'enabled':
            for event in essp.poll():
                status = event['status']
                param = event['param']
                if status == EsspApi.DISABLED:
                    continue

                if status == EsspApi.CREDIT_NOTE:
                    logger.info('[WORKER] credit %s' % Euros[param])
                    credit += Euros[param]
                elif status == EsspApi.READ_NOTE:
                    logger.info('[WORKER] read note %s' % param)
                queue_response.put({'cmd': 'poll', 'status': status, 'param': param, 'credit': credit})
                
        sleep(0.8)

        if os.getppid() == 1:
            logger.info('[WORKER] Parent process has terminated')
            break


def http_server_worker(params):
    app = App(params)
    app.add_route('/', app.index)

    app.add_route('/sync',    app.simple_cmd, cmd='sync')    # |reset
    app.add_route('/enable',  app.simple_cmd, cmd='enable')  # |reset
    app.add_route('/disable', app.simple_cmd, cmd='disable') # |reset
    app.add_route('/hold',    app.simple_cmd, cmd='hold')    # |reset

    app.add_route('/1', app.simple_cent, cmd='5c')
    app.add_route('/2', app.simple_cent, cmd='10c')
    app.add_route('/3', app.simple_cent, cmd='20c')
    app.add_route('/4', app.simple_cent, cmd='50c')
    app.add_route('/5', app.simple_cent, cmd='1e')
    app.add_route('/6', app.simple_cent, cmd='2e')

    app.add_route('/display_on',  app.simple_cmd, cmd='display_on')
    app.add_route('/display_off', app.simple_cmd, cmd='display_off')
    app.add_route('/start',       app.simple_cmd, cmd='start')
    app.add_route('/poll',        app.poll)
    app.add_route('/notes',       app.notes)

    httpd = make_server(params.host, int(params.port), app)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


class Daemon:
    def __init__(self, params):
        logfile = params.logfile if params.daemon else None
        self.stdin = '/dev/null'
        self.stdout = logfile
        self.stderr = logfile
        self.params = params
        self.children = []

    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write('fork #1 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)

        os.chdir('/')
        os.setsid()
        os.umask(0)

        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write('fork #2 failed: %d (%s)\n' % (e.errno, e.strerror))
            sys.exit(1)

        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        atexit.register(self.delpid)
        pid = str(os.getpid())
        file(self.params.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.params.pidfile)

    def start(self):
        try:
            pf = file(self.params.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = 'pidfile %s already exist. Daemon already running?\n'
            sys.stderr.write(message % self.params.pidfile)
            sys.exit(1)

        self.daemonize()
        self.run()

    def stop(self):
        try:
            pf = file(self.params.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = 'pidfile %s does not exist. Daemon not running?\n'
            sys.stderr.write(message % self.params.pidfile)
            return

        try:
            while 1:
                os.kill(pid, SIGTERM)
                sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.params.pidfile):
                    os.remove(self.params.pidfile)
            else:
                print(str(err))
                sys.exit(1)

    def restart(self):
        self.stop()
        self.start()

    def run(self):
        http_server_worker(self.params)


def start(params):
    daemon = Daemon(params)
    daemon.start()


def restart(params):
    daemon = Daemon(params)
    daemon.restart()


def stop(params):
    daemon = Daemon(params)
    daemon.stop()


def run(params):
    daemon = Daemon(params)
    daemon.run()





daemon_params = argparse.ArgumentParser(add_help=False)
daemon_params.add_argument('-p', '--pidfile', default='/tmp/kiosk_server.pid', help='Pid for daemon')
daemon_params.add_argument('-l', '--logfile', default='/tmp/kiosk_server.log', help='Logfile')

run_params = argparse.ArgumentParser(add_help=False)
run_params.add_argument('-v', '--verbose', action='count',        help='-vv: very verbose')
run_params.add_argument('-P', '--port',    default=8080,          help='Port to serve (default 8080)')
run_params.add_argument('-H', '--host',    default='127.0.0.1',   help='Host to serve (default 127.0.0.1; 0.0.0.0 to make public)')
run_params.add_argument('-D', '--device',  default='/dev/nv10',help='Cash in device (default /dev/nv10)')

parser = argparse.ArgumentParser(description='Kiosk http server. Help: %(prog)s start -h')
p = parser.add_subparsers()
sp_start =   p.add_parser('start',   parents=[run_params, daemon_params], help='Starts %(prog)s daemon')
sp_stop =    p.add_parser('stop',    parents=[daemon_params], help='Stops %(prog)s daemon')
sp_restart = p.add_parser('restart', parents=[daemon_params], help='Restarts %(prog)s daemon')
sp_run =     p.add_parser('run',     parents=[run_params],    help='Run in foreground')

sp_start.set_defaults(   func=start,   daemon=True)
sp_stop.set_defaults(    func=stop,    daemon=True)
sp_restart.set_defaults( func=restart, daemon=True)
sp_run.set_defaults(     func=run,     daemon=False) # <<<

args = parser.parse_args()
args.func(args)
