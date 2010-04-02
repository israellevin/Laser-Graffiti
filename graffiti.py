import sys
#import VideoCapture
import math
import Image
import pyglet

def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step


#class Cam(VideoCapture.Device):
class Cam():
    def __init__(self):
        #VideoCapture.Device.__init__(self)
        img = self.getImage()
        self.width, self.height = img.size
        self.mode = img.mode
        self.pitch = -1 * self.width * len(self.mode)

    def getPygImage(self):
        img = self.getImage()
        w = self.width
        h = self.height
        m = self.mode
        d = img.tostring()
        p = self.pitch
        return pyglet.image.ImageData(w, h, m, d, p)
    
    def getImage(self):
        return Image.open('tmp.png')

cam = Cam()


screens = pyglet.window.get_platform().get_default_display().get_screens()

class Projection:
    def __init__(self):
        self.screen = screens[-1]
        self.width = self.screen.width
        self.height = self.screen.height
        self.mode = cam.mode
        self.pitch = -1 * self.width * len(self.mode)
        self.img = pyglet.image.ImageData(self.width, self.height, 'RGB', (chr(255) + chr(0) + chr(0)) * self.width * self.height)
        #self.win = pyglet.window.Window(fullscreen = (False if len(screens) < 2 else True), screen = self.screen)
        self.win = pyglet.window.Window(self.width, self.height)

    def draw(self):
        self.win.switch_to()
        self.img.blit(0, 0)

projection = Projection()


class Coord:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.xy = (x, y)

    def flat(self):
        yield self.x
        yield self.y

    def distance(self, *params):
        if len(params) == 1:
            x = params[0].x
            y = params[0].y
        elif len(params) == 2:
            x = params[0]
            y = params[1]
        else:
            raise Exception
        return math.sqrt(pow(abs(self.x - x), 2) + pow(abs(self.y - y), 2))

class Line:
    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.length = a.distance(b)
        self.xdif = b.x - a.x
        self.ydif = b.y - a.y

    def point(self, fact):
        x = int(round(self.a.x + (self.xdif * fact)))
        y = int(round(self.a.y + (self.ydif * fact)))
        return Coord(x, y)

class Quad:
    def __init__(self):
        wf = cam.width / 3
        hf = cam.height / 3
        self.coords = [Coord(wf, hf), Coord(wf, hf*2), Coord(wf*2, hf*2), Coord(wf*2, hf)]
        self.matrix = False

    def moveCorner(self, x, y):
        minp = 9999
        closest = 0
        for i in range(4):
            p = self.coords[i].distance(x, y)
            if p < minp:
                minp = p
                closest = i
        self.coords[closest].x, self.coords[closest].y = x, y

    def draw(self):
        guiwindow.switch_to()
        coords = [i for c in self.coords for i in c.flat()]
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, ('v2i', coords))

    def calculate(self):
        s = Line(self.coords[0], self.coords[3])
        w = Line(self.coords[0], self.coords[1])
        n = Line(self.coords[1], self.coords[2])
        e = Line(self.coords[3], self.coords[2])

        projw = Line(Coord(0, 0), Coord(0, projection.height))
        proje = Line(Coord(projection.width, 0), Coord(projection.width, projection.height))

        xsteps = int(max(s.length, n.length) + 1)
        ysteps = int(max(w.length, e.length) + 1)

        self.matrix = []
        for row in frange(0, 1, 1.0 / ysteps):
            camrow = Line(w.point(row), e.point(row))
            projrow = Line(projw.point(row), proje.point(row))
            for col in frange(0, 1, 1.0 / xsteps):
                cp = camrow.point(col)
                pp = projrow.point(col)
                self.matrix.append((cp.x, cp.y, pp.x, pp.y))

quad = Quad()


guiwindow = pyglet.window.Window(cam.width, cam.height)

@guiwindow.event
def on_close():
    pyglet.app.exit()

@guiwindow.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.ESCAPE:
        pyglet.app.exit()

    if symbol == pyglet.window.key.RETURN:
        quad.calculate()
        curpic = cam.getPygImage()
        campix = curpic.get_data(cam.mode, cam.pitch)
        projection.img = pyglet.image.ImageData(projection.width, projection.height, projection.mode, chr(0) * len(projection.mode) * projection.width * projection.height, pitch = projection.pitch)
        projpix = [0 for i in range(len(projection.mode) * projection.width * projection.height)]
        for point in quad.matrix:
            cami = -3 * ((point[1] * cam.width) - point[0])
            proji = -3 * ((point[3] * projection.width) - point[2])
            try:
                for i in range(3):
                    projpix[proji + i] = ord(campix[cami + i])
            except IndexError:
                pass
        c = ''
        for i in projpix:
            c += chr(i)
        projection.img.set_data(projection.mode, projection.pitch, c)


@guiwindow.event
def on_mouse_press(x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
        quad.moveCorner(x, y)


def update(dt):
    if guiwindow.has_exit:
        return
    img = cam.getPygImage()
    guiwindow.switch_to()
    img.blit(0, 0)
    quad.draw()

    if projection.win.has_exit:
        return
    projection.draw()

pyglet.clock.schedule_interval(update, 0.05)
pyglet.app.run()
