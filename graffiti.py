import VideoCapture
import Image
import pyglet
import math


def pil2pyg(pilimg):
        w, h = pilimg.size
        m = pilimg.mode
        d = pilimg.tostring()
        return pyglet.image.ImageData(w, h, m, d, (-1 * w * len(m)))

def distance(ax, ay, bx, by):
    return math.sqrt(pow(abs(ax - bx), 2) + pow(abs(ay - by), 2))


cam = VideoCapture.Device()
campic = cam.getImage()
camSize = campic.size
camMode = campic.mode


class Quad:
    def __init__(self):
        wf = camSize[0] / 3
        hf = camSize[1] / 3
        self.coords = [wf, hf, wf, hf*2, wf*2, hf*2, wf*2, hf]
        self.matrix = False

    def moveCorner(self, x, y):
        minp = 9999
        closest = 0
        for i in range(4):
            p = distance(self.coords[i*2], self.coords[i*2+1], x, y)
            if p < minp:
                minp = p
                closest = i
        self.coords[closest*2:closest*2+2] = [x, y]

    def draw(self):
        guiwindow.switch_to()
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, ('v2i', self.coords))

    def calculate(self):
        matrix = []

        nw = self.coords[0:2]
        sw = self.coords[2:4]
        se = self.coords[4:6]
        ne = self.coords[6:8]
        x0, y0 = nw
        As = 1.0 / w
        At = 1.0 / h
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
                x = (coefs[0] * col + coefs[1] * row + coefs[2]) / (coefs[6] * col + coefs[7] * row + 1)
                y = (coefs[3] * col + coefs[4] * row + coefs[5]) / (coefs[6] * col + coefs[7] * row + 1)
                matrix.append((row, col, x, y))

quad = Quad()


screens = pyglet.window.get_platform().get_default_display().get_screens()

class Projection:
    def __init__(self):
        self.screen = screens[-1]
        self.width = self.screen.width
        self.height = self.screen.height
        self.pilimg = Image.new(camMode, (self.width, self.height), (255, 0, 0))
        self.win = pyglet.window.Window(fullscreen = True, screen = self.screen)

    def draw(self):
        self.win.switch_to()
        pil2pyg(self.pilimg).blit(0, 0)

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

@guiwindow.event
def on_mouse_press(x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
        quad.moveCorner(x, y)


def update(dt):
    i = cam.getImage()
    i = pil2pyg(i)
    guiwindow.switch_to()
    i.blit(0, 0)
    quad.draw()
    projection.draw()

pyglet.clock.schedule_interval(update, 0.05)
pyglet.app.run()
