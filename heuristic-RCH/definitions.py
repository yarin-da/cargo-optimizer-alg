from enum import Enum, unique, auto
from tkinter.tix import DECREASING


DIMENSIONS = 3


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
        size: tuple[int, int, int], 
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
        self.volume = size[0] * size[1] * size[2]
        # TODO: calculate taxability
        alpha = weight / 1
        self.taxability = max(weight, alpha * self.volume)

    def get_common_dims(self, other):
        return [i for i in range(DIMENSIONS) if self.size[i] == other.size[i]]

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
            size = (box_a.size[0], box_a.size[1], box_a.size[2] + box_b.size[2])
        elif combination.combination_type in [CombinationType.WD_LOWER, CombinationType.WD_HIGHER]:
            size = (box_a.size[0], box_a.size[1] + box_b.size[1], box_a.size[2])
        else:
            size = (box_a.size[0] + box_b.size[0], box_a.size[1], box_a.size[2])

        # call constructor
        return cls('combined', size, weight, priority, rotations, stackable, combination)
