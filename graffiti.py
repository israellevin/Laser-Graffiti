import Image
import pyglet

screens = pyglet.window.get_platform().get_default_display().get_screens()
window = pyglet.window.Window(fullscreen = True, screen = screen)
#window.push_handlers(pyglet.window.event.WindowEventLogger())
#label = pyglet.text.Label('Yo')

@window.event
def on_draw():
    pass
    #window.clear()

@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.ESCAPE:
        pyglet.app.exit()
    if symbol == pyglet.window.key.A:
        pilimg = Image.open('tmp.png')
        w, h = pilimg.size
        m = pilimg.mode
        d = pilimg.tostring()
        i = pyglet.image.ImageData(w, h, m, d, (-1 * w * len(m)))
        i.blit(0, 0)

@window.event
def on_mouse_press(x, y, button, modifiers):
    if button == pyglet.window.mouse.LEFT:
        print x, y

pyglet.app.run()
