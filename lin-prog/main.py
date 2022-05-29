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
    def __init__(self, size, id=0, can_roat=True, can_down=True, rotX=0, rotY=0, rotZ=0, priority=0, profit=0, weight=0,
                 nosort=False):
        super().__init__(size, weight, nosort)
        self.X = self.Y = self.Z = -1
        self.ID = id
        self.can_roat = can_roat
        self.can_down = can_down
        self.priority = priority
        self.profit = profit
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


def parse_json_input(input_data):
    result = {}
    result['packages'] = []
    boxes = []
    for package in input_data['packages']:
        result['packages'].append({
            'type': package['type'],
            'width': package['width'],
            'height': package['height'],
            'depth': package['depth'],
            'weight': package['weight'],
            'priority': package['priority'],
            'profit': package['profit'],
            'canRotate': package['canRotate'],
            'canStackAbove': package['canStackAbove']
        })
        weight = package['weight']
        priority = package['priority']
        profit = package['profit']
        canRotate = package['canRotate']
        canStackAbove = package['canStackAbove']

        package_size = (package['height'], package['width'], package['depth'])
        package_type = package['type']
        boxes += [Box(size=package_size, id=f'{package_type}-{i}', weight=weight, priority=priority, profit=profit,
                      can_roat=canRotate, can_down=canStackAbove,
                      nosort=True) for i in range(package['amount'])]

    container_data = input_data['container']
    maxWeight = container_data['maxWeight']
    container_size = (container_data['height'], container_data['width'], container_data['depth'])
    container = Package(size=container_size, weight=maxWeight, nosort=True)
    result['container'] = {
        'width': container_data['width'],
        'height': container_data['height'],
        'depth': container_data['depth'],
        'cost': container_data['cost'],
        'maxWeight': container_data['maxWeight']
    }
    # result <-- the object that we'd finally return to the client
    # container <-- an object that contains the dimensions of the container
    # boxes <-- an array of Boxes
    return result, container, boxes


def generateBox():
    fd = open('testdata.txt')
    cargo = []
    for line in fd:
        cargo = cargo + [Box(pack) for pack in line.strip().split()]
        # break
    return cargo


if __name__ == '__main__':
    filepath = './input.json'
    m = Model("CLP")
    M = 1e7

    try:
        json_file = open(filepath, 'r')
        raw_data = json_file.read()
        json_data = json.loads(raw_data)
        result, container, boxes = parse_json_input(json_data)
        n = len(boxes)
    except Exception as e:
        print('received exception', e)
        exit(-1)

    L, W, H = (container.length, container.width, container.heigth)

    # Add decision variables.
    a_list = [m.add_var(name="a_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    b_list = [m.add_var(name="b_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    c_list = [m.add_var(name="c_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    d_list = [m.add_var(name="d_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    #e_list = [m.add_var(name="e_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]

    e_list = []
    # e_ij is a binary variable which is equal to 1 if box i is placed on the top of the box j.
    # If boxes[j].StackAbove == false --> for all i, e_ij = 0.
    for i in range(n):
        for j in range(i + 1, n):
            if not boxes[j].get_canStackAbove():
                m.add_var(name="e_" + str(i) + "_" + str(j), lb=0, ub=0) # e_ij = 0
            else:
                m.add_var(name="e_" + str(i) + "_" + str(j), var_type=BINARY) # e_ij binary

    f_list = [m.add_var(name="f_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    #  A binary variable which is equal to 1 if box i is placed in the container
    s_list = [m.add_var(name="s_" + str(i), var_type=BINARY) for i in range(n)]

    # Profit values.
    v_list = [boxes[i].get_profit() for i in range(n)]
    # Weights list.
    weights_list = [boxes[i].get_weight() for i in range(n)]
    priority_list = [boxes[i].get_priority() for i in range(n)]
    max_priority = max(priority_list)

    x_list = [m.add_var(name="x_" + str(i), lb=0) for i in range(n)]
    y_list = [m.add_var(name="y_" + str(i), lb=0) for i in range(n)]
    z_list = [m.add_var(name="z_" + str(i), lb=0) for i in range(n)]

    # parameters
    h_list = [box.size[0] for box in boxes]
    w_list = [box.size[1] for box in boxes]
    l_list = [box.size[2] for box in boxes]

    # Add objective functions
    # Maximize volume.
    m.objective = maximize(xsum(l_list[i] * w_list[i] * h_list[i] * s_list[i] for i in range(n)) / (L * W * H))
    # Maximize profit.
    m.objective = maximize(xsum(s_list[i] * v_list[i] for i in range(n)))
    # for all 0 < i < n : Max sum(si * (maxPriority + 1) - priority_i)
    m.objective = maximize(xsum((s_list[i] * ((max_priority + 1) - priority_list[i])) for i in range(n)))

    # Add constraints
    for i in range(n):
        m += (weights_list[i] * s_list[i]) <= container.weight
        m += x_list[i] + l_list[i] <= (L + M * (1 - s_list[i]))
        m += y_list[i] + w_list[i] <= (W + M * (1 - s_list[i]))
        m += z_list[i] + h_list[i] <= (H + M * (1 - s_list[i]))
        for j in range(i + 1, n):
            m += x_list[i] + l_list[i] <= (x_list[j] + M * (1 - m.var_by_name(f"a_{i}_{j}")))
            m += x_list[j] + l_list[j] <= (x_list[i] + M * (1 - m.var_by_name(f"b_{i}_{j}")))
            m += y_list[i] + w_list[i] <= (y_list[j] + M * (1 - m.var_by_name(f"c_{i}_{j}")))
            m += y_list[j] + w_list[j] <= (y_list[i] + M * (1 - m.var_by_name(f"d_{i}_{j}")))
            m += z_list[i] + h_list[i] <= (z_list[j] + M * (1 - m.var_by_name(f"e_{i}_{j}")))
            m += z_list[j] + h_list[j] <= (z_list[i] + M * (1 - m.var_by_name(f"f_{i}_{j}")))
            m += m.var_by_name(f"a_{i}_{j}") + m.var_by_name(f"b_{i}_{j}") + m.var_by_name(
                f"c_{i}_{j}") + m.var_by_name(f"d_{i}_{j}") + m.var_by_name(f"e_{i}_{j}") + m.var_by_name(
                f"f_{i}_{j}") >= (s_list[i] + s_list[j] - 1)
    m.max_gap = 0.05
    status = m.optimize(max_seconds=10000000000000000000)
    print('----- STATUS : ', status, '------')
    if status == OptimizationStatus.OPTIMAL:
        print('optimal solution cost {} found'.format(m.objective_value))
    elif status == OptimizationStatus.FEASIBLE:
        print('sol.cost {} found, best possible: {} '.format(m.objective_value, m.objective_bound))
    elif status == OptimizationStatus.NO_SOLUTION_FOUND:
        print('no feasible solution found, lower bound is: {} '.format(m.objective_bound))
    if status == OptimizationStatus.OPTIMAL or status == OptimizationStatus.FEASIBLE:
        print('solution:')
        for v in m.vars:
            # if abs(v.x) > 1e-6:  # only printing non-zeros
            print('{} : {} '.format(v.name, v.x))
