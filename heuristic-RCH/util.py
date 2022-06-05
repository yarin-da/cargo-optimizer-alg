from rch_enums import *
from rch_types import *
from debug_utils import *
import random


DIMENSIONS = 3


def to_rotation3d(rotation_type: RotationType) -> Rotation3D:
    if rotation_type == RotationType.NONE: return Rotation3D(0,  0,  0)
    if rotation_type == RotationType.W:    return Rotation3D(90, 0,  0)
    if rotation_type == RotationType.H:    return Rotation3D(0,  0,  90)
    if rotation_type == RotationType.WH:   return Rotation3D(90, 0,  90)
    if rotation_type == RotationType.D:    return Rotation3D(0,  90, 0)
    if rotation_type == RotationType.WD:   return Rotation3D(90, 90, 0)
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


