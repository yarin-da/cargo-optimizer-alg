from rch_enums import *


class PackingInput: pass
class Combination:  pass
class Rotation3D:   pass
class Packing:      pass
class Point:        pass
class Size:         pass
class Box:          pass


class Point:
    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __str__(self):
        return f'Point(x={self.x}, y={self.y}, z={self.z})'

    def __repr__(self):
        return f'Point(x={self.x}, y={self.y}, z={self.z})'


class Size:
    def __init__(self, dims: tuple[int, int, int]):
        self.w = dims[0]
        self.d = dims[1]
        self.h = dims[2]

    def volume(self):
        return self.w * self.d * self.h

    def to_tuple(self):
        return (self.w, self.d, self.h)

    def __eq__(self, other):
        return self.w == other.w and self.h == other.h and self.d == other.d

    def __str__(self):
        return f'Size(w={self.w}, d={self.d}, h={self.h})'
        
    def __repr__(self):
        return f'Size(w={self.w}, d={self.d}, h={self.h})'


class Container:
    def __init__(self, size: Size, weight_limit: int):
        self.size = size
        self.weight_limit = weight_limit


# rotation in degrees
class Rotation3D():
    def __init__(self, x: int = 0, y: int = 0, z: int = 0):
        self.x = x % 180
        self.y = y % 180
        self.z = z % 180

    def __str__(self):
        return f'Rotation(x={self.x}, y={self.y}, z={self.z})'
    
    def __repr__(self):
        return f'Rotation(x={self.x}, y={self.y}, z={self.z})'


class Combination:
    def __init__(self, first: Box, second: Box, combination_type: CombinationType):
        self.first = first
        self.second = second
        self.combination_type = combination_type         

    def set_position(self, position: Point) -> None:
        x, y, z = position.x, position.y, position.z
        a_size = self.first.size
        aw, ah, ad = a_size.w, a_size.h, a_size.d
        b_size = self.second.size
        bw, bh, bd = b_size.w, b_size.h, b_size.d

        if self.combination_type == CombinationType.WH_LOWER:
            self.first.set_position(Point(x, y, z))
            self.second.set_position(Point(x, y + ad, z))
        elif self.combination_type == CombinationType.WD_LOWER:
            self.first.set_position(Point(x, y, z))
            self.second.set_position(Point(x, y, z + ah))
        elif self.combination_type == CombinationType.HD_LOWER:
            self.first.set_position(Point(x, y, z))
            self.second.set_position(Point(x + aw, y, z))
        elif self.combination_type == CombinationType.WH_HIGHER:
            self.first.set_position(Point(x, y + bd, z))
            self.second.set_position(Point(x, y, z))
        elif self.combination_type == CombinationType.WD_HIGHER:
            self.first.set_position(Point(x, y, z + bh))
            self.second.set_position(Point(x, y, z))
        else:
            self.first.set_position(Point(x + bw, y, z))
            self.second.set_position(Point(x, y, z))
        
    def rotate(self, rotation_type: RotationType) -> None:
        self.first.rotate(rotation_type)
        self.second.rotate(rotation_type)      
        self.combination_type = self.combination_type.rotate(rotation_type)