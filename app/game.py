from math import sqrt
import os

import pygame as pg

from app.window import GameWindow, Color, Font
from app.trig import tan, origin_rotate
from app.cube import Cube

class Game(GameWindow):
    ASSET_DIR = 'app/asset'
    FPS = 30
    BG_COL = Color.L_Gray
    WINDOW_SIZE = (800, 500)

    def __init__(self):
        self.cube = Cube()
        self.init_window()
        self.init_camera()
        self.init_mouse()
        self.init_gui()

    def init_window(self):
        super().__init__(self.WINDOW_SIZE)
        self.set_window_title('Rubik\'s Cube 3D')

    def init_camera(self):
        self.set_fov(70)
        self.pitch = 30 # 0-360: (0 = level)
        self.yaw = 45 # 0-360: (0 = down +z axis)
        self.pos = [-10, -8, -10] # X, Y, Z

    def set_fov(self, fov_val):
        self.projection_dist = (self.width / 2) / tan(fov_val / 2)

    def init_mouse(self):
        self.mouse_pos = (0, 0)

        # Load mouse
        pg.mouse.set_visible(False)
        self.pointer_img = self.load_img('mouse/pointer.png')
        size = self.pointer_img.get_size()
        scale = 1 / 6
        self.pointer_img = pg.transform.scale(self.pointer_img, [int(x * scale) for x in size])

    def init_gui(self):
        self.gui_width = 200
        self.gui_bg_col = (29, 132, 235)
        self.gui_title_col = (20, 100, 179)
        self.gui_font = Font(self.screen, 'app/asset/font/SFNS.ttf', size=25)

        # --- Create control buttons ---
        btns = len(self.cube.moves.keys())
        self.gui_row_height = self.height / (btns + 1)

        padding = 10 # Space between buttons
        btn_height = (self.height - self.gui_row_height - padding * (btns + 1)) / btns # Height of each button
        curr_height = self.gui_row_height

        # Colour of left and right buttons
        left_col = (240, ) * 3
        right_col = (220, ) * 3

        # Button dimensions
        size = (
            self.gui_width / 2 - padding,
            btn_height
        )

        self.buttons = []
        for val in self.cube.moves.keys():
            curr_height += padding

            p1 = (
                padding,
                curr_height
            )
            p2 = (
                self.gui_width / 2,
                curr_height
            )
            self.buttons.append(Button(val, p1, size, left_col))
            self.buttons.append(Button(val + '\'', p2, size, right_col))

            curr_height += btn_height

    def load_img(self, fname):
        """Load an image from the asset directory"""
        return pg.image.load(os.path.join(self.ASSET_DIR, fname))

    def frame(self):
        self.update()
        self.render()

    def update(self):
        self.handle_events()
        self.cube.update()

    def handle_events(self):
        self.mouse_pos = pg.mouse.get_pos()

        for evt in self.events:
            if evt.type == pg.MOUSEBUTTONDOWN:
                for btn in self.buttons:
                    if self.coord_in_extended_rect(self.mouse_pos, btn.coord, btn.size):
                        self.cube.move_queue.append(btn.label)

    def render(self):
        self.draw_cube()
        self.draw_gui()
        self.draw_mouse()

    def calc_coord(self, point):
        # Transform so camera at origin
        point = [val - self.pos[i] for i, val in enumerate(point)]

        # Rotate so camera is facing down +z axis
        point[0], point[2] = origin_rotate(point[0], point[2], -self.yaw)
        point[1], point[2] = origin_rotate(point[1], point[2], -self.pitch)

        # Ensure point is visible
        assert point[2] > 0, 'Vertex is located behind camera view!'
        
        # Scale factor to project point onto projection plane
        scale = self.projection_dist / point[2]

        # Resulting screen coodinate
        res = [point[0] * scale, point[1] * scale]

        # Transform so that (0, 0) is centre of screen
        res[0] += self.width / 2
        res[1] += self.height / 2

        return res

    def draw_cube(self):
        def dist_from_camera(tri):
            """Distance from centre of triangle to camera position"""

            # Transform so camera at origin
            tri = [[(point[i] - self.pos[i]) for i in range(3)] for point in tri]
            # Get centre (average coordinate) - skip middle coordinate
            centre = [(tri[0][i] + tri[1][i]) / 2 for i in range(3)]
            # Calculate distance
            dist = sqrt(centre[0] ** 2 + centre[1] ** 2 + centre[2] ** 2)

            return dist

        render_tris = []

        # Get all tris to be rendered
        for plane in self.cube.blocks:
            for row in plane:
                for block in row:
                    for axis in block.tris:
                        for side in axis:
                            for tri in side:
                                render_tris.append(tri)

        # Sort according to depth
        render_tris.sort(key=lambda tri: dist_from_camera(tri.coords), reverse=True)

        # Render all tris
        for tri in render_tris:
            points = [self.calc_coord(point) for point in tri.coords]
            for point in points:
                point[0] += self.gui_width // 2
            # self.pen.draw_polygon(points, width=1) # Draw triangle - debugging only
            self.pen.draw_polygon(points, col=tri.col.rgb_vals())

    def draw_gui(self):
        # Background
        self.pen.draw_rect((0, 0), (self.gui_width, self.height), col=self.gui_bg_col)

        # Title
        self.pen.draw_rect((0, 0), (self.gui_width, self.gui_row_height), col=self.gui_title_col)
        self.gui_font.render('Rubik\'s Cube 3D', self.gui_width // 2, self.gui_row_height // 2, x_anchor='center', y_anchor='center', col=Color.White)

        # Buttons
        for btn in self.buttons:
            col = btn.default_col
            if self.coord_in_extended_rect(self.mouse_pos, btn.coord, btn.size):
                col = (200, ) * 3
                if pg.mouse.get_pressed()[0]:
                    col = (180, ) * 3

            self.pen.draw_rect(btn.coord, btn.size, col=col)
            mid_x = btn.coord[0] + btn.size[0] / 2
            mid_y = btn.coord[1] + btn.size[1] / 2
            self.gui_font.render(btn.label, mid_x, mid_y, x_anchor='center', y_anchor='center')

    def coord_in_extended_rect(self, coord, rect_from, size):
        """Check if coordinate is within an extended rectangle"""
        if coord[0] < rect_from[0]:
            return False
        if coord[1] < rect_from[1]:
            return False
        if coord[0] > rect_from[0] + size[0]:
            return False
        if coord[1] > rect_from[1] + size[1]:
            return False
        return True

    def draw_mouse(self):
        if pg.mouse.get_focused():
            self.screen.blit(self.pointer_img, self.mouse_pos)

class Button:
    def __init__(self, label, coord, size, default_col):
        self.label = label
        self.coord = coord
        self.size = size
        self.default_col = default_col
