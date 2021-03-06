from rch_types import *
from rch_used_space import *
from util import *
from box import *


class Packing:
    def __init__(self, container: Container):
        self.container = container
        self.boxes = []
        self.total_weight = 0
        self.total_priority = 0
        self.total_profit = 0
        self.used_space = UsedSpace(container.size)

    def add(self, box: Box, point: Point, potential_points: list[Point]) -> None:
        self.boxes.append(box)
        self.total_weight += box.weight
        self.total_profit += box.profit
        self.total_priority += box.priority
        self.used_space.add(box, point)

        potential_points.remove(point)

        corner_w = (point[0] + box.size[0], point[1], point[2])
        projected_corner_w = self.used_space.vertical_projection(corner_w)
        if projected_corner_w is not None:
            potential_points.append(projected_corner_w)

        corner_d = (point[0], point[1] + box.size[1], point[2])
        projected_corner_d = self.used_space.vertical_projection(corner_d)
        if projected_corner_d is not None:
            potential_points.append(projected_corner_d)

        corner_h = (point[0], point[1], point[2] + box.size[2])
        projected_corner_h = self.used_space.vertical_projection(corner_h)
        if projected_corner_h is not None:
            potential_points.append(projected_corner_h)

    def can_be_added(self, box: Box, point: Point) -> bool:
        # does the box exceed the container weight limit
        new_total_weight = box.weight + self.total_weight
        if new_total_weight > self.container.weight_limit:
            return False
        
        # does the box exceed the container boundaries
        corner = (point[0] + box.size[0], point[1] + box.size[1], point[2] + box.size[2])
        if corner[0] > self.container.size[0] or corner[1] > self.container.size[1] or corner[2] > self.container.size[2]:
            return False

        # does the box overlap another box
        if not self.used_space.can_be_added(box, point):
            return False
        
        return True

    def get_support_score(self, box: Box, point: Point) -> float:
        real_boxes = box.get_all_real_boxes()
        floating_scores = [self.used_space.get_support_score(b, point) for b in real_boxes]
        return min(floating_scores)

    def is_better_than(self, other: Packing, preference: str = 'volume') -> bool:
        if other is None: return True
        
        # comparators that return True iff self is better than other
        def cmp_space(self, other):
            self_unused_ratio = 1 - self.used_space.ratio()
            other_unused_ratio = 1 - other.used_space.ratio()
            return self_unused_ratio < other_unused_ratio
        def cmp_profit(self, other):   return self.total_profit > other.total_profit
        def cmp_priority(self, other): return self.total_priority > other.total_priority

        if preference == 'profit':   return cmp_profit(self, other)
        if preference == 'priority': return cmp_priority(self, other)
        return cmp_space(self, other)
        
    def unfloat(self):
        for box in self.boxes: self.used_space.unfloat(box)

    def used_space_ratio(self) -> float: return self.used_space.ratio()

    def box_usage(self, packing_input: PackingInput):
        used_boxes = {}
        for block in self.boxes:
            for box in block.get_all_real_boxes():
                if box.box_type not in used_boxes: used_boxes[box.box_type] = { 'used': 0, 'total': 0 }
            used_boxes[box.box_type]['used'] += 1
        for box in packing_input.original_json['packages']: 
            if box['type'] in used_boxes:
                used_boxes[box['type']]['total'] = box['amount']
        return used_boxes

    def get_stats(self, packing_input: PackingInput):
        space_str = f'Space used: {self.used_space_ratio()}'
        profit_str = f'Total profit: {self.total_profit}'
        used_boxes = self.box_usage(packing_input)
        box_usage_str = '\n'.join([f'{key}: [{used_boxes[key]["used"]}/{used_boxes[key]["total"]}]' for key in used_boxes.keys()])
        return '\n'.join([space_str, profit_str, box_usage_str])


class PackingInput:
    def __init__(self, json_data, scalar):
        self.original_json = json_data
        self.scalar = scalar
        self.preference = json_data['preference'] if 'preference' in json_data else 'volume'
        # init container
        container = json_data['container']
        container_size = (container['width'], container['depth'], container['height'])
        self.container = Container(container_size, container['maxWeight'])
        
        # init boxes
        self.boxes = []
        packages = json_data['packages']
        for pkg in packages:
            # convert input to correct types (incase we get json where 'width' is a string for example)
            amount = int(pkg['amount'])
            canRotate = pkg['canRotate'] if type(pkg['canRotate']) == bool else pkg['canRotate'].lower() == 'true'
            canStackAbove = pkg['canStackAbove'] if type(pkg['canStackAbove']) == bool else pkg['canStackAbove'].lower() == 'true'
            width, depth, height = int(pkg['width']), int(pkg['depth']), int(pkg['height'])
            priority = int(pkg['priority'])
            weight = int(pkg['weight'])
            for _ in range(amount):
                box = Box(
                    box_type=pkg['type'],
                    size=(width, depth, height),
                    weight=weight,
                    profit=float(pkg['profit']),
                    priority=priority,
                    rotations=set(list(RotationType)) if canRotate else set([RotationType.NONE]),
                    stackable=canStackAbove,
                    combination=None,
                    customer_code=1
                )
                self.boxes.append(box)


class PackingResult:
    def __init__(self, error: str = None, packing_input: PackingInput = None, packing: Packing = None):
        self.error = error
        self.packing = packing
        self.packing_input = packing_input  

    def to_json(self):
        json_data = {}
        if self.error is not None:
            json_data['error'] = self.error
            return json_data

        if self.packing is not None:
            container_size = self.packing.container.size
            json_data['container'] = {
                "width": int(container_size[0]),
                "depth": int(container_size[1]),
                "height": int(container_size[2]),
                "maxWeight": float(self.packing_input.container.weight_limit)
            }
            
            packages = self.packing_input.original_json['packages']
            json_data['packages'] = []
            for pkg in packages:
                json_data['packages'].append({
                    "type": pkg['type'],
                    "width": int(pkg['width']),
                    "height": int(pkg['height']),
                    "depth": int(pkg['depth'])
                })
            
            json_data['solution'] = []
            boxes = self.packing.boxes
            
            ids = []
            dup_count = 0

            for block in boxes:
                real_boxes = block.get_all_real_boxes()
                for box in real_boxes:
                    if id(box) not in ids:
                        ids.append(id(box))
                    else:
                        dup_count += 1
                    rotation = to_rotation3d(box.rotation_type)
                    box_type = box.box_type
                    json_data['solution'].append({
                        "type": box_type,
                        "x": box.position[0],
                        "y": box.position[1],
                        "z": box.position[2],
                        "rotation-x": rotation.x,
                        "rotation-y": rotation.y, 
                        "rotation-z": rotation.z
                    })
            assert_debug(dup_count == 0)
        
        json_data['stats'] = {
            'profit': self.packing.total_profit,
            'weight': self.packing.total_weight,
            'box_usage': self.packing.box_usage(self.packing_input),
            'space_usage': self.packing.used_space_ratio()
        }

        json_data['scalar'] = self.packing_input.scalar
        return json_data

