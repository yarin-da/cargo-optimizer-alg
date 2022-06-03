import unittest
from definitions import *


def get_testing_box(size: Size, rotations: set(RotationType) = set(list(RotationType))) -> Box:
    return Box(
        'test',
        size,
        2,
        3,
        rotations,
        False
    )


class TestRotationMethods(unittest.TestCase):
    def test_point_removal(self):
        points = [Point(1, 2, 3), Point(3, 2, 1)]
        points.remove(Point(1, 2, 3))
        self.assertTrue(Point(3, 2, 1) in points)
        self.assertTrue(Point(1, 2, 3) not in points)
        self.assertTrue(len(points) == 1)

    def test_rotations_shallow(self):
        box = get_testing_box(Size(1, 2, 3))
        
        box.rotate(RotationType.NONE)
        self.assertEqual(box.size, Size(1, 2, 3))
        box.rotate(RotationType.X)
        self.assertEqual(box.size, Size(1, 3, 2))
        box.rotate(RotationType.Z)
        self.assertEqual(box.size, Size(3, 1, 2))
        box.rotate(RotationType.XZ)
        self.assertEqual(box.size, Size(1, 2, 3))
        box.rotate(RotationType.Y)
        self.assertEqual(box.size, Size(3, 2, 1))

    def test_rotations_compound(self):
        box_a = get_testing_box(Size(1, 2, 3))
        box_b = get_testing_box(Size(1, 2, 1))
        box = combine(box_a, box_b, box_a.get_common_dims(box_b), 'lower')
        box.set_position(Point(1, 1, 1))
        
        self.assertEqual(box.combination.combination_type, CombinationType.WD_LOWER)
        self.assertEqual(box.size, Size(1, 2, 4))
        self.assertEqual(box.combination.first.size, Size(1, 2, 3))
        self.assertEqual(box.combination.second.size, Size(1, 2, 1))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(1, 1, 4))

        box.rotate(RotationType.NONE)
        self.assertEqual(box.combination.combination_type, CombinationType.WD_LOWER)
        self.assertEqual(box.size, Size(1, 2, 4))
        self.assertEqual(box.combination.first.size, Size(1, 2, 3))
        self.assertEqual(box.combination.second.size, Size(1, 2, 1))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(1, 1, 4))

        box.rotate(RotationType.X)
        self.assertEqual(box.combination.combination_type, CombinationType.WH_LOWER)
        self.assertEqual(box.size, Size(1, 4, 2))
        self.assertEqual(box.combination.first.size, Size(1, 3, 2))
        self.assertEqual(box.combination.second.size, Size(1, 1, 2))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(1, 4, 1))

        box.rotate(RotationType.Z)
        self.assertEqual(box.combination.combination_type, CombinationType.HD_LOWER)
        self.assertEqual(box.size, Size(4, 1, 2))
        self.assertEqual(box.combination.first.size, Size(3, 1, 2))
        self.assertEqual(box.combination.second.size, Size(1, 1, 2))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(4, 1, 1))

        box.rotate(RotationType.XZ)
        self.assertEqual(box.combination.combination_type, CombinationType.WD_LOWER)
        self.assertEqual(box.size, Size(1, 2, 4))
        self.assertEqual(box.combination.first.size, Size(1, 2, 3))
        self.assertEqual(box.combination.second.size, Size(1, 2, 1))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(1, 1, 4))

        box.rotate(RotationType.Y)
        self.assertEqual(box.combination.combination_type, CombinationType.HD_LOWER)
        self.assertEqual(box.size, Size(4, 2, 1))
        self.assertEqual(box.combination.first.size, Size(3, 2, 1))
        self.assertEqual(box.combination.second.size, Size(1, 2, 1))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(4, 1, 1))

        box.rotate(RotationType.XY)
        self.assertEqual(box.combination.combination_type, CombinationType.WH_LOWER)
        self.assertEqual(box.size, Size(1, 4, 2))
        self.assertEqual(box.combination.first.size, Size(1, 3, 2))
        self.assertEqual(box.combination.second.size, Size(1, 1, 2))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(1, 4, 1))


if __name__ == '__main__':
    unittest.main()