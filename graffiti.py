# CONSTANTS - modify this part only #

COLORS = ((0, 0, 0, 127),
          (0, 0, 127, 127),
          (0, 127, 0, 127),
          (0, 127, 127, 127),
          (127, 0, 0, 127),
          (127, 0, 127, 127),
          (127, 127, 0, 127),
          (127, 127, 127, 127))

THRESHOLDS = ([.8, 0, 0],)
#              [1, 1, 1],
#              [1, 1, 1])

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

    def draw(self, x = False, y = False, size = 40, sides = 16, rgb = (0, 0, 0)):
        if False != x and False != y:
            coords = []
            for i in range(sides):
                coords.append(int(round(x + size * math.cos(i * 2 * math.pi / sides))))
                coords.append(int(round(y + size * math.sin(i * 2 * math.pi / sides))))
            self.win.switch_to()
            pyglet.graphics.draw(len(coords) / 2, pyglet.gl.GL_TRIANGLE_FAN,
                ('v2i', coords),
                ('c4b', (rgb[0], rgb[1], rgb[2], 127) * 16))

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
        coords = [i for c in self.coords for i in c.flat()]
        gui.switch_to()
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

    def getpoint(self, threshold):
        if False == self.matrix:
            return False
        img = cam.getPygImage().get_data(cam.mode, cam.pitch)
        detectedxs = []
        detectedys = []
        for point in self.matrix:
            cami = -3 * ((point[1] * cam.width) - point[0])
            try:
                if ord(img[cami]) > 255.0 * threshold[0]:
                    if ord(img[cami + 1]) > 255.0 * threshold[1]:
                        if ord(img[cami + 2]) > 255.0 * threshold[2]:
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
        slider.Slider.__init__(self,
                x = (len(parent.parent.colorctls) + 1) * cam.width,
                y = cam.height + (idx * 30) + 40,
                width = cam.width, value = parent.threshold[idx])
        parent.parent.push_handlers(self)

        @self.event
        def on_value_change(slider):
            parent.threshold[slider.idx] = slider.value
            parent.parent.clear()
            parent.parent.draw()

class Colorctl():
    def __init__(self, threshold, color, parent):
        self.threshold = threshold[:]
        self.color = color
        self.parent = parent
        self.img = cam.getPygImage(self.threshold)
        self.x = cam.width * (1 + len(parent.colorctls))
        self.red = Colslider(self, 0)
        self.grn = Colslider(self, 1)
        self.blu = Colslider(self, 2)
    def draw(self):
        self.img = cam.getPygImage(self.threshold)
        colors = [b for c in COLORS for i in range(4) for b in c]
        coords = []
        for i in range(8):
            x1 = self.x + (i * (cam.width / 8))
            x2 = x1 + (cam.width / 8)
            y1 = cam.height
            y2 = y1 + 30
            coords += [x1, y1, x1, y2, x2, y2, x2, y1]
        gui.switch_to()
        pyglet.graphics.draw(len(coords) / 2, pyglet.gl.GL_QUADS,
                ('v2i', coords),
                ('c4b', colors))
        self.img.blit(self.x, 0)

    def project(self):
        p = quad.getpoint(self.threshold)
        if False != p:
            projection.draw(p.x, p.y, rgb = COLORS[self.color])

class Gui(pyglet.window.Window):
    def __init__(self):
        self.img = cam.getPygImage()
        self.colorctls = []
        for th in THRESHOLDS:
            self.colorctls.append(Colorctl(th, 0, self))
        pyglet.window.Window.__init__(self,
                width = cam.width * (1 + len(self.colorctls)),
                height = cam.height + 130)

    def on_close(self):
        pyglet.app.exit()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            pyglet.app.exit()

    def on_mouse(self, x, y, button, modifiers):
        if button == pyglet.window.mouse.RIGHT:
            if False == quad.matrix:
                quad.calculate()
                gui.wipescreen()
                projection.wipescreen()
            else:
                quad.matrix = False
                projection.wipescreen(127, 127, 127)
            return pyglet.event.EVENT_HANDLED
        if button == pyglet.window.mouse.LEFT:
            if x > 0 and y > 0 and y < cam.height and x < cam.width:
                quad.moveCorner(x, y)
                return pyglet.event.EVENT_HANDLED
            elif x > cam.width and y > cam.height and y - cam.height < 30:
                ctli = (x / cam.width) - 1
                coli = x % cam.width / (cam.width / 8)
                self.colorctls[ctli].color = coli
            else:
                return pyglet.event.EVENT_UNHANDLED

    def on_mouse_press(self, x, y, button, modifiers):
        self.on_mouse(x, y, button, modifiers)

    def on_mouse_drag(self, x, y, dx, dy, button, modifiers):
        self.on_mouse(x, y, button, modifiers)

    def wipescreen(self, r = 0, g = 0, b = 0):
        self.switch_to()
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                ('v2i', (0, 0, 0, cam.height, self.width, cam.height, self.width, 0)),
                ('c4b', (r, g, b, 127) * 4))

    def draw(self):
        self.img = cam.getPygImage()
        gui.switch_to()
        self.img.blit(0, 0)
        quad.draw()
        for colorctl in self.colorctls:
            colorctl.draw()

    def project(self):
        for colorctl in self.colorctls:
            colorctl.project()

gui = Gui()


def update(dt):
    if gui.has_exit or projection.win.has_exit:
        pyglet.app.exit()
        return

    if False == quad.matrix:
        gui.draw()
    else:
        gui.draw()
        gui.project()

    #gui.switch_to()
    #gui.img.blit(0, 0)
    #fps_display.draw()

fps_display = pyglet.clock.ClockDisplay()
fps_display.label.color = (127, 127, 0, 2)
pyglet.clock.schedule(update)
pyglet.app.run()
