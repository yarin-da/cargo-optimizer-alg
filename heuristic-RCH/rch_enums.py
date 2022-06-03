from debug_utils import *
from enum import Enum, unique, auto


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