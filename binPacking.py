#!/usr/bin/env python
# encoding: utf-8
"""
binpack_simple.py
This code implemnts 3D bin packing in pure Python
Bin packing in this context is calculating the best way to store a number of differently sized boxes in a
number of fixed sized "bins". It is what usually happens in a Warehouse bevore shipping.
The Algorithm has a simple fit first approach, but can archive relative good results because it tries
different rectangular rotations of the packages. Since the Algorithm can't interate over all possible
combinations we use a heuristic approach.
For a few dozen packages it reaches adaequate runtime. Below are the results calculated about a set of
500 real world packing problems.
Binsize     Runtime                 Recuction in shipped Packages
600x400x400 31.5993559361 4970 2033 40.9054325956
600x445x400 31.5596890450 4970 1854 37.3038229376
600x500x400 29.1432909966 4970 1685 33.9034205231
On the datasets we operate on we can archive comparable preformance to academic higly optimized C code
like David Pisinger's 3bpp:
     Runtime                 Recuction in shipped Packages
py   11.3468761444 2721 1066 39.1767732451
3bpp 9.95857691765 2721 1086 39.9117971334
The Python implementation is somewhat slower but can archive slightly better packing results on our
datasets.
Created by Maximillian Dornseif on 2010-08-14.
Copyright (c) 2010 HUDORA. All rights reserved.
"""

import time
import random
from itertools import permutations


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
        self.volume = self.heigth * self.width *self.length
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
        otherseiten = set([(other.heigth, other.width), (other.heigth, other.length),(other.width, other.length)])
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
        return self.heigth+(self.width<<16)+(self.length<<32)

    def __eq__(self, other):
        """Package objects are equal if they have exactly the same dimensions.

           Permutations of the dimensions are considered equal:

           >>> Package((100,110,120)) == Package((100,110,120))
           True
           >>> Package((120,110,100)) == Package((100,110,120))
           True
        """
        return (self.heigth == other.heigth and self.width == other.width and self.length == other.length)

    def __cmp__(self, other):
        """Enables to sort by Volume."""
        return cmp(self.volume, other.volume)

    def __mul__(self, multiplicand):
        """Package can be multiplied with an integer. This results in the Package beeing
           stacked along the biggest side.

           >>> Package((400,300,600)) * 2
           <Package 600x600x400>
           """
        return Package((self.heigth, self.width, self.length*multiplicand), self.weight*multiplicand)

    def __add__(self, other):
        """
            >>> Package((1600, 250, 480)) + Package((1600, 470, 480))
            <Package 1600x720x480>
            >>> Package((1600, 250, 480)) + Package((1600, 480, 480))
            <Package 1600x730x480>
            >>> Package((1600, 250, 480)) + Package((1600, 490, 480))
            <Package 1600x740x480>
            """
        meineseiten = set([(self.heigth, self.width), (self.heigth, self.length),(self.width, self.length)])
        otherseiten = set([(other.heigth, other.width), (other.heigth, other.length),(other.width, other.length)])
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
    def __init__(self, size, id=0, can_roat=True, can_down=True, rotX=0, rotY=0, rotZ=0, priority=0, weight=0, nosort=False):
        super().__init__(size, weight, nosort)
        self.X = self.Y = self.Z = -1
        self.ID = id
        self.can_roat = can_roat
        self.can_down = can_down
        self.priority = priority
        self.rotX = rotX
        self.rotY = rotY
        self.rotZ = rotZ

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


def packstrip(bin, p, start_width=0, start_length=0):
    """Creates a Strip which fits into bin.
    Returns the Packages to be used in the strip, the dimensions of the strip as a 3-tuple
    and a list of "left over" packages.
    """
    # This code is somewhat optimized and somewhat unreadable

    s = []  # strip
    r = []  # rest
    ss = sw = sl = 0  # stripsize
    s_x, s_y = start_width, start_length
    bs = bin.heigth  # binsize
    sapp = s.append  # speedup
    rapp = r.append  # speedup
    ppop = p.pop  # speedup
    while p and (ss <= bs):
        n = ppop(0)
        nh, nw, nl = n.size
        if ss + nh <= bs:
            n.set_coordinates((s_x, s_y, ss))
            ss += nh
            sapp(n)
            # set to the container

            if nw > sw:
                sw = nw
            if nl > sl:
                sl = nl
        else:
            rapp(n)
    return s, (ss, sw, sl), r + p


def packlayer(bin, packages, layer_y_start):
    strips = []
    layersize = 0
    layerx = 0
    layery = 0
    binsize = bin.width
    while packages:
        strip, (sizex, stripsize, sizez), rest = packstrip(bin, packages, layersize, layer_y_start)
        if layersize + stripsize <= binsize:
            packages = rest
            if not strip:
                # we were not able to pack anything
                break
            layersize += stripsize # width
            layerx = max([sizex, layerx]) # height
            layery = max([sizez, layery]) # length
            strips.extend(strip)
        else:
            # Next Layer please
            packages = strip + rest
            break
    return strips, (layerx, layersize, layery), packages


def packbin(bin, packages):
    # packages.sort()
    sorted(packages, key=lambda x: x.volume, reverse=True)
    layers = []
    contentheigth = 0
    contentx = 0
    contenty = 0
    binsize = bin.length
    layersize = 0
    layer_width = 0
    while packages:
        layer, (sizex, sizey, layersize), rest = packlayer(bin, packages, contentheigth)
        if contentheigth + layersize <= binsize:
            packages = rest
            if not layer:
                # we were not able to pack anything
                break
            contentheigth += layersize
            contentx = max([contentx, sizex])
            contenty = max([contenty, sizey])
            layers.extend(layer)

        else:
            # Next Bin please
            packages = layer + rest
            break
    return layers, (contentx, contenty, contentheigth), packages


def packit(bin, originalpackages):
    packedbins = []
    packages = sorted(originalpackages, key=lambda x: x.volume, reverse=True)
    while packages:
        packagesinbin, (binx, biny, binz), rest = packbin(bin, packages)
        if not packagesinbin:
            # we were not able to pack anything
            break
        packedbins.append(packagesinbin)
        packages = rest
    # we now have a result, try to get a better result by rotating some bins

    return packedbins, rest


class Timeout(Exception):
    pass


def allpermutations_helper(permuted, todo, maxcounter, callback, bin, bestpack, counter):
    if not todo:
        return counter + callback(bin, permuted, bestpack)
    else:
        others = todo[1:]
        thispackage = todo[0]
        if thispackage.can_roat is False:
            return allpermutations_helper(permuted + [thispackage], others, maxcounter, callback, bin, bestpack,
                                          counter)
        w, h, d = thispackage
        rotations = [
            [ (w, h, d), 0,  0,  0  ],
            [ (w, d, h), 90, 0,  0  ],
            [ (h, w, d), 0,  0,  90 ],
            [ (h, d, w), 90, 0,  90 ],
            [ (d, h, w), 0,  90, 0  ],
            [ (d, w, h), 90, 90, 0  ],
        ]
        for dims, rotX, rotY, rotZ in rotations:
            thispackage = Box(size=dims, rotX=rotX, rotY=rotY, rotZ=rotZ, nosort=True)
            if thispackage in bin:
                counter = allpermutations_helper(permuted + [thispackage], others, maxcounter, callback,
                                                 bin, bestpack, counter)
            if counter > maxcounter:
                raise Timeout('more than %d iterations tries' % counter)
        return counter


def trypack(bin, packages, bestpack):
    bins, rest = packit(bin, packages)
    if len(bins) < bestpack['bincount']:
        bestpack['bincount'] = len(bins)
        bestpack['bins'] = bins
        bestpack['rest'] = rest
    if bestpack['bincount'] < 2:
        raise Timeout('optimal solution found')
    return len(packages)


def allpermutations(todo, bin, iterlimit=5000):
    random.seed(1)
    random.shuffle(todo)
    bestpack = dict(bincount=len(todo) + 1)
    try:
        # First try unpermuted
        trypack(bin, todo, bestpack)
        # now try permutations
        allpermutations_helper([], todo, iterlimit, trypack, bin, bestpack, 0)
    except Timeout as e:
        print(e)
    return bestpack['bins'], bestpack['rest']


def binpack(packages, bin, iterlimit=5000):
    """Packs a list of Package() objects into a number of equal-sized bins.
    Returns a list of bins listing the packages within the bins and a list of packages which can't be
    packed because they are too big."""
    return allpermutations(packages, bin, iterlimit)


def run(input_data):
    result = {}
    result['packages'] = []
    packages = []
    for package in input_data['packages']:
        result['packages'].append({
            'type': package['type'],
            'width': package['width'],
            'height': package['height'],
            'depth': package['depth'],
        })
        package_size = (package['width'], package['height'], package['depth'])
        package_type = package['type']
        packages += [Box(size=package_size, id=f'{package_type}-{i}') for i in range(package['amount'])]

    container_data = input_data['container']
    container_size = (container_data['width'], container_data['height'], container_data['depth'])
    container = Package(size=container_size)
    result['container'] = {
        'width': container_data['width'],
        'height': container_data['height'],
        'depth': container_data['depth'],
    }

    # initialize counters and time
    number_of_packages = 0
    number_of_bins = 0
    start = time.time()

    # solve
    bins, rest = binpack(packages, container)
    if rest:
        print("invalid data", rest)
    else:
        number_of_packages += len(packages)
        number_of_bins += len(bins)

    # print results
    volume_of_container = container.volume

    for i in range(len(bins)):
        print(len(bins[i]))
        print(f"utilization of container_{i + 1}: {sum(x.volume for x in bins[i]) / volume_of_container * 100}")

    print("Container volume", volume_of_container)
    print("Total time", time.time() - start)
    print("Bins: ", bins)
    print(
        f"number of packages: {number_of_packages}, number of containers: {number_of_bins}, {float(number_of_bins) / number_of_packages * 100}")
    
    result['solution'] = []
    for i in range(len(bins[0])):
        result['solution'].append({
            "type": bins[0][i].ID.split('-')[0],
            'x': bins[0][i].X,
            'y': bins[0][i].Y,
            'z': bins[0][i].Z,
            'rotation-x': bins[0][i].rotX,
            'rotation-y': bins[0][i].rotY,
            'rotation-z': bins[0][i].rotZ,
        })
        # print(f"box id: {bins[0][i].ID} coordinates {bins[0][i].X, bins[0][i].Y, bins[0][i].Z} rotations {bins[0][i].rotX, bins[0][i].rotY, bins[0][i].rotZ}")
    return result