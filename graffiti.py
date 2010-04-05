# CONSTANTS - modify this part only #

threshold1 = [.8, .8, .8]
color1a = (255, 0, 0)
color1b = (0, 255, 0)
color1c = (0, 0, 255)

threshold2 = (0, 255, 0)
color2a = (255, 0, 0)
color2b = (0, 255, 0)
color2c = (0, 0, 255)

threshold3 = (0, 0, 255)
color3a = (255, 0, 0)
color3b = (0, 255, 0)
color3c = (0, 0, 255)


# CONSTANTS END - do not modify further down #


import sys
import math
import time
import Image
import pyglet
import ImageChops
import VideoCapture
from pywidget import slider

def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step


class Cam(VideoCapture.Device):
    def __init__(self):
        VideoCapture.Device.__init__(self)
        img = self.getImage()
        self.size = img.size
        self.width, self.height = self.size
        self.mode = img.mode
        self.pitch = -1 * self.width * len(self.mode)

    def getPygImage(self, th = False):
        img = self.getImage()
        w = self.width
        h = self.height
        if False == th:
            m = self.mode
            d = img.tostring()
            p = self.pitch
        else:
            th = [255.0 * x for x in th]
            r, g, b = img.split()
            r = Image.eval(r, lambda i: 255 if i < th[0] else 0)
            g = Image.eval(g, lambda i: 255 if i < th[1] else 0)
            b = Image.eval(b, lambda i: 255 if i < th[2] else 0)
            m = img.mode
            i = Image.merge(m, (r, g, b))
            d = i.tostring()
            p = -1 * w * len(m)
        return pyglet.image.ImageData(w, h, m, d, p)

cam = Cam()


class Projection:
    def __init__(self):
        screens = pyglet.window.get_platform().get_default_display().get_screens()
        self.screen = screens[-1]
        self.width = self.screen.width
        self.height = self.screen.height
        self.mode = cam.mode
        self.pitch = -1 * self.width * len(self.mode)
        self.img = pyglet.image.ImageData(self.width, self.height, self.mode, (0) * self.mode * self.width * self.height)
        t = pyglet.gl.Config(double_buffer = False)
        if len(screens) > 1:
            self.win = pyglet.window.Window(fullscreen = True, screen = self.screen, config = t)
        else:
            self.win = pyglet.window.Window(self.width, self.height, config = t)

    def wipescreen(self, r = 0, g = 0, b = 0):
        self.win.switch_to()
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                ('v2i', (0, 0, 0, self.height, self.width, self.height, self.width, 0)),
                ('c4b', (r, g, b, 127) * 4))

    def draw(self, x = False, y = False, size = 40, sides = 16):
        if False != x and False != y:
            coords = []
            for i in range(sides):
                coords.append(int(round(x + size * math.cos(i * 2 * math.pi / sides))))
                coords.append(int(round(y + size * math.sin(i * 2 * math.pi / sides))))
            self.win.switch_to()

            pyglet.graphics.draw(len(coords) / 2, pyglet.gl.GL_TRIANGLE_FAN,
                ('v2i', coords),
                ('c4b', (0, 0, 0, 127) * 16))

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
        gui.switch_to()
        coords = [i for c in self.coords for i in c.flat()]
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                ('v2i', coords),
                ('c4b', (127, 0, 0, 127) * 4))

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

    def getpoint(self):
        if False == self.matrix:
            return False
        img = cam.getPygImage().get_data(cam.mode, cam.pitch)
        detectedxs = []
        detectedys = []
        for point in self.matrix:
            cami = -3 * ((point[1] * cam.width) - point[0])
            try:
                if ord(img[cami]) > 255.0 * threshold1[0]:
                    if ord(img[cami + 1]) > 255.0 * threshold1[1]:
                        if ord(img[cami + 2]) > 255.0 * threshold1[2]:
                            detectedxs.append(point[2])
                            detectedys.append(point[3])
            except IndexError:
                pass
            if len(detectedxs) > 0 and len(detectedys) > 0:
                x = int(round((sum(detectedxs) / len(detectedxs))))
                y = int(round((sum(detectedys) + len(detectedys))))
                return Coord(x, y)
        return False

quad = Quad()


class Colslider(slider.Slider):
    def __init__(self, parent, idx):
        self.idx = idx
        slider.Slider.__init__(self, x = 0, y = cam.height * 2 + 10 + idx * 30, width = cam.width, value = threshold1[idx])
        parent.push_handlers(self)

        @self.event
        def on_value_change(slider):
            threshold1[slider.idx] = slider.value
            parent.clear()
            parent.draw()

class Sliders():
    def __init__(self, parent):
        self.red = Colslider(parent, 0)
        self.grn = Colslider(parent, 1)
        self.blu = Colslider(parent, 2)

class Gui(pyglet.window.Window):
    def __init__(self):
        self.img = cam.getPygImage()
        self.mask = cam.getPygImage(threshold1)
        self.sliders = Sliders(self)
        pyglet.window.Window.__init__(self, width = cam.width, height = cam.height * 2 + 100)

    def on_close(self):
        pyglet.app.exit()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()

        if symbol == pyglet.window.key.RETURN:
            quad.calculate()

        if symbol == pyglet.window.key.SPACE:
            projection.wipescreen(r = 127, g = 127, b = 127)
            quad.matrix = False

    def on_mouse_press(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.LEFT:
            if y < cam.height:
                quad.moveCorner(x, y)
                return pyglet.event.EVENT_HANDLED
            else:
                return pyglet.event.EVENT_UNHANDLED

    def draw(self):
        self.img = cam.getPygImage()
        self.mask = cam.getPygImage(threshold1)
        gui.switch_to()
        self.img.blit(0, 0)
        self.mask.blit(0, cam.height)

gui = Gui()


def update(dt):
    if gui.has_exit or projection.win.has_exit:
        pyglet.app.exit()
        return

    gui.draw()

    if False == quad.matrix:
        quad.draw()
    else:
        p = quad.getpoint()
        if False != p:
            projection.draw(p.x, p.y)

pyglet.clock.schedule_interval(update, 0.05)
pyglet.app.run()
