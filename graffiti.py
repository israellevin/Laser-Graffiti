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
        self.coordinates = [wf, hf, wf, hf*2, wf*2, hf*2, wf*2, hf]
        self.matrix = False

    def moveCorner(self, x, y):
        minp = 9999
        closest = 0
        for i in range(4):
            p = distance(self.coordinates[i*2], self.coordinates[i*2+1], x, y)
            if p < minp:
                minp = p
                closest = i
        self.coordinates[closest*2:closest*2+2] = [x, y]

    def draw(self):
        guiwindow.switch_to()
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS, ('v2i', self.coordinates))

    def calculate(self):
        d = min(self.coordinates[1], self.coordinates[3], self.coordinates[5], self.coordinates[7])
        l = min(self.coordinates[0], self.coordinates[2], self.coordinates[4], self.coordinates[6])
        u = max(self.coordinates[1], self.coordinates[3], self.coordinates[5], self.coordinates[7])
        r = max(self.coordinates[0], self.coordinates[2], self.coordinates[4], self.coordinates[6])

        for row in range(d, u + 1):
            for col in range(l, r + 1):

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
