# (c) Copyright 2015, Synapse Wireless, Inc.
"""Application Server for IronMan demo
   A web server based on Tornado, integrated with SNAP Connect.
"""

import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket

import snapconnect
from snapconnect import snap
from apy import ioloop_scheduler

import asyncore
import os
import logging

log = logging.getLogger(__file__)

# SNAP Connect settings
#serial_conn = snap.SERIAL_TYPE_SNAPSTICK100
serial_conn = snap.SERIAL_TYPE_SNAPSTICK200
#serial_conn = snap.SERIAL_TYPE_RS232
serial_port = 0
#serial_port = 'COM3'
snap_addr = '\xff\xb6\x06'


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    ''' Send and receive websocket messages between server and browser(s).
        Messages TO the browser are encoded "rpc-like" as
            {'kind' : 'funcName', 'args' : params}
        Messages FROM the browser are translated to RPC calls and invoked on
        our SNAP Connect instance.
    '''
    waiters = set()    # Browser connections

    def allow_draft76(self):
        '''Allow older browser websocket versions'''
        return True
    
    def open(self):
        WebSocketHandler.waiters.add(self)

    def on_close(self):
        WebSocketHandler.waiters.remove(self)

    @classmethod
    def send_updates(cls, message):
        #log.info("sending message to %d waiters", len(cls.waiters))
        for waiter in cls.waiters:
            try:
                waiter.write_message(message)
            except:
                log.error("Error sending message", exc_info=True)

    def on_message(self, message):
        '''Translate browser message into RPC function call (into local SnapCom object)'''
        #log.info("got message %r", message)
        parsed = tornado.escape.json_decode(message)
        try:
            func = getattr(snapCom, parsed['funcname'])
        except AttributeError:
            log.exception('Browser called unknown function: %s' % str(parsed))
        else:
            try:
                args = [str(a) if isinstance(a,unicode) else a for a in parsed['args']]
                func(*args)
            except:
                log.exception('Error calling function: %s' % str(parsed))


class SnapCom(object):
    """Snap Connect communication layer"""
    SNAPCONNECT_POLL_INTERVAL = 5 # ms

    def __init__(self):
        self.snapRpcFuncs = {'dist' : self.dist,
                             'send_ws' : self.send_ws
                            }
        
        cur_dir = os.path.dirname(__file__)

        # Create SNAP Connect instance. Note: we are using TornadoWeb's scheduler.
        self.snapconnect = snap.Snap(license_file = os.path.join(cur_dir, 'SrvLicense.dat'),
                                     addr = snap_addr,
                                     scheduler=ioloop_scheduler.IOLoopScheduler.instance(),
                                     funcs = self.snapRpcFuncs
                                    )

        # Connect to local SNAP wireless network
        self.snapconnect.open_serial(serial_conn, serial_port)
   
        #self.snapconnect.accept_tcp()
        
        self.snapconnect.set_hook(snap.hooks.HOOK_SNAPCOM_OPENED, self.on_connected)
        self.snapconnect.set_hook(snap.hooks.HOOK_SNAPCOM_CLOSED, self.on_disconnected)
        
        # Tell the Tornado scheduler to call SNAP Connect's internal poll function.
        tornado.ioloop.PeriodicCallback(asyncore.poll, self.SNAPCONNECT_POLL_INTERVAL).start()
        tornado.ioloop.PeriodicCallback(self.snapconnect.poll_internals, self.SNAPCONNECT_POLL_INTERVAL).start()
 
    def send_ws(self, func, *args):
        '''SNAPpy call-in to invoke websocket functions'''
        message = {'funcname' : func, 'args' : args}
        WebSocketHandler.send_updates(message)
    
    def dist(self, index, val):
        """Distance report call-in from SNAPpy"""
        self.send_ws('report_dist', index, val)
        
    def snap_method(self, func, *args):
        '''Browser call-in to directly invoke snapconnect methods'''
        func = getattr(self.snapconnect, func, None)
        if callable(func):
            func(*args)

    def do_log(self, *args):
        log.info(*args)

    def on_connected(self, addr_pair, remote_snap_addr):
        self.connected = True
        log.debug("on_connected(%s)" % str(addr_pair))
        
    def on_disconnected(self, addr_pair, remote_snap_addr):
        """Called by SNAP Connect when a SNAP TCP connection has been disconnected or failed to connect"""
        self.connected = False
        log.debug("on_disconnected(%s)" % str(addr_pair))

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", tornado.web.RedirectHandler, {"url": "/index.html"}),
            (r"/wshub", WebSocketHandler),
            (r"/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__), "www")}),
        ]
        settings = dict(
            cookie_secret="43oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            static_path=os.path.join(os.path.dirname(__file__), "www"),
            xsrf_cookies=True,
            autoescape=None,
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        
def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)-15s %(levelname)-8s %(name)-8s %(message)s')
    log.info("***** Begin Console Log *****")

    app = Application()
    app.listen(80)
    
    snapCom = SnapCom()
    
    tornado.ioloop.IOLoop.instance().start()
    

if __name__ == '__main__':
    main()

