# the code is based on article: "An optimization approach for a complex real-life container loading problem"
# https://www.researchgate.net/publication/355421342_An_optimization_approach_for_a_complex_real-life_container_loading_problem


import copy
import traceback
import random
import json
from definitions import *


# TODO: handle floating number values (round up/down)
# TODO: Packing list order matters? i.e. order of packing (Algorithm 2 output)


SKIP_COMBINE_PROBABILITY = 0.5
# TODO: (4.5): "N is potentially a large number to the order of hundreds of thousands"
ALGORITHM_REPEAT_COUNT = 1
REORDER_PROBABILITY = 0.5
REORDER_RATIO_OFFSET = 0.3
REORDER_RATIO_LOWER_BOUND = 1 - REORDER_RATIO_OFFSET
REORDER_RATIO_HIGHER_BOUND = 1 + REORDER_RATIO_OFFSET


def chance(probability: float) -> bool:
    return random.random() < probability


def combine(a: Box, b: Box, common_dims: list[int]) -> list[Box]:
    amount_of_common_dims = len(common_dims)
    if amount_of_common_dims == 3:
        combination_type = random.choice(list(CombinationType))
    elif amount_of_common_dims == 2:
        if 'w' in common_dims and 'h' in common_dims:
            combination_type = random.choice([CombinationType.WH_LOWER, CombinationType.WH_HIGHER])
        elif 'w' in common_dims and 'd' in common_dims:
            combination_type = random.choice([CombinationType.WD_LOWER, CombinationType.WD_HIGHER])
        else:
            combination_type = random.choice([CombinationType.HD_LOWER, CombinationType.HD_HIGHER])

    if combination_type in [CombinationType.WH_LOWER, CombinationType.WD_LOWER, CombinationType.HD_LOWER]:
        combination = Combination(a, b, combination_type)
    else: 
        combination = Combination(b, a, combination_type)
    return Box.from_boxes(combination)


def preprocess_boxes(boxes: list[Box]) -> list[Box]:
    processed_boxes = []
    combined_boxes = []
    iterable = reversed(range(len(boxes)))
    for i in iterable:
        for j in iterable:
            if i == j:
                continue
            a = boxes[i]
            b = boxes[j]
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


def sort_boxes(boxes: list[Box]) -> None:
    sorting_type = random.choice(list(SortingType))
    if sorting_type == SortingType.DECREASING_TAXABILITY:
        boxes.sort(key=lambda box: box.taxability, reverse=True)
    elif sorting_type == SortingType.DECREASING_PRIORITY:
        boxes.sort(key=lambda box: (box.priority, box.taxability), reverse=True)
    else:
        boxes.sort(key=lambda box: (box.customer_code, box.taxability), reverse=True)


def perturb_phase1(boxes: list[Box]) -> None:
    # TODO: update possible rotations?
    perturb_rotation = random.choice(list(PerturbRotation))
    if perturb_rotation == PerturbRotation.INDIVIDUAL:
        for box in boxes:
            box.rotate()
    else: # IDENTICAL
        rotation_per_type = {}
        for box in boxes:
            if box.box_type not in rotation_per_type:
                rotation_per_type[box.box_type] = random.choice(list(box.rotations))
            box.rotate(rotation_per_type[box.box_type])


def perturb_phase2(boxes: list[Box]) -> None:
    perturb_rotation = random.choice(list(PerturbOrder))
    for i in range(len(boxes) - 1):
        key_curr = boxes[i].volume if perturb_rotation == PerturbOrder.VOLUME else boxes[i].weight
        key_next = boxes[i + 1].volume if perturb_rotation == PerturbOrder.VOLUME else boxes[i + 1].weight
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
    # TODO: better fit point
    #    i.e. best_point is None OR larger proportion of the contact surface with the underlying item is used
    #    FALL BACK to x value comparison (in case of tie)
    if b is None: return True
    diff = packing.get_support_score(box, a) - packing.get_support_score(box, b)
    if diff > 0: return True
    if diff < 0: return False
    return a.x < b.x


def find_best_point(box: Box, potential_points: list[Point], packing: Packing) -> Point:
    best_point = None
    for point in potential_points:
        if packing.can_be_added(box, point) and is_better_fit_point(point, best_point, box, packing):
            best_point = point
    return best_point


# Algorithm 2
# Constructive Packing Phase of RCH
def construct_packing(boxes: list[Box], container: Container) -> Packing:
    potential_points = [Point(0, 0, 0), Point(container.size.w, 0, 0)] # P = {BLF, BRF}
    retry_list = []
    packing = Packing(container)
    
    for box in boxes: # foreach item i in L
        best_point = find_best_point(box, potential_points, packing)
        if best_point is not None:
            packing.add(box, best_point, potential_points)
        else:
            # The insertion of box has failed
            retry_list.append(box)
    
    print_debug(f'construct_packing:: boxes={len(boxes)} retry_list={len(retry_list)}')
   
    for box in retry_list:
        box.rotate()
        best_point = find_best_point(box, potential_points, packing)
        if best_point is not None:
            packing.add(box, best_point, potential_points)
    
    return packing


# Algorithm 1
# Randomized Constructive Heuristic
def rch(packing_input: PackingInput) -> PackingResult:
    input_container = packing_input.container
    input_boxes = packing_input.boxes
    packing_options = []
    for _ in range(ALGORITHM_REPEAT_COUNT): # iteration n=1 to N
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
        packing_options.append(packing)

        # TODO: check if packing is infeasible

    # TODO: return all packings
    result = PackingResult(packing_input=packing_input, packing=packing_options[0])
    return result
    

def parse_input(input_data: bytearray):
    parsed_data = json.loads(input_data)
    return parsed_data


def pack(input_data):
    result = {}
    try:
        packing_input = PackingInput(input_data)
        result = rch(packing_input)
    except Exception as e:
        result = PackingResult(error=f'Exception: {e}')
        # TODO: remove
        raise e
    return result.to_json()


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
