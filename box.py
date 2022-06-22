import random
from rch_enums import *
from rch_types import *


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
        profit: int,
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
        self.profit = profit
        self.priority = priority
        self.rotations = rotations
        self.stackable = stackable
        self.combination = combination
        self.customer_code = customer_code
        self.position = position
        self.rotation_type = RotationType.NONE

    def get_common_dims(self, other):
        common_dims = []
        if self.size.w == other.size.w: common_dims.append('w')
        if self.size.h == other.size.h: common_dims.append('h')
        if self.size.d == other.size.d: common_dims.append('d')
        return common_dims

    def rotate(self, new_rotation_type: RotationType = None) -> None:
        if new_rotation_type is None:
            new_rotation_type = random.choice(list(self.rotations))
        
        new_dims = new_rotation_type.permute(self.size.to_tuple())
        self.size = Size(new_dims)
        self.rotation_type = self.rotation_type.rotate(new_rotation_type)
        
        if self.combination is not None:
            self.combination.rotate(new_rotation_type)
            if self.position is not None:
                self.combination.set_position(self.position)

    def set_position(self, position: Point):
        self.position = position
        if self.combination is not None:
            self.combination.set_position(position)

    def get_all_real_boxes(self) -> list[Box]:
        if self.combination is None:
            return [self]
        a_children = self.combination.first.get_all_real_boxes()
        b_children = self.combination.second.get_all_real_boxes()
        return a_children + b_children

    # create a new box by combining two other boxes
    @classmethod
    def from_boxes(cls, combination: Combination):
        box_a = combination.first
        box_b = combination.second
        # set new the box fields
        weight = box_a.weight + box_b.weight
        profit = box_a.profit + box_b.profit
        priority = box_a.priority + box_b.priority
        stackable = box_a.stackable and box_b.stackable
        rotations = box_a.rotations.intersection(box_b.rotations)

        # size depends on the type of combination
        if combination.combination_type in [CombinationType.WH_LOWER, CombinationType.WH_HIGHER]:
            size = Size((box_a.size.w, box_a.size.d + box_b.size.d, box_a.size.h))
        elif combination.combination_type in [CombinationType.WD_LOWER, CombinationType.WD_HIGHER]:
            size = Size((box_a.size.w, box_a.size.d, box_a.size.h + box_b.size.h))
        else:
            size = Size((box_a.size.w + box_b.size.w, box_a.size.d, box_a.size.h))

        # call constructor
        return cls('combined', size, weight, profit, priority, rotations, stackable, combination)
