# the code is based on article: "An optimization approach for a complex real-life container loading problem"
# https://www.researchgate.net/publication/355421342_An_optimization_approach_for_a_complex_real-life_container_loading_problem


import math
import copy
import traceback
import random
import json
from packing import *
from debug_utils import *


SKIP_COMBINE_PROBABILITY = 1
ALGORITHM_REPEAT_COUNT = 50
REORDER_PROBABILITY = 0.5
REORDER_RATIO_OFFSET = 0.3
REORDER_RATIO_LOWER_BOUND = 1 - REORDER_RATIO_OFFSET
REORDER_RATIO_HIGHER_BOUND = 1 + REORDER_RATIO_OFFSET


def chance(probability: float) -> bool: 
    return random.random() < probability


def preprocess_boxes(boxes: list[Box]) -> list[Box]:
    processed_boxes = []
    combined_boxes = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a = boxes[i]
            b = boxes[j]
            if not a.stackable or not b.stackable: continue
            if i == j or a in combined_boxes or b in combined_boxes: continue
            common_dims = a.get_common_dims(b)
            if len(common_dims) >= 2:
                # keep track of boxes that were combined (they'll be removed from the return value)
                combined_boxes.append(a)
                combined_boxes.append(b)
                # add the combination to processed_boxes
                processed_boxes.append(combine(a, b, common_dims))
    # add all boxes that were not combined to the return value
    processed_boxes.extend([box for box in boxes if box not in combined_boxes])

    return processed_boxes


def sort_boxes(boxes: list[Box], sorting_type: SortingType = None) -> None:
    if sorting_type is None:
        sorting_type = random.choice(list(SortingType))
    if sorting_type == SortingType.DECREASING_VOLUME:
        boxes.sort(key=lambda box: (2 if box.stackable else 1, box.size.volume(), box.priority, box.profit), reverse=True)
    elif sorting_type == SortingType.DECREASING_PRIORITY:
        boxes.sort(key=lambda box: (2 if box.stackable else 1, box.priority, box.size.volume()), reverse=True)
    elif sorting_type == SortingType.DECREASING_PROFIT:
        boxes.sort(key=lambda box: (2 if box.stackable else 1, box.profit, box.priority, box.size.volume()), reverse=True)
    else:
        boxes.sort(key=lambda box: (2 if box.stackable else 1, box.customer_code, box.size.volume()), reverse=True)


def perturb_phase1(boxes: list[Box]) -> None:
    perturb_rotation = random.choice(list(PerturbRotation))
    if perturb_rotation == PerturbRotation.INDIVIDUAL:
        for box in boxes: box.rotate()
    else: # IDENTICAL
        rotation_per_type = {}
        for box in boxes:
            if box.box_type not in rotation_per_type:
                rotation_per_type[box.box_type] = random.choice(list(box.rotations))
            box.rotate(rotation_per_type[box.box_type])


def perturb_phase2(boxes: list[Box]) -> None:
    perturb_rotation = random.choice(list(PerturbOrder))
    for i in range(len(boxes) - 1):
        key_curr = boxes[i].size.volume() if perturb_rotation == PerturbOrder.VOLUME else boxes[i].weight
        key_next = boxes[i + 1].size.volume() if perturb_rotation == PerturbOrder.VOLUME else boxes[i + 1].weight
        ratio = key_curr / key_next
        if REORDER_RATIO_LOWER_BOUND <= ratio <= REORDER_RATIO_HIGHER_BOUND and chance(REORDER_PROBABILITY):
            boxes[i], boxes[i + 1] = boxes[i + 1], boxes[i]


# returns True iff a is "better" than b
def is_better_fit_point(
    a: Point,
    b: Point,
    box: Box,
    packing: Packing
) -> bool:
    if b is None: return True
    a_floating = 1 - packing.get_support_score(box, a)
    b_floating = 1 - packing.get_support_score(box, b)
    a_stack_score = a.z if box.stackable else 0
    b_stack_score = b.z if box.stackable else 0
    return (a_floating, a_stack_score, a.x) < (b_floating, b_stack_score, b.x)


def find_best_point(box: Box, potential_points: list[Point], packing: Packing) -> Point:
    best_point = None
    for point in potential_points:
        if packing.can_be_added(box, point) and is_better_fit_point(point, best_point, box, packing):
            best_point = point
    return best_point


def is_feasible(packing: Packing) -> bool:
    return True


# Algorithm 2
# Constructive Packing Phase of RCH
def construct_packing(boxes: list[Box], container: Container) -> Packing:
    potential_points = [Point(0, 0, 0), Point(container.size.w, 0, 0)] # P = {BLF, BRF}
    retry_list = []
    packing = Packing(container)
    
    for box in boxes: # foreach item i in L
        best_point = find_best_point(box, potential_points, packing)
        if best_point is not None:
            box.set_position(best_point)
            packing.add(box, best_point, potential_points)
        else:
            # The insertion of box has failed
            retry_list.append(box)
    
    # print_debug(f'construct_packing:: boxes={len(boxes)} retry_list={len(retry_list)}')
   
    for box in retry_list:
        box.rotate()
        best_point = find_best_point(box, potential_points, packing)
        if best_point is not None:
            box.set_position(best_point)
            packing.add(box, best_point, potential_points)
    
    return packing


# Algorithm 1
# Randomized Constructive Heuristic
def rch(packing_input: PackingInput) -> PackingResult:
    input_container = packing_input.container
    input_boxes = packing_input.boxes
    best_packing = None
    for i in range(ALGORITHM_REPEAT_COUNT): # iteration n=1 to N
        container = copy.deepcopy(input_container)
        boxes = copy.deepcopy(input_boxes)

        # pre-process phase (section 4.2)
        if not chance(SKIP_COMBINE_PROBABILITY):
            boxes = preprocess_boxes(boxes)

        # sort/perturb phase (section 4.3)
        sort_boxes(boxes)
        perturb_phase1(boxes)
        perturb_phase2(boxes)

        # construct a solution (section 4.4)
        packing = construct_packing(boxes, container)
        if is_feasible(packing) and packing.is_better_than(best_packing):
            best_packing = packing
        ratio = best_packing.used_space_ratio()
        print_debug(f'[{i}/{ALGORITHM_REPEAT_COUNT}] best_packing::used_volume {ratio}\r')
        # have we already finished?
        if ratio == 1 or len(best_packing.boxes) == len(boxes): break

    print_debug(best_packing.get_stats(packing_input))
    result = PackingResult(packing_input=packing_input, packing=best_packing)
    return result
    

def parse_input(input_data: bytearray):
    parsed_data = json.loads(input_data)
    return parsed_data


def get_scalar(input_data) -> int:
    c = input_data['container']
    scalars = []
    for dim in ['width', 'depth', 'height']:
        dim_list = list(map(lambda x: x[dim], input_data['packages']))
        dim_list.append(c[dim])
        scalars.append(math.gcd(*dim_list))
    scalar = min(*scalars)
    return scalar


def scale_input(input_data, scalar) -> None:
    if scalar == 1: return
    c = input_data['container']
    for dim in ['width', 'depth', 'height']:
        for pkg in input_data['packages']:
            pkg[dim] //= scalar
        c[dim] //= scalar


def pack(input_data):
    result_json = None
    try:
        scalar = get_scalar(input_data)
        scale_input(input_data, scalar)
        packing_input = PackingInput(input_data, scalar)
        result = rch(packing_input)
        result_json = result.to_json()
    except Exception as e:
        result = PackingResult(error=f'Exception: {e}')
        print('EXCEPTION')
        print(traceback.format_exc())
        print(e)
    return result_json


def write_result_to_file(result):
    with open('./heuristic-rch/output.json', 'w') as out_file:
        out_file.write(result)


def main():
    input_path = './heuristic-rch/input.json'
    try:
        with open(input_path, 'r') as in_file:
            input_data = in_file.read()
            parsed_input = parse_input(input_data)
            result = pack(parsed_input)
            result_string = json.dumps(result, indent=2, sort_keys=False)
            write_result_to_file(result_string)
            print('finished!')
    except Exception as e:
        print('received an exception', e)
        traceback.print_exc()


if __name__ == '__main__':
    main()
