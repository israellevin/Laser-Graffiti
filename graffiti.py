import Image
import pyglet

guiwindow = pyglet.window.Window()
#guiwindow.push_handlers(pyglet.window.event.WindowEventLogger())

@guiwindow.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.ESCAPE:
        pyglet.app.exit()

@guiwindow.event
def on_mouse_press(x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
        print x, y


screens = pyglet.window.get_platform().get_default_display().get_screens()
vidwindow = pyglet.window.Window(fullscreen = True, screen = screens[-1])

@vidwindow.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.ESCAPE:
        pyglet.app.exit()
    if symbol == pyglet.window.key.A:
        pilimg = Image.open('tmp.png')
        w, h = pilimg.size
        m = pilimg.mode
        d = pilimg.tostring()
        i = pyglet.image.ImageData(w, h, m, d, (-1 * w * len(m)))
        vidwindow.switch_to()
        i.blit(0, 0)


pyglet.app.run()
