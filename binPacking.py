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
import cProfile
from pyshipping.package import Package
from itertools import permutations
from Box import Box


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
        for dimensions in set(permutations((thispackage[0], thispackage[1], thispackage[2]))):
            thispackage = Box(dimensions, nosort=True)
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
    except Timeout:
        pass
    return bestpack['bins'], bestpack['rest']


def binpack(packages, bin=None, iterlimit=5000):
    """Packs a list of Package() objects into a number of equal-sized bins.
    Returns a list of bins listing the packages within the bins and a list of packages which can't be
    packed because they are to big."""
    if not bin:
        bin = Package("200x200x600")
    return allpermutations(packages, bin, iterlimit)


def test():
    fd = open('testdata.txt')
    # initialize counters and time
    number_of_packages = 0
    number_of_bins = 0
    start = time.time()

    container = Package("400x200x600", nosort=True)
    # load data set
    packages = []
    for line in fd:
        packages = packages + [Box(pack,id=k) for k,pack in enumerate(line.strip().split())]
        if not packages:
            continue
    bins, rest = binpack(packages, container)
    if rest:
        print("invalid data", rest, line)
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
    for i in range(len(bins[0])):
        print(f"box id: {bins[0][i].ID} coordinates {bins[0][i].X, bins[0][i].Y, bins[0][i].Z}")


if __name__ == '__main__':
    cProfile.run('test()')
