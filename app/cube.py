from copy import deepcopy
import random
from app.trig import origin_rotate

class RbxCol:
    COLS = {
        'WHITE'  : (255, 255, 255),
        'RED'    : (255,   0,   0),
        'BLUE'   : (  0,   0, 255),
        'YELLOW' : (255, 255,   0),
        'GREEN'  : (  0, 128,   0),
        'ORANGE' : (255, 165,   0),
        'BLACK'  : ( 50,  50,  50)
    }

    def __init__(self, name=None):
        if name is None:
            self._name = 'BLACK'
        else:
            self._name = name.upper()
            assert self._name in self.COLS.keys(), 'Invalid color name'

    def rgb_vals(self):
        return self.COLS[self._name]

    @property
    def name(self):
        return self._name

    def __eq__(self, other):
        if isinstance(other, RbxCol):
            return self._name == other._name
        elif isinstance(other, str):
            return self._name == other.upper()
        else:
            raise ValueError('Other must be RbxCol or string')
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f'<RbxCol(\'{self._name}\' RGB={self.rgb_vals()})>'

    def __str__(self):
        return f'<COL/{self._name}>'

class Tri:
    def __init__(self, coords, col):
        self.coords = coords
        self.col = col

    def __repr__(self):
        return f'<Tri coords={self.coords} col={self.col}>'

class Block:
    """Defines a single block within the cube"""

    # Block color rules
    # X=0, Y=1, Z=2
    # (2, 2) Means when cube z == 2, face with z = 2 should be orange
    SIDE_COLS = {
        (0, 0): RbxCol('Green'), # -ve x: green face
        (0, 2): RbxCol('Blue'), # +ve x: blue face
        (1, 0): RbxCol('White'), # -ve y: white face
        (1, 2): RbxCol('Yellow'), # +ve y: yellow face
        (2, 0): RbxCol('Red'), # -ve z: red face
        (2, 2): RbxCol('Orange'), # +ve z: yellow face
    }

    CUBE_SIZE = 2 # Size of cube
    CUBE_PADD = 0.15 # Padding between cubes
    CUBE_OFFSET = -1.5 * (CUBE_SIZE) - CUBE_PADD

    @staticmethod
    def gen_template_block():
        tris = [[[] for _ in range(2)] for _ in range(3)]
        for axis in range(3): # X/Y/Z
            for side in range(2): # -ve/+ve
                p1 = [side] * 3 # First vertex
                p2 = ([side ^ 1] * 3) # Second vertex
                p2[axis] ^= 1
                
                for flip_i in range(3):
                    if flip_i == axis:
                        continue

                    p3 = p1.copy() # Third vertex
                    p3[flip_i] ^= 1

                    # Copy first and second
                    p1_copy = p1.copy()
                    p2_copy = p2.copy()

                    gen_tri = Tri([p1_copy, p2_copy, p3], None)
                    tris[axis][side].append(gen_tri)
        return tris
    
    TEMPLAETE_BLOCK_TRIS = gen_template_block()

    def __init__(self, pos):
        self.pos = pos

        # Block face colors
        # Index 0: Axis (x, y, z), Index 1: -ve/+ve side of axis
        self.cols = [[RbxCol() for _ in range(2)] for _ in range(3)]
        self.new_cols = None

        # Apply color rules to block faces depending on cube position
        for (axis, val), col in self.SIDE_COLS.items():
            if self.pos[axis] == val:
                self.cols[axis][val//2] = col
        
        # Generate block tris (each pair of triangles corresponds to a face color)
        # Index 0: Axis (x, y, z), Index 1: -ve/+ve side of axis (contains both tris)
        self.tris = deepcopy(self.TEMPLAETE_BLOCK_TRIS)
        for axis_i in range(3):
            for side_i in range(2):
                for pair_i in range(2):
                    tri = self.tris[axis_i][side_i][pair_i] # Select tri
                    # Update value of each coordinate (scale and translate block)
                    for vtx in tri.coords:
                        for i in range(3):
                            vtx[i] = ((self.CUBE_SIZE + self.CUBE_PADD) * self.pos[i]) + (vtx[i] * self.CUBE_SIZE) + self.CUBE_OFFSET
        
        # Set tri cols
        self.update_tri_cols()
        
        # Create reusable copy of tris
        self.tris_original = deepcopy(self.tris)

    def update_tri_cols(self):
        for axis_i in range(3):
            for side_i in range(2):
                for pair_i in range(2):
                    tri = self.tris[axis_i][side_i][pair_i] # Select tri
                    tri.col = self.cols[axis_i][side_i] # Set color

    def __repr__(self):
        return f'<Block pos={self.pos} cols={self.cols}>'

    def __str__(self):
        cols = []
        for col_nve, col_pve in self.cols:
            cols.append(col_nve.name)
            cols.append(col_pve.name)
        return f'<Block {self.pos} {cols}>'

class Cube:
    def __init__(self):
        self.blocks = [[[Block([x, y, z]) for z in range(3)] for y in range(3)] for x in range(3)]

        self.cube_rot_speed = 90 / 20 # Degrees per frame

        # Rotation of cubes when (Axis (X=0/Y=1/Z=2) == Side (-ve=0/+ve=2))
        self.moves = {
            'L': (0, 0),
            'R': (0, 2),
            'U': (1, 0),
            'D': (1, 2),
            'F': (2, 0),
            'B': (2, 2)
        }
        self.move_queue = []
        # self.move_queue = ['L2', 'U-', 'F2']
        # for _ in range(100):
        #     move = random.choice(list(self.moves.keys()))
        #     move += random.choice(('', '2', '-'))
        #     self.move_queue.append(move)

        self.is_moving = False
        self.load_next_move()

    def load_next_move(self):
        # No moves; skip
        if len(self.move_queue) == 0:
            return

        self.is_moving = True
        move = self.move_queue.pop(0).upper()
        self.move_axis, self.move_side = self.moves[move[0]]

        self.move_rot = 90
        self.move_amt = self.cube_rot_speed
        self.move_curr_rot = 0

        if len(move) == 2:
            if move[1] == '2': # Double move
                self.move_rot *= 2
            elif move[1] == '\'': # Reverse (prime / -90 degrees) move
                self.move_rot *= -1
                self.move_amt *= -1
        
        self.rot_index = [0, 1, 2]
        self.rot_index.remove(self.move_axis)
    
    def update(self):
        if not self.is_moving:
            self.load_next_move()

        if self.is_moving:
            # rot = (self.move_rot * 2 - self.move_curr_rot) / 40 + self.move_amt / 5
            for plane in self.blocks:
                for row in plane:
                    for block in row:
                        if block.pos[self.move_axis] == self.move_side:
                            for axis in block.tris:
                                for side in axis:
                                    for tri in side:
                                        for vtx in tri.coords:
                                            vtx[self.rot_index[0]], vtx[self.rot_index[1]] = origin_rotate(vtx[self.rot_index[0]], vtx[self.rot_index[1]], self.move_amt)

            self.move_curr_rot += self.move_amt
            if self.move_amt > 0: # +ve move amoutn
                if self.move_curr_rot >= self.move_rot:
                    self.is_moving = False
                    self.handle_rotation_complete()
            else: # -ve move amount
                if self.move_curr_rot <= self.move_rot:
                    self.is_moving = False
                    self.handle_rotation_complete()
    
    def handle_rotation_complete(self):
        for plane in self.blocks:
            for row in plane:
                for block in row:
                    # For blocks involved in rotation
                    if block.pos[self.move_axis] == self.move_side:

                        # Reset all tri positions
                        block.tris = deepcopy(block.tris_original)

                        # Calculate destination block position
                        pos = [x - 1 for x in block.pos] # Shift so 0 is centre
                        pos[self.rot_index[0]], pos[self.rot_index[1]] = [round(x) for x in origin_rotate(pos[self.rot_index[0]], pos[self.rot_index[1]], self.move_rot)] # Perform rotation
                        pos = [x + 1 for x in pos] # Shift back so 1 is centre

                        cols = deepcopy(block.cols)
                        if self.move_rot == 180: # Half turn
                            cols[self.rot_index[0]][0], cols[self.rot_index[0]][1] = cols[self.rot_index[0]][1], cols[self.rot_index[0]][0]
                            cols[self.rot_index[1]][0], cols[self.rot_index[1]][1] = cols[self.rot_index[1]][1], cols[self.rot_index[1]][0]
                        elif self.move_rot == 90: # Quarter clockwise turn
                            cols[self.rot_index[0]][0], cols[self.rot_index[0]][1], cols[self.rot_index[1]][0], cols[self.rot_index[1]][1] = cols[self.rot_index[1]][0], cols[self.rot_index[1]][1], cols[self.rot_index[0]][1], cols[self.rot_index[0]][0]
                        elif self.move_rot == -90: # Quarter anticlockwise turn
                            cols[self.rot_index[0]][0], cols[self.rot_index[0]][1], cols[self.rot_index[1]][0], cols[self.rot_index[1]][1] = cols[self.rot_index[1]][1], cols[self.rot_index[1]][0], cols[self.rot_index[0]][0], cols[self.rot_index[0]][1]

                        self.blocks[pos[0]][pos[1]][pos[2]].new_cols = cols

        # Update colors
        for plane in self.blocks:
            for row in plane:
                for block in row:
                    # For blocks involved in rotation, update those with new color to be set
                    if block.pos[self.move_axis] == self.move_side:
                        if block.new_cols is not None:
                            block.cols = block.new_cols
                            block.update_tri_cols()
                            block.new_cols = None

    def __repr__(self):
        return f'<Cube blocks={self.blocks}>'

if __name__ == '__main__':
    tot = 0
    tris = Cube().blocks[0][0][0].tris
    for axis in tris:
        for side in axis:
            tot += len(side)
    print(f'Tris/block: {tot}')
