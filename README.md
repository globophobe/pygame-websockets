# Pygame Autobahn Integration Demo

Demo integration of Pygame 1.9.1 and Autobahn 0.10.2 for WebSockets. Targets Python 2.7, for Twisted integration, and to support building an EXE with Pyinstaller.

## The Gist

Unfortunately, there isn't much information on the Internet about how to do this. The Twisted FAQ suggests [Game](https://launchpad.net/game), which doesn't look simple. As well, The accepted answer for the top Google result, at [Stack Overflow](http://stackoverflow.com/questions/8381850/combining-pygame-and-twisted), suggests danger in starving the Twisted reactor.

It is correct, that we must avoid blocking calls. But, programming callbacks with Twisted deferreds is not so difficult. In fact, integrating Pygame and Twisted is really simple.

Usually, the Pygame event loop is just a **while** loop:

    import pygame


    class App(object):
        def __init__(self):
            self._run = True
            pygame.display.init()
            pygame.display.set_mode((600, 480), pygame.RESIZABLE)

        def main(self):
            while self._run:  # Pygame event loop.
                self.process_events()
                # Do pygame stuff.

        def process_events(self):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._run = False

    if __name__ == '__main__':
        app = App()
        app.main()


To integrate with Twisted, we add a *yield* statement to the **while** loop, and coiterate with twisted.internet.task.Cooperator:

    import pygame
    from twisted.internet import reactor
    from twisted.internet.task import Cooperator


    class App(object):
        def __init__(self):
            self._run = True
            pygame.display.init()
            pygame.display.set_mode((600, 480), pygame.RESIZABLE)

        def main(self):
            while self._run:
                self.process_events()
                # Do pygame stuff.
                yield  # For the Twisted reactor

        def process_events(self):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._run = False
                    reactor.stop()  # Stop the Twisted reactor.

    if __name__ == '__main__':
        app = App()
        # twisted.internet.task.LoopingCall is also possible.
        coop = Cooperator()
        coop.coiterate(app.main())
        reactor.run()  # Start the Twisted reactor.


Look at client.py for the full integration of Pygame and Autobahn. The server.py is copied from [WebSocket (Echo Twisted-based)](https://github.com/tavendo/AutobahnPython/tree/master/examples/twisted/websocket/echo). The Pygame client.py was derived from [Using wxPython with Autobahn](https://github.com/tavendo/AutobahnPython/tree/master/examples/twisted/websocket/wxpython).

MIT License
