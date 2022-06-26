from mip import *
import json
from Box import *


def parse_json_input(input_data, m):
    result = {}
    result['packages'] = []
    boxes = []
    s_list = []
    boxes_counter = 0
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

        width = package['width']
        height = package['height']
        depth = package['depth']
        package_size = (width, depth, height)
        package_type = package['type']
        rotations = [
            ((width, depth, height), (0, 0, 0)),
            ((width, height, depth), (90, 0, 0)),
            ((depth, width, height), (0, 0, 90)),
            ((height, width, depth), (90, 0, 90)),
            ((height, depth, width), (0, 90, 0)),
            ((depth, height, width), (90, 90, 0)),
        ]
        if canRotate:
            for i in range(package['amount']):
                for size, rot in rotations:
                    boxes += [
                        Box(
                            size=size,
                            id=f'{package_type}-{i}--{0}',
                            weight=weight,
                            priority=priority,
                            profit=profit,
                            rot=rot,
                            can_roat=canRotate,
                            can_down=canStackAbove,
                            nosort=True
                        )
                    ]

                for j in range(6):
                    s_list.append(m.add_var(name="s_" + str(boxes_counter), var_type=BINARY))
                    boxes_counter += 1

                m += xsum(s_list[boxes_counter - i - 1] for i in range(6)) <= 1



        else:
            boxes += [Box(size=package_size, id=f'{package_type}-{i}', weight=weight, priority=priority, profit=profit,
                          can_roat=canRotate, can_down=canStackAbove,
                          nosort=True) for i in range(package['amount'])]

            for i in range(package['amount']):
                s_list.append(m.add_var(name="s_" + str(boxes_counter), var_type=BINARY))
                boxes_counter += 1

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
    return result, container, boxes, s_list


def generateBox():
    fd = open('testdata.txt')
    cargo = []
    for line in fd:
        cargo = cargo + [Box(pack) for pack in line.strip().split()]
        # break
    return cargo


def update_result(result, n, s_list, boxes, x_list, y_list, z_list, total_weight, total_profit, total_usage,
                  weights_list, priority_list, l_list, w_list, h_list):
    for i in range(n):
        if s_list[i].x == 1.0:
            result['solution'].append({
                "type": boxes[i].ID.split('-')[0],
                'x': round(x_list[i].x),
                'y': round(y_list[i].x),
                'z': round(z_list[i].x),
                'rotation-x': boxes[i].rotX,
                'rotation-y': boxes[i].rotY,
                'rotation-z': boxes[i].rotZ,
            })
            total_weight += weights_list[i]
            total_profit += priority_list[i]
            total_usage += l_list[i] * w_list[i] * h_list[i]

            print(boxes[i].ID)
            print(x_list[i].x, y_list[i].x, z_list[i].x)


def update_stats(result, total_weight, total_usage, total_profit, L, H, W):

    result['stats'] = {
        'profit': total_profit,
        'weight': total_weight,

        'space_usage': total_usage / (L * H * W)
    }


def add_decision_vars(m, n, boxes):
    a_list = [m.add_var(name="a_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    b_list = [m.add_var(name="b_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    c_list = [m.add_var(name="c_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    d_list = [m.add_var(name="d_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]

    e_list = []
    # e_ij is a binary variable which is equal to 1 if box i is placed on the top of the box j.
    # If boxes[j].StackAbove == false --> for all i, e_ij = 0.

    for i in range(n):
        for j in range(i + 1, n):
            if not boxes[j].get_canStackAbove():
                m.add_var(name="e_" + str(i) + "_" + str(j), lb=0, ub=0)  # e_ij = 0
            else:
                m.add_var(name="e_" + str(i) + "_" + str(j), var_type=BINARY)  # e_ij binary

    f_list = [m.add_var(name="f_" + str(i) + "_" + str(j), var_type=BINARY) for i in range(n) for j in range(i + 1, n)]
    #  A binary variable which is equal to 1 if box i is placed in the container

    x_list = [m.add_var(name="x_" + str(i), lb=0) for i in range(n)]
    y_list = [m.add_var(name="y_" + str(i), lb=0) for i in range(n)]
    z_list = [m.add_var(name="z_" + str(i), lb=0) for i in range(n)]
    return x_list, y_list, z_list


def add_constrains(m, n, W, L, H, M, x_list, y_list, z_list, w_list, h_list, l_list, s_list, weights_list, container):
    # Add constraints
    for i in range(n):
        m += x_list[i] + w_list[i] <= (W + M * (1 - s_list[i]))
        m += y_list[i] + l_list[i] <= (L + M * (1 - s_list[i]))
        m += z_list[i] + h_list[i] <= (H + M * (1 - s_list[i]))
        for j in range(i + 1, n):
            m += x_list[i] + w_list[i] <= (x_list[j] + M * (1 - m.var_by_name(f"a_{i}_{j}")))
            m += x_list[j] + w_list[j] <= (x_list[i] + M * (1 - m.var_by_name(f"b_{i}_{j}")))
            m += y_list[i] + l_list[i] <= (y_list[j] + M * (1 - m.var_by_name(f"c_{i}_{j}")))
            m += y_list[j] + l_list[j] <= (y_list[i] + M * (1 - m.var_by_name(f"d_{i}_{j}")))
            m += z_list[i] + h_list[i] <= (z_list[j] + M * (1 - m.var_by_name(f"e_{i}_{j}")))
            m += z_list[j] + h_list[j] <= (z_list[i] + M * (1 - m.var_by_name(f"f_{i}_{j}")))

            m += m.var_by_name(f"a_{i}_{j}") + m.var_by_name(f"b_{i}_{j}") + m.var_by_name(
                f"c_{i}_{j}") + m.var_by_name(f"d_{i}_{j}") + m.var_by_name(f"e_{i}_{j}") + m.var_by_name(
                f"f_{i}_{j}") >= (s_list[i] + s_list[j] - 1)

    m += xsum(weights_list[i] * s_list[i] for i in range(n)) <= container.weight


def add_objectives(m, n, l_list, w_list, h_list, s_list, v_list, priority_list, max_priority):
    # Add objective functions
    # Maximize volume.
    m.objective = maximize(xsum(l_list[i] * w_list[i] * h_list[i] * s_list[i] for i in range(n)))
    # Maximize profit.
    m.objective.add_expr(maximize(xsum(s_list[i] * v_list[i] for i in range(n))), 1)
    # for all 0 < i < n : Max sum(si * (maxPriority + 1) - priority_i)
    m.objective.add_expr(maximize(xsum((s_list[i] * ((max_priority + 1) - priority_list[i])) for i in range(n))), 1)


def pack(json_data):
    # create the model
    m = Model("CLP")
    # Big M method
    M = 1e5

    # get the input form the json file
    try:
        result, container, boxes, s_list = parse_json_input(json_data, m)
        n = len(boxes)
    except Exception as e:
        print('received exception', e)
        exit(-1)

    # container sizes
    L, W, H = (container.length, container.width, container.heigth)
    print(f'L={L}, W={W}, H={H}')

    # add decision vars
    x_list, y_list, z_list = add_decision_vars(m, n, boxes)

    # parameters
    h_list = [box.size[0] for box in boxes]
    w_list = [box.size[1] for box in boxes]
    l_list = [box.size[2] for box in boxes]

    # Profit values.
    v_list = [boxes[i].get_profit() for i in range(n)]

    # Weights list.
    weights_list = [boxes[i].get_weight() for i in range(n)]
    priority_list = [boxes[i].get_priority() for i in range(n)]
    max_priority = max(priority_list)

    # Add objective functions
    add_objectives(m, n, l_list, w_list, h_list, s_list, v_list, priority_list, max_priority)

    # Add constraints
    add_constrains(m, n, W, L, H, M, x_list, y_list, z_list, w_list, h_list, l_list, s_list, weights_list, container)

    # optimize solution and print
    result['solution'] = []
    m.max_gap = 0.05
    status = m.optimize(max_seconds=500)
    print('----- STATUS : ', status, '------')
    if status == OptimizationStatus.OPTIMAL:
        print('optimal solution cost {} found'.format(m.objective_value))
    elif status == OptimizationStatus.FEASIBLE:
        print('sol.cost {} found, best possible: {} '.format(m.objective_value, m.objective_bound))
    elif status == OptimizationStatus.NO_SOLUTION_FOUND:
        print('no feasible solution found, lower bound is: {} '.format(m.objective_bound))
    if status == OptimizationStatus.OPTIMAL or status == OptimizationStatus.FEASIBLE:
        print('solution:')
        print("number of boxes inside the container ", sum([s_list[i].x for i in range(n)]))
        total_profit, total_weight, total_usage, total_space = 0, 0, 0, 0

        # update result and statics
        update_result(result, n, s_list, boxes, x_list, y_list, z_list, total_weight, total_profit, total_usage,
                      weights_list, priority_list, l_list, w_list, h_list)
        update_stats(result, total_weight, total_usage, total_profit, L, H, W)

        for v in m.vars:
            # if abs(v.x) > 1e-6:  # only printing non-zeros
            print('{} : {} '.format(v.name, v.x))
    return result


def pack_from_file():
    filepath = './input.json'
    with open(filepath, 'r') as json_file:
        raw_data = json_file.read()
        json_data = json.loads(raw_data)
        pack(json_data)


if __name__ == '__main__':
    pack_from_file()
