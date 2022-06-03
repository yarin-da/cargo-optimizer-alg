import random
from enum import Enum, unique, auto
import numpy


DEBUG_MODE = True
DIMENSIONS = 3


class Rotation3D: pass
class Box: pass
class Combination: pass


def print_debug(message):
    if DEBUG_MODE:
        print(message)


def assert_debug(cond):
    if not cond: 
        print_debug('fail')


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
    def __init__(self, width: int, depth: int, height: int):
        self.w = width
        self.d = depth
        self.h = height

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


@unique
class PerturbOrder(Enum):
    VOLUME = auto()
    WEIGHT = auto()


@unique
class PerturbRotation(Enum):
    INDIVIDUAL = auto()
    IDENTICAL  = auto()


@unique
class SortingType(Enum):
    DECREASING_TAXABILITY    = auto()
    DECREASING_PRIORITY      = auto()
    DECREASING_CUSTOMER_CODE = auto()


'''
box=(w,h,d)
rotations = [
    [ (w, h, d), 0,  0,  0  ], # NONE
    [ (w, d, h), 90, 0,  0  ], # X
    [ (h, w, d), 0,  0,  90 ], # Z
    [ (h, d, w), 90, 0,  90 ], # XZ
    [ (d, h, w), 0,  90, 0  ], # Y
    [ (d, w, h), 90, 90, 0  ], # XY
'''
@unique
class RotationType(Enum):
    NONE = auto()
    X    = auto()
    Z    = auto()
    XZ   = auto()
    Y    = auto()
    XY   = auto()

    def to_rotation3d(self):
        if self.value == RotationType.NONE.value: return Rotation3D(0,  0,  0)
        if self.value == RotationType.X.value:    return Rotation3D(90, 0,  0)
        if self.value == RotationType.Z.value:    return Rotation3D(0,  0,  90)
        if self.value == RotationType.XZ.value:   return Rotation3D(90, 0,  90)
        if self.value == RotationType.Y.value:    return Rotation3D(0,  90, 0)
        if self.value == RotationType.XY.value:   return Rotation3D(90, 90, 0)
        assert_debug(False)


# rotation in degrees
class Rotation3D():
    def __init__(self, x: int = 0, y: int = 0, z: int = 0):
        self.x = x % 180
        self.y = y % 180
        self.z = z % 180

    def add(self, angles): 
        self.x = (self.x + angles[0]) % 180
        self.y = (self.y + angles[1]) % 180
        self.z = (self.z + angles[2]) % 180
        return self
    
    def add_x(self, rotation_angle): self.x = (self.x + rotation_angle) % 180
    def add_y(self, rotation_angle): self.y = (self.y + rotation_angle) % 180
    def add_z(self, rotation_angle): self.z = (self.z + rotation_angle) % 180

    def to_rotation_type(self):
        angles = (self.x, self.y, self.z)
        if angles == (90, 0, 0):   return RotationType.X
        if angles == (0, 0, 90):   return RotationType.Z
        if angles == (90, 0, 90):  return RotationType.XZ
        if angles == (0, 90, 0):   return RotationType.Y
        if angles == (90, 90, 90): return RotationType.Y
        if angles == (90, 90, 0):  return RotationType.XY
        if angles == (0, 90, 90):  return RotationType.XY
        if angles == (0, 0, 0):    return RotationType.NONE
        assert_debug(False)

    def __str__(self):
        return f'Rotation(x={self.x}, y={self.y}, z={self.z})'
    
    def __repr__(self):
        return f'Rotation(x={self.x}, y={self.y}, z={self.z})'


'''
assuming we have two boxes A, B:
each combination type notes which two dimensions are equal (W - width, H - height, D - depth)
also, lower/higher note the position of A relative to B
e.g. (A, B, WH_LOWER): 
  A and B are equal in width and height, thus they'll be merged along the depth
  LOWER notes that the depth value of A is lower with respect to B
'''
@unique
class CombinationType(Enum):
    WH_LOWER  = auto()
    WD_LOWER  = auto()
    HD_LOWER  = auto()
    WH_HIGHER = auto()
    WD_HIGHER = auto()
    HD_HIGHER = auto()

    @classmethod
    def get_type(cls, relation, common_dim):
        if relation == 'lower':
            if common_dim == 'd': return CombinationType.WH_LOWER
            if common_dim == 'h': return CombinationType.WD_LOWER
            if common_dim == 'w': return CombinationType.HD_LOWER
        else:
            if common_dim == 'd': return CombinationType.WH_HIGHER
            if common_dim == 'h': return CombinationType.WD_HIGHER
            if common_dim == 'w': return CombinationType.HD_HIGHER
        assert_debug(False)

    def get_params(self):
        if self.value == CombinationType.WH_LOWER.value: return ('lower', 'd')
        if self.value == CombinationType.WD_LOWER.value: return ('lower', 'h')
        if self.value == CombinationType.HD_LOWER.value: return ('lower', 'w')
        if self.value == CombinationType.WH_HIGHER.value: return ('higher', 'd')
        if self.value == CombinationType.WD_HIGHER.value: return ('higher', 'h')
        if self.value == CombinationType.HD_HIGHER.value: return ('higher', 'w')
        assert_debug(False)


def combine(a: Box, b: Box, common_dims: list[int], relation: str = None) -> list[Box]:
    relation = random.choice(['lower', 'higher']) if relation is None else relation
    amount_of_common_dims = len(common_dims)
    common_dim = None
    if amount_of_common_dims == 3: 
        common_dim = random.choice(['w', 'h', 'd'])
    elif amount_of_common_dims == 2:
        if 'w' in common_dims and 'h' in common_dims: 
            common_dim = 'd'
        elif 'w' in common_dims and 'd' in common_dims: 
            common_dim = 'h'
        else: 
            common_dim = 'w'

    assert_debug(common_dim is not None)
    combination_type = CombinationType.get_type(relation, common_dim)
    if relation == 'lower':
        combination = Combination(a, b, combination_type)
    else: 
        combination = Combination(b, a, combination_type)
    return Box.from_boxes(combination)


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
        assert_debug(self.combination_type is not None)
        self.first.rotate(rotation_type)
        self.second.rotate(rotation_type)
        relation, old_common_dim = self.combination_type.get_params()
        # TODO: rotate combination type
        new_common_dim = None
        
        if old_common_dim == 'w':
            if rotation_type == RotationType.NONE: new_common_dim = 'w'
            elif rotation_type == RotationType.X:  new_common_dim = 'w'
            elif rotation_type == RotationType.Z:  new_common_dim = 'd'
            elif rotation_type == RotationType.XZ: new_common_dim = 'd'
            elif rotation_type == RotationType.Y:  new_common_dim = 'h'
            elif rotation_type == RotationType.XY: new_common_dim = 'h'        
        elif old_common_dim == 'd':
            if rotation_type == RotationType.NONE: new_common_dim = 'd'
            elif rotation_type == RotationType.X:  new_common_dim = 'h'
            elif rotation_type == RotationType.Z:  new_common_dim = 'w'
            elif rotation_type == RotationType.XZ: new_common_dim = 'h'
            elif rotation_type == RotationType.Y:  new_common_dim = 'd'
            elif rotation_type == RotationType.XY: new_common_dim = 'w'        
        elif old_common_dim == 'h':
            if rotation_type == RotationType.NONE: new_common_dim = 'h'
            elif rotation_type == RotationType.X:  new_common_dim = 'd'
            elif rotation_type == RotationType.Z:  new_common_dim = 'h'
            elif rotation_type == RotationType.XZ: new_common_dim = 'w'
            elif rotation_type == RotationType.Y:  new_common_dim = 'w'
            elif rotation_type == RotationType.XY: new_common_dim = 'd'
        combination_type = CombinationType.get_type(relation, new_common_dim)
        print_debug(f'{self.combination_type} x {rotation_type} = {combination_type}')
        self.combination_type = combination_type


class Box:
    '''
    size = (width, height, depth)
    rotations = set of possible rotation types
    stackable = False (fragile) iff no box can be stacked above
    customer_code = group packages for each customer, and pack them in certain order
    priority = [1-10] the higher, the more likely the package will be packed (10 being hard constraint)
    children = (relevant for combined boxes) - specifies which two boxes created this box
    '''
    def __init__(
        self, 
        box_type: str,
        size: Size, 
        weight: int, # C1
        priority: int, # C3
        rotations: set[RotationType], # C4
        stackable: bool, # C5
        combination: Combination = None,
        customer_code: int = 1, # C8
        position: Point = None,
    ):
        self.box_type = box_type
        self.size = size
        self.weight = weight
        self.priority = priority
        self.rotations = rotations
        self.stackable = stackable
        self.combination = combination
        self.customer_code = customer_code
        self.position = position
        self.rotation = Rotation3D()
        self.volume = size.w * size.h * size.d
        # TODO: calculate alpha
        alpha = weight / 1
        self.taxability = max(weight, alpha * self.volume)

    def get_common_dims(self, other):
        common_dims = []
        if self.size.w == other.size.w: common_dims.append('w')
        if self.size.h == other.size.h: common_dims.append('h')
        if self.size.d == other.size.d: common_dims.append('d')
        return common_dims

    # TODO: may not be necessary
    def update_rotation(self, x, y, z):
        self.rotation.add((x, y, z))
        new_rotations = set()
        for rot in self.rotations:
            new_rotation = rot.to_rotation3d().add((-x, -y, -z)).to_rotation_type()
            new_rotations.add(new_rotation)
        self.rotations = new_rotations

    def rotate(self, rotation_type: RotationType = None) -> None:
        if rotation_type is None:
            rotation_type = random.choice(list(self.rotations))
        
        w, d, h = self.size.w, self.size.d, self.size.h
        x_angle, y_angle, z_angle = 0, 0, 0
        if rotation_type == RotationType.X:
            self.size = Size(w, h, d)
            x_angle = 90
        elif rotation_type == RotationType.Z:
            self.size = Size(d, w, h)
            z_angle = 90
        elif rotation_type == RotationType.XZ:
            self.size = Size(h, w, d)
            x_angle, z_angle = 90, 90
        elif rotation_type == RotationType.Y:
            self.size = Size(h, d, w)
            y_angle = 90
        elif rotation_type == RotationType.XY:
            self.size = Size(d, h, w)
            x_angle, y_angle = 90, 90
        
        self.update_rotation(x_angle, y_angle, z_angle)
        if self.combination is not None:
            self.combination.rotate(rotation_type)
            if self.position is not None:
                self.combination.set_position(self.position)

    def set_position(self, position: Point):
        self.position = position
        if self.combination is not None:
            self.combination.set_position(position)

    # create a new box by combining two other boxes
    @classmethod
    def from_boxes(cls, combination: Combination):
        box_a = combination.first
        box_b = combination.second
        # set new the box fields
        weight = box_a.weight + box_b.weight
        priority = box_a.priority + box_b.priority
        stackable = box_a.stackable and box_b.stackable
        rotations = box_a.rotations.intersection(box_b.rotations)

        # size depends on the type of combination
        if combination.combination_type in [CombinationType.WH_LOWER, CombinationType.WH_HIGHER]:
            size = Size(box_a.size.w, box_a.size.d + box_b.size.d, box_a.size.h)
        elif combination.combination_type in [CombinationType.WD_LOWER, CombinationType.WD_HIGHER]:
            size = Size(box_a.size.w, box_a.size.d, box_a.size.h + box_b.size.h)
        else:
            size = Size(box_a.size.w + box_b.size.w, box_a.size.d, box_a.size.h)

        # call constructor
        return cls('combined', size, weight, priority, rotations, stackable, combination)


class OccupiedSpace(Exception):
    def __init__(self, message):
        super().__init__(message)


class UsedSpace:
    def __init__(self, size: Size):
        self.size = size
        self.used_space_map = [[[False for _ in range(size.h)] for _ in range(size.d)] for _ in range(size.w)]

    def sum(self):
        ret = 0
        for x in range(self.size.w):
            for y in range(self.size.d):
                for z in range(self.size.h):
                    if self.used_space_map[x][y][z]: ret += 1
        return ret

    def add(self, box: Box, point: Point) -> None:
        before = self.sum()
        for x in range(point.x, point.x + box.size.w):
            for y in range(point.y, point.y + box.size.d):
                for z in range(point.z, point.z + box.size.h):
                    assert_debug(not self.used_space_map[x][y][z])
                    self.used_space_map[x][y][z] = True
        after = self.sum()
        assert_debug(after - before == box.volume)

    def can_be_added(self, box: Box, point: Point) -> bool:
        for x in range(point.x, point.x + box.size.w):
            for y in range(point.y, point.y + box.size.d):
                for z in range(point.z, point.z + box.size.h):
                    if self.used_space_map[x][y][z]: return False
        return True

    def vertical_projection(self, point: Point) -> Point:
        x, y, z = point.x, point.y, point.z
        if x >= self.size.w or y >= self.size.d or z >= self.size.h: return None
        if self.used_space_map[x][y][z]: return point

        while z > 0 and not self.used_space_map[x][y][z - 1]: 
            z -= 1
        
        return Point(x, y, z)

    def get_support_score(self, box: Box, point: Point) -> int:
        if point.z == 0: return box.size.w * box.size.d
        count = 0
        for x in range(point.x, point.x + box.size.w):
            for y in range(point.y, point.y + box.size.d):
                if self.used_space_map[x][y][point.z - 1]: count += 1
        return count


class Packing:
    def __init__(self, container: Container):
        self.container = container
        self.boxes = []
        self.total_weight = 0
        self.total_priority = 0
        self.used_space = UsedSpace(container.size)
        self.used_volume = 0

    def add(self, box: Box, point: Point, potential_points: list[Point]) -> None:
        box.set_position(point)
        self.boxes.append(box)
        self.total_weight += box.weight
        self.total_priority += box.priority
        self.used_space.add(box, point)

        potential_points.remove(point)

        corner_w = Point(point.x + box.size.w, point.y, point.z)
        projected_corner_w = self.used_space.vertical_projection(corner_w)
        if projected_corner_w is not None:
            potential_points.append(projected_corner_w)

        corner_d = Point(point.x, point.y + box.size.d, point.z)
        projected_corner_d = self.used_space.vertical_projection(corner_d)
        if projected_corner_d is not None:
            potential_points.append(projected_corner_d)

        corner_h = Point(point.x, point.y, point.z + box.size.h)
        projected_corner_h = self.used_space.vertical_projection(corner_h)
        if projected_corner_h is not None:
            potential_points.append(projected_corner_h)

    def can_be_added(self, box: Box, point: Point) -> bool:
        # does the box exceed the container weight limit
        new_total_weight = box.weight + self.total_weight
        if new_total_weight > self.container.weight_limit:
            return False
        
        # does the box exceed the container boundaries
        corner = Point(point.x + box.size.w, point.y + box.size.d, point.z + box.size.h)
        if corner.x > self.container.size.w or corner.y > self.container.size.d or corner.z > self.container.size.h:
            return False

        # does the box overlap another box
        if not self.used_space.can_be_added(box, point):
            return False
        
        # TODO: is the box above nonstackable box
        # IDEA: upon adding nonstackable box -> mark all space above as occupied
        return True

    def get_support_score(self, box: Box, point: Point) -> int:
        return self.used_space.get_support_score(box, point)


class PackingInput:
    def __init__(self, json_data):
        self.original_json = json_data

        # init container
        container = json_data['container']
        container_size = Size(container['width'], container['depth'], container['height'])
        self.container = Container(container_size, container['maxWeight'])
        
        # init boxes
        self.boxes = []
        packages = json_data['packages']
        for pkg in packages:
            # convert input to correct types (incase we get json where 'width' is a string for example)
            amount = int(pkg['amount'])
            canRotate = pkg['canRotate'] if type(pkg['canRotate']) == bool else pkg['canRotate'].lower() == 'true'
            canStackAbove = pkg['canStackAbove'] if type(pkg['canStackAbove']) == bool else pkg['canStackAbove'].lower() == 'true'
            width, depth, height = int(pkg['width']), int(pkg['depth']), int(pkg['height'])
            priority = int(pkg['priority'])
            weight = int(pkg['weight'])
            for _ in range(amount):
                box = Box(
                    box_type=pkg['type'],
                    size=Size(width, depth, height),
                    weight=weight,
                    priority=priority,
                    rotations=set(list(RotationType)) if canRotate else set([RotationType.NONE]),
                    stackable=canStackAbove,
                    combination=None,
                    customer_code=1
                )
                self.boxes.append(box)


def get_all_real_boxes(box: Box) -> list[Box]:
    if box.combination is None:
        return [box]
    a_children = get_all_real_boxes(box.combination.first)
    b_children = get_all_real_boxes(box.combination.second)
    return a_children + b_children


class PackingResult:
    def __init__(self, error: str = None, packing_input: PackingInput = None, packing: Packing = None):
        self.error = error
        self.packing = packing
        self.packing_input = packing_input  

    def to_json(self):
        json_data = {}
        if self.error is not None:
            json_data['error'] = self.error
        if self.packing is not None:
            container_size = self.packing.container.size
            json_data['container'] = {
                "width": int(container_size.w),
                "height": int(container_size.h),
                "depth": int(container_size.d)
            }
            
            packages = self.packing_input.original_json['packages']
            json_data['packages'] = []
            for pkg in packages:
                print_debug({
                    "type": pkg['type'],
                    "width": int(pkg['width']),
                    "height": int(pkg['height']),
                    "depth": int(pkg['depth'])
                })
                json_data['packages'].append({
                    "type": pkg['type'],
                    "width": int(pkg['width']),
                    "height": int(pkg['height']),
                    "depth": int(pkg['depth'])
                })
            
            json_data['solution'] = []
            boxes = self.packing.boxes
            
            ids = []
            dup_count = 0

            for block in boxes:
                real_boxes = get_all_real_boxes(block)
                print_debug(f'BLOCK :: pos={block.position} size={block.size}')
                for box in real_boxes:
                    if id(box) not in ids:
                        ids.append(id(box))
                    else:
                        dup_count += 1
                    print_debug(f'\ttype={box.box_type} pos={box.position} size={box.size} rotation={box.rotation}')
                    box_type = box.box_type
                    json_data['solution'].append({
                        "type": box_type,
                        "x": box.position.x,
                        "y": box.position.y,
                        "z": box.position.z,
                        "rotation-x": box.rotation.x,
                        "rotation-y": box.rotation.y, 
                        "rotation-z": box.rotation.z
                    })
            assert_debug(dup_count == 0)
        return json_data

