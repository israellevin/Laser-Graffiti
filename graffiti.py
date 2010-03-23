# CONSTANTS - modify this part only #

threshold1 = (255, 0, 0)
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


from VideoCapture import Device
import pygame
import Image
import ImageChops
import ImageDraw
from time import sleep


pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
info = pygame.display.Info()
screenWidth = info.current_w
screenHeight = info.current_h
screenSize = (screenWidth, screenHeight)
screenMode = 'RGB'

cam = Device()
campic = cam.getImage()
camSize = campic.size
camMode = campic.mode


def showpic(pic):
    if pic.mode != screenMode:
        pic = pic.convert(screenMode)
    if pic.size != screenSize:
        pic = pic.resize(screenSize)

    pilpic = pygame.image.fromstring(pic.tostring(), screenSize, screenMode)
    screen.blit(pilpic, (0,0))
    pygame.display.flip()


def showvid():
    while True:
        pygame.event.pump()
        keyinput = pygame.key.get_pressed()
        if keyinput[pygame.K_ESCAPE] or pygame.event.peek(pygame.QUIT):
            return

        showpic(cam.getImage())


class Rect:
    def __init__(self, bg, color, realSize):
        self.left = 0
        self.up = 0
        self.right = screenWidth
        self.down = screenHeight
        self.bg = bg.resize(screenSize)
        self.color = color
        self.realSize = realSize
        self.crop = (0, 0, realSize[0], realSize[1])
        self.set()

    def draw(self):
        pic = self.bg.copy()
        pic.paste(self.color, (self.left, self.up, self.right, self.down))
        showpic(pic)

    def getCrop(self):
        l = int(round(1.0 * self.left / screenWidth * self.realSize[0], 0))
        u = int(round(1.0 * self.up / screenHeight * self.realSize[1], 0))
        r = int(round(1.0 * self.right / screenWidth * self.realSize[0], 0))
        d = int(round(1.0 * self.down / screenHeight * self.realSize[1], 0))
        return (l, u, r, d)

    def set(self):
        while True:
            pygame.event.pump()
            keyinput = pygame.key.get_pressed()
            shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
            ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL

            if keyinput[pygame.K_ESCAPE] or pygame.event.peek(pygame.QUIT):
                self.crop = self.getCrop()
                return

            factor = 15 if ctrl else 1
            if shift:
                if keyinput[pygame.K_LEFT] and self.right > self.left: self.right -= factor
                if keyinput[pygame.K_UP] and self.down > self.up: self.down -= factor
                if keyinput[pygame.K_RIGHT]:
                    if self.right < screenWidth: self.right += factor
                    elif self.left > 0: self.left -= factor
                if keyinput[pygame.K_DOWN]:
                    if self.down < screenHeight: self.down += factor
                    elif self.up > 0: self.up -= factor
            else:
                if keyinput[pygame.K_LEFT] and self.left > 0:
                        self.right -= factor
                        self.left -= factor
                if keyinput[pygame.K_UP] and self.up > 0:
                        self.down -= factor
                        self.up -= factor
                if keyinput[pygame.K_RIGHT] and self.right < screenWidth:
                        self.left += factor
                        self.right += factor
                if keyinput[pygame.K_DOWN] and self.down < screenHeight:
                        self.up += factor
                        self.down += factor

            self.draw()


class Quad:
    def __init__(self, bg, color, realSize):
        self.coords = [0, 0, 0, screenHeight, screenWidth, screenHeight, screenWidth, 0]
        self.data = (0, 0, 0, realSize[1], realSize[0], realSize[1], realSize[0], 0)
        self.active = 0
        self.bg = bg.resize(screenSize)
        self.color = color
        self.realSize = realSize

        self.set()

    def draw(self):
        pic = self.bg.copy()
        draw = ImageDraw.Draw(pic)
        self.color = (0, 255, 255)
        draw.polygon(self.coords, fill = self.color)
        x = self.coords[self.active]
        y = self.coords[self.active + 1]
        draw.rectangle((x - 5, y - 5, x + 5, y + 5), fill = (55, 0, 0))
        showpic(pic)

    def getData(self):
        x0 = int(round(1.0 * self.coords[0] / screenWidth * self.realSize[0], 0))
        y0 = int(round(1.0 * self.coords[1] / screenHeight * self.realSize[1], 0))
        x1 = int(round(1.0 * self.coords[2] / screenWidth * self.realSize[0], 0))
        y1 = int(round(1.0 * self.coords[3] / screenHeight * self.realSize[1], 0))
        x2 = int(round(1.0 * self.coords[4] / screenWidth * self.realSize[0], 0))
        y2 = int(round(1.0 * self.coords[5] / screenHeight * self.realSize[1], 0))
        x3 = int(round(1.0 * self.coords[6] / screenWidth * self.realSize[0], 0))
        y3 = int(round(1.0 * self.coords[7] / screenHeight * self.realSize[1], 0))
        return (x0, y0, x1, y1, x2, y2, x3, y3)

    def set(self):
        while True:
            pygame.event.pump()
            keyinput = pygame.key.get_pressed()
            shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
            ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL

            if keyinput[pygame.K_ESCAPE] or pygame.event.peek(pygame.QUIT):
                self.data = self.getData()
                return

            if keyinput[pygame.K_RETURN]:
                self.active = (self.active + 2) % 8
                sleep(0.2)

            factor = 25 if ctrl else 1
            if keyinput[pygame.K_LEFT]:
                    self.coords[self.active] -= factor
            if keyinput[pygame.K_UP]:
                    self.coords[self.active + 1] -= factor
            if keyinput[pygame.K_RIGHT]:
                    self.coords[self.active] += factor
            if keyinput[pygame.K_DOWN]:
                    self.coords[self.active + 1] += factor

            self.draw()


def calibrate():
    showvid()
    sleep(0.5)
    projRect = Rect(Image.new(screenMode, screenSize), (255, 0, 0), screenSize)
    sleep(0.5)
    camRect = Quad(cam.getImage(), (0, 255, 0), camSize)
    sleep(0.5)
    return (projRect, camRect)


def makemask(r, g, b, th):
    redmask = Image.eval(r, lambda i: 255 if i < th[0] else 0)
    grnmask = Image.eval(g, lambda i: 255 if i < th[1] else 0)
    blumask = Image.eval(b, lambda i: 255 if i < th[2] else 0)
    mask = ImageChops.lighter(redmask, grnmask)
    mask = ImageChops.lighter(mask, blumask)
    return mask


projRect, camRect = calibrate()
curpic = cam.getImage()
color1 = Image.new(screenMode, curpic.size, color1a)
color2 = Image.new(screenMode, curpic.size, color2a)
color3 = Image.new(screenMode, curpic.size, color3a)
composite = Image.new(screenMode, curpic.size)
while True:
    curpic = cam.getImage()
    r, g, b = curpic.split()

    composite = Image.composite(composite, color1, makemask(r, g, b, threshold1))
    composite = Image.composite(composite, color2, makemask(r, g, b, threshold2))
    composite = Image.composite(composite, color3, makemask(r, g, b, threshold3))

    showpic(composite.transform(screenSize, Image.QUAD, camRect.data))

    pygame.event.pump()
    keyinput = pygame.key.get_pressed()
    if keyinput[pygame.K_ESCAPE] or pygame.event.peek(pygame.QUIT):
        raise SystemExit
    if keyinput[pygame.K_RETURN]:
        projRect, camRect = calibrate()
    if keyinput[pygame.K_SPACE]:
        composite = Image.new(screenMode, curpic.size)
    if keyinput[pygame.K_q]:
        color1 = Image.new(screenMode, curpic.size, color1a)
    if keyinput[pygame.K_w]:
        color1 = Image.new(screenMode, curpic.size, color1b)
    if keyinput[pygame.K_e]:
        color1 = Image.new(screenMode, curpic.size, color1c)
    if keyinput[pygame.K_a]:
        color2 = Image.new(screenMode, curpic.size, color2a)
    if keyinput[pygame.K_s]:
        color2 = Image.new(screenMode, curpic.size, color2b)
    if keyinput[pygame.K_d]:
        color2 = Image.new(screenMode, curpic.size, color2c)
    if keyinput[pygame.K_z]:
        color3 = Image.new(screenMode, curpic.size, color3a)
    if keyinput[pygame.K_x]:
        color3 = Image.new(screenMode, curpic.size, color3b)
    if keyinput[pygame.K_c]:
        color3 = Image.new(screenMode, curpic.size, color3c)


graffiti()


#    pas = []
#    pix = curpic.load()
#    for x in range(camSize[0]):
#        for y in range(camSize[1]):
#            if pix[x, y][0] > threshold[0] and pix[x, y][1] > threshold[1] and pix[x, y][2] > threshold[2]:
#                pas.append((x, y))
#    if len(pas) > threshold[3]:
#        tot = [0, 0]
#        for i in pas:
#            tot[0] += i[0]
#            tot[1] += i[1]
#        x = tot[0] / len(pas)
#        y = tot[1] / len(pas)
#        draw = ImageDraw.Draw(composite)
#        draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill = color3)
#        x = self.coords[self.active]
#        y = self.coords[self.active + 1]
#        draw.rectangle((x - 5, y - 5, x + 5, y + 5), fill = (55, 0, 0))
#        showpic(curpic)

