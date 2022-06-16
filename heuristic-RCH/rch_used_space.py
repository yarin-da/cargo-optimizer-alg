from rch_enums import *
from rch_types import *


class OccupiedSpace(Exception):
    def __init__(self, message):
        super().__init__(message)


class UsedSpace:
    def __init__(self, size: Size):
        self.size = size
        self.used_space_map = [[[UsedSpaceType.NOT_USED for _ in range(size.h)] for _ in range(size.d)] for _ in range(size.w)]

    def is_floating(self, box: Box) -> bool:
        if box.position.z == 0: return False
        for x in range(box.position.x, box.position.x + box.size.w):
            for y in range(box.position.y, box.position.y + box.size.d):
                if self.used_space_map[x][y][box.position.z - 1] == UsedSpaceType.USED: return False
        return True

    def unfloat(self, box: Box) -> None:
        while self.is_floating(box):
            z = box.position.z
            box.position.z = z - 1
            for x in range(box.position.x, box.position.x + box.size.w):
                for y in range(box.position.y, box.position.y + box.size.d):
                    self.used_space_map[x][y][z + box.size.h - 1] = UsedSpaceType.NOT_USED
                    self.used_space_map[x][y][z - 1] = UsedSpaceType.USED

    def ratio(self) -> float:
        sum = 0
        for z in range(self.size.h): 
            for y in range(self.size.d): 
                for x in range(self.size.w):
                    if self.used_space_map[x][y][z] == UsedSpaceType.USED: sum += 1
        return sum / self.size.volume()

    def add(self, box: Box, point: Point) -> None:
        for x in range(point.x, point.x + box.size.w):
            for y in range(point.y, point.y + box.size.d):
                for z in range(point.z, point.z + box.size.h):
                    assert_debug(self.used_space_map[x][y][z] == UsedSpaceType.NOT_USED)
                    self.used_space_map[x][y][z] = UsedSpaceType.USED
        
        if not box.stackable:
            for x in range(point.x, point.x + box.size.w):
                for y in range(point.y, point.y + box.size.d):
                    for z in range(point.z + box.size.h, self.size.h):
                        if self.used_space_map[x][y][z] == UsedSpaceType.NOT_USED:
                            self.used_space_map[x][y][z] = UsedSpaceType.UNAVAIL

    def can_be_added(self, box: Box, point: Point) -> bool:
        for x in range(point.x, point.x + box.size.w):
            for y in range(point.y, point.y + box.size.d):
                for z in range(point.z, point.z + box.size.h):
                    if self.used_space_map[x][y][z] != UsedSpaceType.NOT_USED: return False
        return True

    def vertical_projection(self, point: Point) -> Point:
        x, y, z = point.x, point.y, point.z
        if x >= self.size.w or y >= self.size.d or z >= self.size.h: return None
        if self.used_space_map[x][y][z] != UsedSpaceType.NOT_USED: return point

        while z > 0 and self.used_space_map[x][y][z - 1] == UsedSpaceType.NOT_USED:
            z -= 1
        
        return Point(x, y, z)

    def get_support_score(self, box: Box, point: Point) -> float:
        if point.z == 0: return 1
        count = 0
        for x in range(point.x, point.x + box.size.w):
            for y in range(point.y, point.y + box.size.d):
                if self.used_space_map[x][y][point.z - 1] == UsedSpaceType.USED: count += 1
        return count / (box.size.w * box.size.d)

    def total_floating(self) -> int:
        count = 0
        for x in range(self.size.w):
            for y in range(self.size.d):
                for z in range(self.size.h - 1):
                    if self.used_space_map[x][y][z] == UsedSpaceType.NOT_USED\
                        and self.used_space_map[x][y][z + 1] == UsedSpaceType.USED:
                        count += 1
        return count