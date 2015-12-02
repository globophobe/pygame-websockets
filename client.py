###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Alex Newby
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################
import sys
import datetime
import pygame
from twisted.internet import reactor
from twisted.python import log
from twisted.internet.task import Cooperator
from autobahn.twisted.websocket import (
    WebSocketClientProtocol, WebSocketClientFactory
)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


class MyClientProtocol(WebSocketClientProtocol):
    def onOpen(self):
        log.msg('WebSocket connection open.')
        # The WebSocket connection is open. we store ourselves on the
        # factory object, so that we can access this protocol instance
        # from pygame, e.g. to use sendMessage() for sending WS msgs.
        self.factory._protocol = self

    def onMessage(self, payload, isBinary):
        # A WebSocket message was received. Now interpret it, possibly
        # accessing the pygame app `self.factory._app`
        if isBinary:
            msg = 'Binary message received: {0} bytes'.format(len(payload))
        else:
            msg = 'Text message received: {0}'.format(payload.decode('utf8'))
        self.factory._app.msgs.append(msg)
        log.msg(msg)

    def onClose(self, wasClean, code, reason):
        log.msg('WebSocket connection closed: {0}'.format(reason))
        # The WebSocket connection is gone. clear the reference to ourselves
        # on the factory object. when accessing this protocol instance from
        # pygame, always check if the ref is None. only use it when it's
        # not None (which means, we are actually connected).
        self.factory._protocol = None
        self.factory._app._run = False


class MyClientFactory(WebSocketClientFactory):
    protocol = MyClientProtocol

    def __init__(self, url, app):
        WebSocketClientFactory.__init__(self, url)
        self._app = app
        self._protocol = None


class App(object):
    def __init__(self):
        self._run = True
        self._timestamp = datetime.datetime.now()
        self.msgs = []
        self.init_display()
        self.init_font()
        self.open_websocket()

    def init_display(self):
        pygame.display.init()
        self._display_surface = pygame.display.set_mode(
            (600, 480), pygame.RESIZABLE
        )

    def init_font(self):
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 48)

    def open_websocket(self):
        self._factory = MyClientFactory('ws://localhost:9000', self)
        reactor.connectTCP('127.0.0.1', 9000, self._factory)

    @property
    def websocket(self):
        if self._factory:
            return self._factory._protocol

    def close_websocket(self):
        if self.websocket:
            self.websocket.sendClose(1000)

    def main(self):
        while self._run or self.websocket:
            self.process_events()
            self.send_msgs()
            # Do pygame stuff.
            self.display_total_msgs()
            yield
        # Stop the Twisted reactor.
        reactor.stop()

    def send_msgs(self):
        if self.websocket:
            # Rather than sleep the main loop for 1 second, as the original
            # echo client does, let's check 1 second has elapsed.
            timestamp = datetime.datetime.now()
            timedelta = timestamp - self._timestamp
            if timedelta.total_seconds() >= 1:
                self.websocket.sendMessage(u'Hello, world!'.encode('utf8'))
                self.websocket.sendMessage(b'\x00\x01\x03\x04', isBinary=True)
                self._timestamp = timestamp

    def display_total_msgs(self):
        total_msgs = len(self.msgs)
        msg = 'WebSocket messages received: {}'.format(unicode(total_msgs))
        msg = self.font.render(msg, True, BLACK)
        w, h = self._display_surface.get_size()
        w = w - msg.get_width()
        h = h - msg.get_height()
        self._display_surface.fill(WHITE)
        self._display_surface.blit(msg, (int(w / 2.0), int(h / 2)))
        pygame.display.flip()

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close_websocket()


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    app = App()
    # twisted.internet.task.LoopingCall is also possible
    coop = Cooperator()
    coop.coiterate(app.main())
    reactor.run()  # Start the Twisted reactor.
