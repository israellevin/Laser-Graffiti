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

            factor = 25 if ctrl else 1
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
        self.ul = (0, 0)
        self.dl = (0, screenHeight)
        self.dr = (screenWidth, screenHeight)
        self.ru = (screenWidth, 0)
        self.bg = bg.resize(screenSize)
        self.color = color
        self.realSize = realSize
        self.data = (0, 0, 0, realSize[1], realSize[0], realSize[1], realSize[0], 0)

        self.set()

    def draw(self):
        pic = self.bg.copy()
        draw = ImageDraw.Draw(pic)
        draw.line(self.data, 128)
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

            factor = 25 if ctrl else 1
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

showvid()
sleep(0.5)
projRect = Rect(Image.new(screenMode, screenSize), (255, 0, 0), screenSize)
sleep(0.5)
camRect = Rect(cam.getImage(), (0, 255, 0), camSize)
sleep(0.5)


curpic = cam.getImage().crop(camRect.crop)
redcolor = Image.new('RGB', curpic.size, (255, 0, 0))
grncolor = Image.new('RGB', curpic.size, (0, 255, 0))
blucolor = Image.new('RGB', curpic.size, (0, 0, 255))
composite = Image.new('RGB', curpic.size)


def graffiti():
    while True:
        curpic = cam.getImage().crop(camRect.crop)
        r, g, b = curpic.split()
        redmask = Image.eval(r, lambda i: 255 if i < 255 else 0)
        grnmask = Image.eval(g, lambda i: 255 if i < 255 else 0)
        blumask = Image.eval(b, lambda i: 255 if i < 255 else 0)

        global composite
        composite = Image.composite(composite, redcolor, redmask)
        composite = Image.composite(composite, grncolor, grnmask)
        composite = Image.composite(composite, blucolor, blumask)

        showpic(composite)

        pygame.event.pump()
        keyinput = pygame.key.get_pressed()
        if keyinput[pygame.K_ESCAPE] or pygame.event.peek(pygame.QUIT):
            raise SystemExit
        if keyinput[pygame.K_0]:
            composite = Image.new('RGB', curpic.size)


graffiti()
