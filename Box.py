import pyshipping.package as ship
from scipy.optimize import linprog
from mip import *


class Box(ship.Package):
    def __init__(self, size, id=0, can_roat=True, can_down=True, priority=0, weight=0, nosort=False):
        super().__init__(size, weight, nosort)
        self.X = self.Y = self.Z = -1
        self.ID = id
        self.can_roat = can_roat
        self.can_down = can_down
        self.priority = priority

    def set_coordinates(self, coordinates):
        self.X = coordinates[0]
        self.Y = coordinates[1]
        self.Z = coordinates[2]

    def reset_coordinates(self):
        self.X = self.Y = self.Z = -1

    def get_coordinates(self):
        if self.X == -1:
            return None
        coordinates = (self.X, self.Y, self.Z)
        return coordinates


class EMS:
    def __init__(self, min_coord, max_coord):
        self.min_coord = min_coord
        self.max_coord = max_coord
        self.length = abs(min_coord[0] - max_coord[0])
        self.width = abs(min_coord[1] - max_coord[1])
        self.height = abs(min_coord[2] - max_coord[2])

    def __eq__(self, other):
        return self.min_coord == other.min_coord and self.max_coord == other.max_coord

    def __ne__(self, other):
        return self.min_coord != other.min_coord or self.max_coord != other.max_coord

    def __le__(self, other):
        return self.min_coord <= other.min_coord

    def __lt__(self, other):
        return self.min_coord < other.min_coord

    def __repr__(self):
        return str(self.min_coord) + " --> " + str(self.max_coord)


