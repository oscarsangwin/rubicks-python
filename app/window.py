"""Base class for the PyGame window, pen rendering and font management"""

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame as pg

class Color:
    """Predefined RGB color codes"""

    Black  = (000, 000, 000)
    White  = (255, 255, 255)
    Red    = (255, 000, 000)
    Lime   = (000, 255, 000)
    Blue   = (000, 000, 255)
    Yellow = (255, 255, 000)
    Silver = (192, 192, 192)
    Gray   = (128, 128, 128)
    L_Gray = (220, 220, 220)
    D_Gray = ( 50,  50,  50)
    Maroon = (128, 000, 000)
    Olive  = (128, 128, 000)
    Green  = (000, 128, 000)
    Purple = (128, 000, 128)
    Teal   = (000, 128, 128)
    Navy   = (000, 000, 128)
    Orange = (255, 165, 000)

class GameWindow:
    """Template PyGame window class"""

    BG_COL = Color.White
    FPS = 60

    def __init__(self, geometry):
        pg.init()
        self._geometry = geometry
        self.screen = pg.display.set_mode(geometry)
        self.pen = _Pen(self.screen)
        self.events = []
        self._running = True

    def set_window_title(self, title):
        pg.display.set_caption(title)

    @property
    def width(self):
        return self._geometry[0]

    @property
    def height(self):
        return self._geometry[1]

    def run(self):
        clock = pg.time.Clock()

        while self._running:

            # Check for window quit
            self.events = pg.event.get()
            for event in self.events:
                if event.type == pg.QUIT:
                    self._running = False

            self.screen.fill(self.BG_COL)
            self.frame()
            pg.display.update()

            clock.tick(self.FPS)

    def frame(self):
        raise NotImplementedError('The frame method must be overridden')

    def quit(self):
        self._running = False

class _Pen:
    """Wrapper functions for drawing to a PyGame surface - class not accessable to main program"""

    def __init__(self, screen: pg.Surface):
        self.screen = screen

    def draw_line(self, start, end, col=Color.Black, width=1):
        pg.draw.line(self.screen, col, start, end, width=width)

    def draw_polygon(self, points, col=Color.Black, width=0):
        pg.draw.polygon(self.screen, col, points, width)

    def draw_circle(self, center, radius, col=Color.Black, width=0):
        pg.draw.circle(self.screen, col, center, radius, width)

    def draw_rect(self, start, dimensions, col=Color.Black, width=0):
        rect = tuple(start) + tuple(dimensions)
        pg.draw.rect(self.screen, col, rect, width=width)

class Font:
    """Class for rendering fonts"""

    def __init__(self, screen, font_dir, size=23):
        self.screen = screen
        self.font = pg.font.Font(font_dir, size)

    def render(self, text, x, y, col=(0, 0, 0), x_anchor='left', y_anchor='top'):
        """
        Render the font on the screen

        Anchors:
        X: ('left', 'center', 'right')
        Y: ('top', 'center', 'bottom')
        """

        if not text: # No text to render
            return

        textsurface = self.font.render(text, True, col)
        width, height = textsurface.get_rect()[2:4]

        # (x, y) parameters are automatically anchored at top left - adjust if necessary:

        if x_anchor == 'center':
            x -= int(width / 2)
        elif x_anchor == 'right':
            x -= width

        if y_anchor == 'center':
            y -= int(height / 2)
        elif y_anchor == 'bottom':
            y -= height

        self.screen.blit(textsurface, (x, y))
