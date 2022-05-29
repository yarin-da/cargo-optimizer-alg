import random
from enum import Enum, unique, auto
from tkinter.tix import DECREASING


DEBUG_MODE = True
DIMENSIONS = 3


def print_debug(message):
    if DEBUG_MODE:
        print(message)


class Point:
    def __init__(self, x: int, y: int, z: int):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z


class Size:
    def __init__(self, width: int, height: int, depth: int):
        self.w = width
        self.h = height
        self.d = depth

    def __eq__(self, other):
        return self.w == other.w and self.h == other.h and self.d == other.d


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


# rotation in degrees
class Rotation():
    def __init__(self):
        self.angle = 0

    def add(self, rotation_angle):
        self.angle = (self.angle + rotation_angle) % 360


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


class Box:
    pass


class Combination:
    def __init__(self, first: Box, second: Box, combination_type: CombinationType):
        self.first = first
        self.second = second
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
        customer_code: int = 1 # C8
    ):
        self.box_type = box_type
        self.size = size
        self.weight = weight
        self.priority = priority
        self.rotations = rotations
        self.stackable = stackable
        self.combination = combination
        self.customer_code = customer_code
        self.volume = size.w * size.h * size.d
        # TODO: calculate alpha
        alpha = weight / 1
        self.taxability = max(weight, alpha * self.volume)

        self.rotation_x = Rotation()
        self.rotation_y = Rotation()
        self.rotation_z = Rotation()

    def get_common_dims(self, other):
        common_dims = []
        if self.size.w == other.size.w: common_dims.append('w')
        if self.size.h == other.size.h: common_dims.append('h')
        if self.size.d == other.size.d: common_dims.append('d')
        return common_dims

    def rotate(self, rotation_type: RotationType = None) -> None:
        if rotation_type is None:
            rotation_type = random.choice(list(self.rotations))
        
        w, h, d = self.size.w, self.size.h, self.size.d
        if rotation_type == RotationType.X:
            self.size = Size(w, d, h)
            self.rotation_x.add(90)
        elif rotation_type == RotationType.Z:
            self.size = Size(h, w, d)
            self.rotation_z.add(90)
        elif rotation_type == RotationType.XZ:
            self.size = Size(h, d, w)
            self.rotation_x.add(90)
            self.rotation_z.add(90)
        elif rotation_type == RotationType.Y:
            self.size = Size(d, h, w)
            self.rotation_y.add(90)
        elif rotation_type == RotationType.XY:
            self.size = Size(d, w, h)
            self.rotation_x.add(90)
            self.rotation_y.add(90)

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

        # TODO: flip h and d?
        # size depends on the type of combination
        if combination.combination_type in [CombinationType.WH_LOWER, CombinationType.WH_HIGHER]:
            size = Size(box_a.size.w, box_a.size.h, box_a.size.d + box_b.size.d)
        elif combination.combination_type in [CombinationType.WD_LOWER, CombinationType.WD_HIGHER]:
            size = Size(box_a.size.w, box_a.size.h + box_b.size.h, box_a.size.d)
        else:
            size = Size(box_a.size.w + box_b.size.w, box_a.size.h, box_a.size.d)

        # call constructor
        return cls('combined', size, weight, priority, rotations, stackable, combination)


class PositionedBox:
    def __init__(self, box: Box, point: Point):
        self.box = box
        self.point = point


class OccupiedSpace(Exception):
    def __init__(self, message):
        super().__init__(message)


class UsedSpace:
    def __init__(self, size: Size):
        self.size = size
        self.used_space_map = [[[False for _ in range(size.d)] for _ in range(size.h)] for _ in range(size.w)]

    def add(self, box: Box, point: Point) -> None:
        # TODO: flip h and d?
        for x in range(point.x, point.x + box.size.w):
            for y in range(point.y, point.y + box.size.h):
                for z in range(point.z, point.z + box.size.d):
                    if not self.used_space_map[x][y][z]:
                        self.used_space_map[x][y][z] = True
                    else:
                        raise OccupiedSpace(f'occupied:: x={x} y={y} z={z} type={box.box_type}')

    def can_be_added(self, box: Box, point: Point) -> bool:
        # TODO: flip h and d?
        for x in range(point.x, point.x + box.size.w):
            for y in range(point.y, point.y + box.size.h):
                for z in range(point.z, point.z + box.size.d):
                    if self.used_space_map[x][y][z]: 
                        return False
        return True


class Packing:
    def __init__(self, container: Container):
        self.container = container
        self.positioned_boxes = []
        self.total_weight = 0
        self.used_space = UsedSpace(container.size)

    def add(self, box: Box, point: Point) -> None:
        positioned_box = PositionedBox(box, point)
        self.positioned_boxes.append(positioned_box)
        self.total_weight += box.weight
        # TODO: flip h and d?
        self.used_space.add(box, point)

    def can_be_added(self, box: Box, point: Point) -> bool:
        # does the box exceed the container weight limit
        new_total_weight = box.weight + self.total_weight
        if new_total_weight > self.container.weight_limit:
            return False
        
        # does the box exceed the container boundaries
        # TODO: flip h and d?
        corner = Point(point.x + box.size.w, point.y + box.size.h, point.z + box.size.d)
        if corner.x >= self.container.size.w or corner.y >= self.container.size.h or corner.z >= self.container.size.d:
            return False
        
        # does the box overlap another box
        if not self.used_space.can_be_added(box, point):
            return False
        
        # TODO: is the box above nonstackable box
        # IDEA: upon adding nonstackable box -> mark all space above as occupied
        
        return True


class PackingInput:
    def __init__(self, json_data):
        # init container
        container = json_data['container']
        container_size = Size(container['width'], container['height'], container['depth'])
        self.container = Container(container_size, container['maxWeight'])
        
        # init boxes
        self.boxes = []
        packages = json_data['packages']
        for pkg in packages:
            for _ in range(pkg['amount']):
                box = Box(
                    box_type=pkg['type'],
                    size=Size(pkg['width'], pkg['height'], pkg['depth']),
                    weight=pkg['weight'],
                    priority=pkg['priority'],
                    rotations=set(list(RotationType)) if pkg['canRotate'] else set([RotationType.NONE]),
                    stackable=pkg['canStackAbove'],
                    combination=None,
                    customer_code=1
                )
                self.boxes.append(box)


class PackingResult:
    def __init__(self, error: str = None, packing: Packing = None):
        self.error = error
        self.packing = packing

    def to_json(self):
        json_data = {}
        if self.error is not None:
            json_data['error'] = self.error
        if self.packing is not None:
            container_size = self.packing.container.size
            json_data['container'] = {
                "width": container_size.w,
                "height": container_size.h,
                "depth": container_size.d
            }
            positioned_boxes = self.packing.positioned_boxes
            package_types = {}
            json_data['solution'] = []
            for b in positioned_boxes:
                box_type = b.box.box_type
                if box_type not in package_types:
                    package_types[box_type] = b.box
                json_data['solution'].append({
                    "type": box_type,
                    "x": b.point.x,
                    "y": b.point.y,
                    "z": b.point.z,
                    "rotation-x": b.box.rotation_x.angle,
                    "rotation-y": b.box.rotation_y.angle, 
                    "rotation-z": b.box.rotation_z.angle
                })
            json_data['packages'] = []
            for key in package_types.keys():
                box = package_types[key]
                json_data['packages'].append({
                    "type": key,
                    "width": box.size.w,
                    "height": box.size.h,
                    "depth": box.size.d
                })
            
        return json_data