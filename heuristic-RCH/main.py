# code based on article:
# https://www.researchgate.net/publication/355421342_An_optimization_approach_for_a_complex_real-life_container_loading_problem


import random
from definitions import Box, CombinationType, Combination, SortingType


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
    sorting_type = random.choice(SortingType)
    if sorting_type == SortingType.DECREASING_TAXABILITY:
        boxes.sort(key=lambda box: box.taxability, reverse=True)
    elif sorting_type == SortingType.DECREASING_PRIORITY:
        boxes.sort(key=lambda box: (box.priority, box.taxability), reverse=True)
    else:
        boxes.sort(key=lambda box: (box.customer_code, box.taxability), reverse=True)


# Randomized Constructive Heuristic
def rch(boxes: list[Box]):
    for _ in range(ALGORITHM_REPEAT_COUNT): # iteration n=1 to N
        # pre-process phase (section 4.2)
        if not chance(SKIP_COMBINE_PROBABILITY):
            boxes = preprocess_boxes(boxes)

        # sorting phase (section 4.3)
        sort_boxes(boxes)

    return None
    

def parse_input(input_data: bytearray):
    # TODO: parse data file to json object
    return input_data


def parse_result(output_data):
    # TODO: parse result
    return output_data


def pack(input_data):
    parsed_input = parse_input(input_data)
    result = rch(parsed_input)
    parsed_result = parse_result(result)
    return parsed_result


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
