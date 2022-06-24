from rch_enums import *


class PackingInput: pass
class Combination:  pass
class Rotation3D:   pass
class Packing:      pass
class Box:          pass


Point = tuple[int, int, int]
Size = tuple[int, int, int]


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
        x, y, z = position
        a_size = self.first.size
        aw, ah, ad = a_size
        b_size = self.second.size
        bw, bh, bd = b_size

        if self.combination_type == CombinationType.WH_LOWER:
            self.first.set_position((x, y, z))
            self.second.set_position((x, y + ad, z))
        elif self.combination_type == CombinationType.WD_LOWER:
            self.first.set_position((x, y, z))
            self.second.set_position((x, y, z + ah))
        elif self.combination_type == CombinationType.HD_LOWER:
            self.first.set_position((x, y, z))
            self.second.set_position((x + aw, y, z))
        elif self.combination_type == CombinationType.WH_HIGHER:
            self.first.set_position((x, y + bd, z))
            self.second.set_position((x, y, z))
        elif self.combination_type == CombinationType.WD_HIGHER:
            self.first.set_position((x, y, z + bh))
            self.second.set_position((x, y, z))
        else:
            self.first.set_position((x + bw, y, z))
            self.second.set_position((x, y, z))
        
    def rotate(self, rotation_type: RotationType) -> None:
        self.first.rotate(rotation_type)
        self.second.rotate(rotation_type)      
        self.combination_type = self.combination_type.rotate(rotation_type)