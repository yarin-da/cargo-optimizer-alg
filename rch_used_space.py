from rch_enums import *
from rch_types import *
import numpy as np


class OccupiedSpace(Exception):
    def __init__(self, message):
        super().__init__(message)


class UsedSpace:
    def __init__(self, size: Size):
        self.size = size
        self.volume = size[0]*size[1]*size[2]
        self.used_space_count = 0
        self.used_space_map = np.zeros(size)

    def is_floating(self, box: Box) -> bool:
        if box.position[2] == 0: return False
        begin_w = box.position[0]
        end_w = begin_w + box.size[0]
        begin_d = box.position[1]
        end_d = begin_d + box.size[1]
        area_below = self.used_space_map[begin_w:end_w, begin_d:end_d, box.position[2] - 1]
        return np.all(area_below != UsedSpaceType.USED.value)

    def unfloat(self, box: Box) -> None:
        while self.is_floating(box):
            z = box.position[2]
            box.position[2] = z - 1
            begin_w = box.position[0]
            end_w = begin_w + box.size[0]
            begin_d = box.position[1]
            end_d = begin_d + box.size[1]
            self.used_space_map[begin_w:end_w, begin_d:end_d, z + box.size[2] - 1] = UsedSpaceType.NOT_USED.value
            self.used_space_map[begin_w:end_w, begin_d:end_d, z - 1] = UsedSpaceType.USED.value

    def ratio(self) -> float:
        return self.used_space_count / self.volume

    def add(self, box: Box, point: Point) -> None:
        self.used_space_count += box.size[0]*box.size[1]*box.size[2]
        begin_w = point[0]
        end_w = begin_w + box.size[0]
        begin_d = point[1]
        end_d = begin_d + box.size[1]
        self.used_space_map[begin_w:end_w, begin_d:end_d, point[2]:point[2]+box.size[2]] = UsedSpaceType.USED.value
        if not box.stackable and point[2] + box.size[2] < self.size[2] - 1:
            self.used_space_map[begin_w:end_w, begin_d:end_d, point[2]+box.size[2]] = UsedSpaceType.UNAVAIL.value

    def can_be_added(self, box: Box, point: Point) -> bool:
        begin_w = point[0]
        end_w = begin_w + box.size[0]
        begin_d = point[1]
        end_d = begin_d + box.size[1]
        begin_h = point[2]
        end_h = begin_h + box.size[2]
        
        if not box.stackable and end_h < self.size[2] - 1:
            area_above = self.used_space_map[begin_w:end_w, begin_d:end_d, end_h:self.size[2]]
            is_area_above_free = np.all(area_above == UsedSpaceType.NOT_USED.value)
            if not is_area_above_free: return False
        
        box_area = self.used_space_map[begin_w:end_w, begin_d:end_d, begin_h:end_h]
        return np.all(box_area == UsedSpaceType.NOT_USED.value)
        
    def vertical_projection(self, point: Point) -> Point:
        x, y, z = point
        if x >= self.size[0] or y >= self.size[1] or z >= self.size[2]: return None
        if self.used_space_map[x, y, z] != UsedSpaceType.NOT_USED.value: return point

        while z > 0 and self.used_space_map[x, y, z - 1] == UsedSpaceType.NOT_USED.value:
            z -= 1
        
        return (x, y, z)

    def get_support_score(self, box: Box, point: Point) -> float:
        if point[2] == 0: return 1
        begin_w = point[0]
        end_w = begin_w + box.size[0]
        begin_d = point[1]
        end_d = begin_d + box.size[1]
        count = np.count_nonzero(self.used_space_map[begin_w:end_w, begin_d:end_d, point[2] - 1] == UsedSpaceType.USED.value)
        return count / (box.size[0] * box.size[1])

