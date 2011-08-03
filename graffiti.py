#!/usr/bin/python

import re
import sys
import math
import Image
import pyglet
import ImageChops
import VideoCapture
from time import time
from pywidget import slider

class Ini():
    def __init__(self, fname):
        self.fname = fname
        self.camnum = 0
        self.savedir = 'saved'
        self.colors = [(0, 0, 0),
                      (127, 0, 0),
                      (0, 127, 0),
                      (0, 0, 127),
                      (127, 63, 0),
                      (127, 80, 0),
                      (31, 63, 127),
                      (127, 127, 127)]
        self.thresholds = ([.8], [.8], [.8])
        try:
            f = open(self.fname, 'r')
            s = f.read()
            f.close()
            p = re.search('(?<=camnum:).*', s)
            if(p): self.camnum = int(p.group(0).strip())
            p = re.search('(?<=savedir:).*', s)
            if(p): self.savedir = p.group(0).strip()
            colors = re.findall('(?<=color:).*', s)
            for cidx, color in enumerate(colors):
                if cidx > 7:
                    print 'Too many colors in ini file'
                    break
                r, g, b = color.split(',')
                self.colors[cidx] = (int(r), int(g), int(b))
            thresholds = re.findall('(?<=threshold:).*', s)
            if len(thresholds) > 0:
                self.thresholds = []
                for threshold in thresholds:
                    self.thresholds.append(float(threshold))
        except IOError:
            print('No ini file found')
    def write(self):
        s = "camnum:%i\nsavedir:%s\n" % (self.camnum, self.savedir)
        for color in self.colors:
            s+= "color:%i,%i,%i\n" % color
        ths = [ctl.threshold for ctl in gui.colorctls] if None != gui else self.thresholds
        for threshold in ths:
            s+= "threshold:%f\n" % (threshold)
        try:
            f = open(self.fname, 'w')
            f.write(s)
            f.close()
        except IOError:
            print('Unable to write file ' + self.fname)

ini = Ini('local.ini')
COLORS = []
for color in ini.colors:
    COLORS.append(color + (127,))
BRUSHSIZE = 5


def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step


class Cam(VideoCapture.Device):
    def __init__(self, camnum = 0):
        VideoCapture.Device.__init__(self, ini.camnum)
        img = self.getImage()
        self.size = img.size
        self.width, self.height = self.size
        self.mode = img.mode
        self.pitch = -1 * self.width * len(self.mode)

    def getPygImage(self, th = False, color = 0):
        img = self.getImage()
        w = self.width
        h = self.height
        if False == th:
            m = self.mode
            d = img.tostring()
            p = self.pitch
        else:
            th = 255.0 * th
            r, g, b = img.split()
            if 0 == color:
                r = Image.eval(r, lambda i: 255 if i < th else 0)
                g = Image.eval(g, lambda i: 255 if i > th else 0)
                b = Image.eval(b, lambda i: 255 if i > th else 0)
            elif 1 == color:
                r = Image.eval(r, lambda i: 255 if i > th else 0)
                g = Image.eval(g, lambda i: 255 if i < th else 0)
                b = Image.eval(b, lambda i: 255 if i > th else 0)
            else:
                r = Image.eval(r, lambda i: 255 if i > th else 0)
                g = Image.eval(g, lambda i: 255 if i > th else 0)
                b = Image.eval(b, lambda i: 255 if i < th else 0)

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
        self.brushsize = BRUSHSIZE
        t = pyglet.gl.Config(double_buffer = False)
        if len(screens) > 1:
            self.win = pyglet.window.Window(fullscreen = True, screen = self.screen, config = t)
        else:
            self.win = pyglet.window.Window(self.width, self.height, config = t)

    def save(self, name):
        self.win.switch_to()
        self.img.save(name)

    def wipescreen(self, r = 0, g = 0, b = 0):
        self.win.switch_to()
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                ('v2i', (0, 0, 0, self.height, self.width, self.height, self.width, 0)),
                ('c4b', (r, g, b, 127) * 4))

    def draw(self, colctl, x = False, y = False, sides = 16):
        if False != x and False != y:
            coords = []
            for i in range(sides):
                coords.append(int(round(x + self.brushsize * math.cos(i * 2 * math.pi / sides))))
                coords.append(int(round(y + self.brushsize * math.sin(i * 2 * math.pi / sides))))
            self.win.switch_to()
            rgb = COLORS[colctl.color]
            pyglet.graphics.draw(len(coords) / 2, pyglet.gl.GL_TRIANGLE_FAN,
                ('v2i', coords),
                ('c4b', (rgb[0], rgb[1], rgb[2], 127) * 16))
            if time() - colctl.lastdot[0] < .25:
                x1 = colctl.lastdot[1]
                y1 = colctl.lastdot[2]
                if x != x1 or y != y1:
                    angle = 1 if x == x1 else math.atan(1.0 * (y - y1) / (x - x1))
                    angle += .5 * math.pi
                    a1x = int(round(x + self.brushsize * math.cos(angle)))
                    a1y = int(round(y + self.brushsize * math.sin(angle)))
                    angle += math.pi
                    a2x = int(round(x + self.brushsize * math.cos(angle)))
                    a2y = int(round(y + self.brushsize * math.sin(angle)))
                    angle += math.pi
                    b1x = int(round(x1 + self.brushsize * math.cos(angle)))
                    b1y = int(round(y1 + self.brushsize * math.sin(angle)))
                    angle += math.pi
                    b2x = int(round(x1 + self.brushsize * math.cos(angle)))
                    b2y = int(round(y1 + self.brushsize * math.sin(angle)))
                    pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                    ('v2i', (a1x, a1y, a2x, a2y, b2x, b2y, b1x, b1y)),
                    ('c4b', (rgb[0], rgb[1], rgb[2], 127) * 4))

            colctl.lastdot = (time(), x, y)

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
                if ord(img[cami]) > 255.0 * threshold:
                    if ord(img[cami + 1]) > 255.0 * threshold:
                        if ord(img[cami + 2]) > 255.0 * threshold:
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
        self.parent = parent
        self.idx = idx
        slider.Slider.__init__(self,
                x = (len(parent.parent.colorctls) + 1) * cam.width,
                y = cam.height + (idx * 30) + 40,
                width = cam.width, value = parent.threshold)
        self.parent.parent.push_handlers(self)

        @self.event
        def on_value_change(slider):
            self.parent.threshold = slider.value

class Colorctl():
    def __init__(self, idx, threshold, color, parent):
        self.idx = idx
        self.threshold = threshold
        self.color = color
        self.parent = parent
        self.img = cam.getPygImage(self.threshold, self.idx)
        self.x = cam.width * (1 + len(parent.colorctls))
        self.sld = Colslider(self, 0)
        self.lastdot = (0, 0, 0)
    def draw(self):
        self.img = cam.getPygImage(self.threshold, self.idx)
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                ('v2i', (
                    self.x, cam.height,
                    self.x, cam.height + 70,
                    self.x + cam.width, cam.height + 70,
                    self.x + cam.width, cam.height)),
                ('c4b', (0, 0, 0, 127) * 4))
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
        self.sld.draw()

    def project(self):
        p = quad.getpoint(self.threshold)
        if False != p:
            projection.draw(self, p.x, p.y)

class Gui(pyglet.window.Window):
    def __init__(self):
        self.img = cam.getPygImage()
        self.colorctls = []
        for idx, th in enumerate(ini.thresholds):
            self.colorctls.append(Colorctl(idx, th, 0, self))
        pyglet.window.Window.__init__(self,
                width = cam.width * (1 + len(self.colorctls)),
                height = cam.height + 70)

    def on_draw(self):
        pyglet.graphics.draw(8, pyglet.gl.GL_QUADS,
                ('v2i', (0, self.height, cam.width, self.height, cam.width, self.height - 35, 0, self.height - 35,
                         0, self.height - 35, cam.width, self.height - 35, cam.width, cam.height, 0, cam.height)),
                ('c4b', (0, 50, 0, 127) * 4 + (50, 0, 0, 127) * 4))
        self.btncap = pyglet.text.Label('+', font_size = 24, color = (200, 255, 200, 255))
        self.btnlod = pyglet.text.Label('-', font_size = 36, color = (255, 200, 200, 255))
        self.btncap.x = cam.width / 2 - 10
        self.btnlod.x = cam.width / 2 - 5
        self.btncap.y = cam.height + 40
        self.btnlod.y = cam.height + 4
        self.btncap.draw()
        self.btnlod.draw()

    def on_close(self):
        ini.write()
        pyglet.app.exit()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            ini.write()
            pyglet.app.exit()
        elif symbol == pyglet.window.key.SPACE:
            #projection.win.switch_to()
            #b = pyglet.image.get_buffer_manager().get_color_buffer()
            #b.save("%s/%i.png" % (ini.savedir, time()))
            #projection.img.texture.save("screencap.%i.jpg" % (time()))
            #i = projection.img.create_texture(pyglet.image.Texture)
            #i.save('stam')
            #Image.fromstring(i.format
            projection.save("screencap.%i.jpg" % (time()))
            projection.wipescreen()
        elif symbol == pyglet.window.key.MINUS:
            if len(self.colorctls) > 1:
                self.colorctls.pop()
                self.set_size(cam.width * (1 + len(self.colorctls)),
                              height = cam.height + 70)
        elif symbol == pyglet.window.key.EQUAL:
            if len(self.colorctls) < 3:
                self.colorctls.append(Colorctl(len(self.colorctls), 0.8, 0, self))
                self.set_size(cam.width * (1 + len(self.colorctls)),
                              height = cam.height + 70)
        elif symbol == pyglet.window.key._0:
            if projection.brushsize >= 5:
                projection.brushsize += 5
            elif projection.brushsize >= 1:
                projection.brushsize += 1
        elif symbol == pyglet.window.key._9:
            if projection.brushsize > 5:
                projection.brushsize -= 5
            elif projection.brushsize > 1:
                projection.brushsize -= 1
        elif symbol >= pyglet.window.key._1 and symbol <= pyglet.window.key._8:
            self.colorctls[0].color = symbol - 49

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
            if x > 0 and y > 0:
                if x < cam.width and y < cam.height:
                    quad.moveCorner(x, y)
                    return pyglet.event.EVENT_HANDLED
                elif y > cam.height and y - cam.height < 30:
                    ctli = (x / cam.width) - 1
                    coli = x % cam.width / (cam.width / 8)
                    self.colorctls[ctli].color = coli
                    return pyglet.event.EVENT_HANDLED
                else:
                    return pyglet.event.EVENT_UNHANDLED

    def on_mouse_press(self, x, y, button, modifiers):
        if x < cam.width and y > cam.height:
            if y > cam.height + 35:
                if len(self.colorctls) < 3:
                    self.colorctls.append(Colorctl(len(self.colorctls), 0.8, 0, self))
                    self.set_size(cam.width * (1 + len(self.colorctls)),
                                  height = cam.height + 70)
            else:
                if len(self.colorctls) > 1:
                    self.colorctls.pop()
                    self.set_size(cam.width * (1 + len(self.colorctls)),
                                  height = cam.height + 70)
            return pyglet.event.EVENT_HANDLED
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
        ini.write()
        pyglet.app.exit()
        return

    if False == quad.matrix:
        projection.wipescreen(127, 127, 127)
        gui.draw()
    else:
        gui.project()

    #gui.switch_to()
    #gui.img.blit(0, 0)
    #fps_display.draw()

#fps_display = pyglet.clock.ClockDisplay()
#fps_display.label.color = (127, 127, 0, 2)
pyglet.clock.schedule(update)
pyglet.app.run()
