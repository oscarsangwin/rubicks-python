"""A collection of trigonometry helper functions (all angles in degrees)"""

import math

def sin(x):
    return math.sin(math.radians(x))

def cos(x):
    return math.cos(math.radians(x))

def tan(x):
    return math.tan(math.radians(x))

def asin(x):
    return math.degrees(math.asin(x))

def acos(x):
    return math.degrees(math.acos(x))

def atan2(y, x):
    return math.degrees(math.atan2(y, x))

def origin_rotate(x, y, angle):
    """Clockwise rotation around the origin"""
    new_x = x * cos(angle) + y * sin(angle)
    new_y = x * -sin(angle) + y * cos(angle)
    return new_x, new_y
