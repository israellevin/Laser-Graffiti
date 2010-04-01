import sys
import math
import Image
import pyglet

campic = pyglet.image.load('tmp.png')

def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step

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

sw = Coord(250, 0)
se = Coord(500, 0)
ne = Coord(500, 50)
nw = Coord(250, 100)

s = Line(sw, se)
w = Line(sw, nw)
n = Line(nw, ne)
e = Line(se, ne)

projw = Line(Coord(0, 0), Coord(0, campic.height))
proje = Line(Coord(campic.width, 0), Coord(campic.width, campic.height))

xsteps = int(max(s.length, n.length) + 1)
ysteps = int(max(w.length, e.length) + 1)

matrix = []
for row in frange(0, 1, 1.0 / ysteps):
    camrow = Line(w.point(row), e.point(row))
    projrow = Line(projw.point(row), proje.point(row))
    for col in frange(0, 1, 1.0 / xsteps):
        cp = camrow.point(col)
        pp = projrow.point(col)
        matrix.append((cp.x, cp.y, pp.x, pp.y))

guiwindow = pyglet.window.Window(campic.width, campic.height)

@guiwindow.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.ESCAPE:
        pyglet.app.exit()
    elif symbol == pyglet.window.key.RETURN:
        campic.blit(0, 0)
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, ('v2i', sw.xy + nw.xy + ne.xy + se.xy))
    elif symbol == pyglet.window.key.SPACE:
        campic1 = pyglet.image.load('tmp.png')
        campix = campic1.get_data('RGB', -3 * campic.width)
        projimg = pyglet.image.ImageData(campic.width, campic.height, 'RGB', chr(0) * 3 * campic.width * campic.height, pitch = -3 * campic.width)
        projpix = [0 for i in range(3 * projimg.width * projimg.height)]
        for point in matrix:
            cami = -3 * ((point[1] * campic.width) - point[0])
            proji = -3 * ((point[3] * campic.width) - point[2])
            try:
                for i in range(3):
                    projpix[proji + i] = campix[cami + i]
            except IndexError:
                pass
        c = ''
        for i in projpix:
            c += chr(i)
        projimg.set_data('RGB', -3 * projimg.width, c)
        projimg.blit(0, 0)

pyglet.app.run()
