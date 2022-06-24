# import pyshipping.package as ship
# from scipy.optimize import linprog
from mip import *
import json


class Package(object):
    """Represents a package as used in cargo/shipping aplications."""

    def __init__(self, size, weight=0, nosort=False):
        """Generates a new Package object.

        The size can be given as an list of integers or an string where the sizes are determined by the letter 'x':
        >>> Package((300, 400, 500))
        <Package 500x400x300>
        >>> Package('300x400x500')
        <Package 500x400x300>
        """
        self.weight = weight
        if "x" in size:
            self.heigth, self.width, self.length = [int(x) for x in size.split('x')]
        else:
            self.heigth, self.width, self.length = size
        if not nosort:
            (self.heigth, self.width, self.length) = sorted((int(self.heigth), int(self.width),
                                                             int(self.length)), reverse=True)
        self.volume = self.heigth * self.width * self.length
        self.size = (self.heigth, self.width, self.length)

    def _get_gurtmass(self):
        """'gurtamss' is the circumference of the box plus the length - which is often used to
            calculate shipping costs.

            >>> Package((100,110,120)).gurtmass
            540
        """

        dimensions = (self.heigth, self.width, self.length)
        maxdimension = max(dimensions)
        otherdimensions = list(dimensions)
        del otherdimensions[otherdimensions.index(maxdimension)]
        return maxdimension + 2 * (sum(otherdimensions))

    gurtmass = property(_get_gurtmass)

    def hat_gleiche_seiten(self, other):
        """Prüft, ob other mindestens eine gleich grosse Seite mit self hat."""

        meineseiten = set([(self.heigth, self.width), (self.heigth, self.length), (self.width, self.length)])
        otherseiten = set([(other.heigth, other.width), (other.heigth, other.length), (other.width, other.length)])
        return not meineseiten.isdisjoint(otherseiten)

    def __getitem__(self, key):
        """The coordinates can be accessed as if the object is a tuple.
        >>> p = Package((500, 400, 300))
        >>> p[0]
        500
        """
        if key == 0:
            return self.heigth
        if key == 1:
            return self.width
        if key == 2:
            return self.length
        if isinstance(key, tuple):
            return (self.heigth, self.width, self.length)[key[0]:key[1]]
        if isinstance(key, slice):
            return (self.heigth, self.width, self.length)[key]
        raise IndexError

    def __contains__(self, other):
        """Checks if on package fits within an other.

        >>> Package((1600, 250, 480)) in Package((1600, 250, 480))
        True
        >>> Package((1600, 252, 480)) in Package((1600, 250, 480))
        False
        """
        return self[0] >= other[0] and self[1] >= other[1] and self[2] >= other[2]

    def __hash__(self):
        return self.heigth + (self.width << 16) + (self.length << 32)

    def __eq__(self, other):
        """Package objects are equal if they have exactly the same dimensions.

           Permutations of the dimensions are considered equal:

           >>> Package((100,110,120)) == Package((100,110,120))
           True
           >>> Package((120,110,100)) == Package((100,110,120))
           True
        """
        return (self.heigth == other.heigth and self.width == other.width and self.length == other.length)

    # def __cmp__(self, other):
    #     """Enables to sort by Volume."""
    #     return cmp(self.volume, other.volume)

    def __mul__(self, multiplicand):
        """Package can be multiplied with an integer. This results in the Package beeing
           stacked along the biggest side.

           >>> Package((400,300,600)) * 2
           <Package 600x600x400>
           """
        return Package((self.heigth, self.width, self.length * multiplicand), self.weight * multiplicand)

    def __add__(self, other):
        """
            >>> Package((1600, 250, 480)) + Package((1600, 470, 480))
            <Package 1600x720x480>
            >>> Package((1600, 250, 480)) + Package((1600, 480, 480))
            <Package 1600x730x480>
            >>> Package((1600, 250, 480)) + Package((1600, 490, 480))
            <Package 1600x740x480>
            """
        meineseiten = set([(self.heigth, self.width), (self.heigth, self.length), (self.width, self.length)])
        otherseiten = set([(other.heigth, other.width), (other.heigth, other.length), (other.width, other.length)])
        if meineseiten.isdisjoint(otherseiten):
            raise ValueError("%s has no fitting sites to %s" % (self, other))
        candidates = sorted(meineseiten.intersection(otherseiten), reverse=True)
        stack_on = candidates[0]
        mysides = [self.heigth, self.width, self.length]
        mysides.remove(stack_on[0])
        mysides.remove(stack_on[1])
        othersides = [other.heigth, other.width, other.length]
        othersides.remove(stack_on[0])
        othersides.remove(stack_on[1])
        return Package((stack_on[0], stack_on[1], mysides[0] + othersides[0]))

    def __str__(self):
        if self.weight:
            return "%dx%dx%d %dg" % (self.heigth, self.width, self.length, self.weight)
        else:
            return "%dx%dx%d" % (self.heigth, self.width, self.length)

    def __repr__(self):
        if self.weight:
            return "<Package %dx%dx%d %d>" % (self.heigth, self.width, self.length, self.weight)
        else:
            return "<Package %dx%dx%d>" % (self.heigth, self.width, self.length)


class Box(Package):
    def __init__(self, size, id=0, can_roat=True, can_down=True, rot=(0, 0, 0), priority=0, profit=0, weight=0,
                 nosort=False):
        super().__init__(size, weight, nosort)
        self.X = self.Y = self.Z = -1
        self.ID = id
        self.can_roat = can_roat
        self.can_down = can_down
        self.priority = priority
        self.profit = profit
        self.rotX = rot[0]
        self.rotY = rot[1]
        self.rotZ = rot[2]

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

    def get_profit(self):
        return self.profit

    def get_weight(self):
        return self.weight

    def get_priority(self):
        return self.priority

    def get_canStackAbove(self):
        return self.can_down


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


#####################
