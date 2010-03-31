import VideoCapture
import Image
import pyglet
import math
import itertools


class Coord:
    def __init__(self, x, y):
        self.x = x
        self.y = y
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
        self.sqrlen = pow(self.length, 2)

class Triangle:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c
        self.ab = Line(a, b)
        self.bc = Line(b, c)
        self.ca = Line(c, a)
        self.alpha = math.degrees(math.acos((self.bc.sqrlen + self.ca.sqrlen - self.ab.sqrlen) / (2.0 * self.bc.length * self.ca.length)))
        self.beta = math.degrees(math.acos((self.ab.sqrlen + self.ca.sqrlen - self.bc.sqrlen) / (2.0 * self.ab.length * self.ca.length)))
        self.gamma = math.degrees(math.acos((self.ab.sqrlen + self.bc.sqrlen - self.ca.sqrlen) / (2.0 * self.ab.length * self.bc.length)))

a = Coord(0, 0)
b = Coord(0, 3)
c = Coord(4, 0)
t = Triangle(a, b, c)
print t.alpha, t.beta, t.gamma


class Cam(VideoCapture.Device):
    def getPygImage(self):
        img = self.getImage()
        w, h = img.size
        m = img.mode
        d = img.tostring()
        return pyglet.image.ImageData(w, h, m, d, (-1 * w * len(m)))

cam = Cam() #VideoCapture.Device()
campic = cam.getImage()
camSize = campic.size
camMode = campic.mode


class Quad:
    def __init__(self):
        wf = camSize[0] / 3
        hf = camSize[1] / 3
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
        self.matrix = []

        nw = self.coords[0:2]
        sw = self.coords[2:4]
        se = self.coords[4:6]
        ne = self.coords[6:8]
        x0, y0 = nw
        As = 1.0 / projection.width
        At = 1.0 / projection.height
        coefs = (x0, (ne[0]-x0)*As, (sw[0]-x0)*At,
                (se[0]-sw[0]-ne[0]+x0)*As*At,
                y0, (ne[1]-y0)*As, (sw[1]-y0)*At,
                (se[1]-sw[1]-ne[1]+y0)*As*At)

        d = min(self.coords[1], self.coords[3], self.coords[5], self.coords[7])
        l = min(self.coords[0], self.coords[2], self.coords[4], self.coords[6])
        u = max(self.coords[1], self.coords[3], self.coords[5], self.coords[7])
        r = max(self.coords[0], self.coords[2], self.coords[4], self.coords[6])

        for row in range(d, u + 1):
            for col in range(l, r + 1):
                x = int(round((coefs[0] * col + coefs[1] * row + coefs[2]) / (coefs[6] * col + coefs[7] * row + 1)))
                y = int(round((coefs[3] * col + coefs[4] * row + coefs[5]) / (coefs[6] * col + coefs[7] * row + 1)))
                if x > 0 and x < projection.width and y > 0 and y < projection.height:
                    self.matrix.append((row, col, x, y))

quad = Quad()


screens = pyglet.window.get_platform().get_default_display().get_screens()

class Projection:
    def __init__(self):
        self.screen = screens[-1]
        self.width = self.screen.width
        self.height = self.screen.height
        self.img = pyglet.image.ImageData(self.width, self.height, 'RGB', (chr(255) + chr(0) + chr(0)) * self.width * self.height)
        self.win = pyglet.window.Window(fullscreen = False, screen = self.screen)

    def draw(self):
        self.win.switch_to()
        self.img.blit(0, 0)

projection = Projection()


guiwindow = pyglet.window.Window(camSize[0], camSize[1])

@guiwindow.event
def on_close():
    pyglet.app.exit()

@guiwindow.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.ESCAPE:
        pyglet.app.exit()
    if symbol == pyglet.window.key.RETURN:
        quad.calculate()
        print quad.matrix[:10]
        camimg = cam.getImage()
        campix = camimg.tostring()
        projimg = projection.img
        projpix = [0 for i in range(projimg.width * projimg.height * 3)]
        for point in quad.matrix:
            cami = ((point[0] + point[1] * camimg.size[0]) * 3)
            proji = ((point[1] + point[2] * projimg.width) * 3)
            try:
                for i in range(3):
                    projpix[proji + i] = 255 #ord(campix[cami + i])
            except IndexError:
                pass
        c = ''
        for i in projpix:
            c += chr(i)
        projection.img.set_data('RGB', projimg.width * 3, c)

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
