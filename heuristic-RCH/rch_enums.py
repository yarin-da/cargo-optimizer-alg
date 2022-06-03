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


@unique
class RotationType(Enum):
    # w = 0, d = 1, h = 2
    NONE = (0, 1, 2)
    W    = (0, 2, 1)
    H    = (1, 0, 2)
    WH   = (2, 0, 1)
    D    = (2, 1, 0)
    WD   = (1, 2, 0)

    @classmethod
    def get_rotation(cls, permutation: tuple[int, int, int]):
        return next(x for x in list(RotationType) if x.value == permutation)

    def permute(self, old_perm: tuple[object, object, object]) -> tuple[object, object, object]:
        permutation = self.value
        new_perm = [None, None, None]
        for i in range(3): new_perm[i] = old_perm[permutation[i]]
        return (new_perm[0], new_perm[1], new_perm[2])
        
    def rotate(self, rotation_type):
        new_rotation = rotation_type.permute(self.value)
        return self.get_rotation(new_rotation)


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
    
    def rotate(self, rotation_type: RotationType):
        normal = ('w', 'd', 'h')
        relation, old_common_dim = self.get_params()
        new_perm = rotation_type.permute(normal)
        index = new_perm.index(old_common_dim)
        new_common_dim = normal[index]
        return CombinationType.get_type(relation, new_common_dim)