import pyshipping.package as ship
from scipy.optimize import linprog
from mip import *
from Box import Box


# class Box(ship.Package):
#     def __init__(self, size, id=0, can_roat=True, can_down=True, priority=0, weight=0, nosort=False):
#         super().__init__(size, weight, nosort)
#         self.ID = id
#         self.can_roat = can_roat
#         self.can_down = can_down
#         self.priority = priority


class Container(ship.Package):
    def __init__(self, size, id):
        super(Container, self).__init__(size)
        self.id = id


def generateBox():
    fd = open('testdata.txt')
    cargo = []
    for line in fd:
        cargo = cargo + [Box(pack) for pack in line.strip().split()]
        # break
    return cargo


if __name__ == '__main__':
    m = Model("CLP")
    M = 1e7

    L, W, H = (600, 200, 200)
    boxes = generateBox()
    n = len(boxes)
    # add decision variables
    a_list = [m.add_var(name="a_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    b_list = [m.add_var(name="b_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    c_list = [m.add_var(name="c_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    d_list = [m.add_var(name="d_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    e_list = [m.add_var(name="e_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    f_list = [m.add_var(name="f_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    s_list = [m.add_var(name="s_" + str(i), var_type=BINARY) for i in range(n)]

    x_list = [m.add_var(name="x_" + str(i), lb=0) for i in range(n)]
    y_list = [m.add_var(name="y_" + str(i), lb=0) for i in range(n)]
    z_list = [m.add_var(name="z_" + str(i), lb=0) for i in range(n)]

    # parameters
    l_list = [box.length for box in boxes]
    w_list = [box.width for box in boxes]
    h_list = [box.heigth for box in boxes]

    # add objective functions
    m.objective = maximize(xsum(l_list[i] * w_list[i] * h_list[i] * s_list[i] for i in range(n)) / (L * W * H))

    # add constrains
    for i in range(n):
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
                f"c_{i}_{j}") + m.var_by_name(f"d_{i}_{j}") + m.var_by_name(f"e_{i}_{j}") + \
                 m.var_by_name(f"f_{i}_{j}") >= (s_list[i] + s_list[j] - 1)
    m.max_gap = 0.05
    status = m.optimize(max_seconds=200)
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
