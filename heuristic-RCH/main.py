# the code is based on article: "An optimization approach for a complex real-life container loading problem"
# https://www.researchgate.net/publication/355421342_An_optimization_approach_for_a_complex_real-life_container_loading_problem


import random
import json
# TODO: from typing import Tuple
from definitions import Box, RotationType, CombinationType, Combination, SortingType, PerturbRotation, PerturbOrder


SKIP_COMBINE_PROBABILITY = 0.5
ALGORITHM_REPEAT_COUNT = 2


def chance(probability: float) -> bool:
    return random.random() < probability


def combine(a: Box, b: Box, common_dims: list[int]) -> list[Box]:
    amount_of_common_dims = len(common_dims)
    if amount_of_common_dims == 3:
        combination_type = random.choice(list(CombinationType))
    elif amount_of_common_dims == 2:
        if 0 in common_dims and 1 in common_dims:
            combination_type = random.choice([CombinationType.WH_LOWER, CombinationType.WH_HIGHER])
        elif 0 in common_dims and 2 in common_dims:
            combination_type = random.choice([CombinationType.WD_LOWER, CombinationType.WD_HIGHER])
        else:
            combination_type = random.choice([CombinationType.HD_LOWER, CombinationType.HD_HIGHER])

    combination = Combination(a, b, combination_type)
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
                combined_boxes.append(a, b)
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


def rotate(box: Box, rotation_type: RotationType = None) -> None:
    if rotation_type is None:
        rotation_type = random.choice(box.rotations)
    
    w, h, d = box.size
    if rotation_type == RotationType.X:
        box.size = (w, d, h)
    elif rotation_type == RotationType.Z:
        box.size = (h, w, d)
    elif rotation_type == RotationType.XZ:
        box.size = (h, d, w)
    elif rotation_type == RotationType.Y:
        box.size = (d, h, w)
    elif rotation_type == RotationType.XY:
        box.size = (d, w, h)


def perturb_phase1(boxes: list[Box]) -> None:
    # TODO: update possible rotations?
    perturb_rotation = random.choice(list(PerturbRotation))
    if perturb_rotation == PerturbRotation.INDIVIDUAL:
        for box in boxes:
            rotate(box)
    else: # IDENTICAL
        rotation_per_type = {}
        for box in boxes:
            if box.box_type not in rotation_per_type:
                rotation_per_type[box.box_type] = random.choice(box.rotations)
            rotate(box, rotation_per_type[box.box_type])


def perturb_phase2(boxes: list[Box]) -> None:
    perturb_rotation = random.choice(list(PerturbOrder))
    key = lambda box: box.volume if perturb_rotation == PerturbOrder.VOLUME else lambda box: box.weight
    for i in range(len(boxes) - 1):
        ratio = key(boxes[i]) / key(boxes[i + 1])
        if 0.7 <= ratio <= 1.3 and chance(0.5):
            boxes[i], boxes[i + 1] = boxes[i + 1], boxes[i]


# Randomized Constructive Heuristic
def rch(boxes: list[Box]):
    for _ in range(ALGORITHM_REPEAT_COUNT): # iteration n=1 to N
        # pre-process phase (section 4.2)
        if not chance(SKIP_COMBINE_PROBABILITY):
            boxes = preprocess_boxes(boxes)

        # sort/perturb phase (section 4.3)
        sort_boxes(boxes)
        perturb_phase1(boxes)
        perturb_phase2(boxes)

        # construct a solution (section 4.4)
    result = {}
    return result
    

def parse_input(input_data: bytearray):
    parsed_data = json.loads(input_data)
    return parsed_data


def pack(input_data):
    parsed_input = parse_input(input_data)
    result = rch(parsed_input)
    return result


def main():
    input_path = 'input.json'
    try:
        with open(input_path, 'r') as in_file:
            input_data = in_file.read()
            result = pack(input_data)
            print('finished', result)
    except Exception as e:
        print('received an exception', e)


if __name__ == '__main__':
    main()
