import unittest
from rch_types import *
from rch import combine


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
    def test_rotations(self):
        size = (0, 1, 2)
        self.assertEqual(RotationType.NONE.permute(size), (0, 1, 2))
        self.assertEqual(RotationType.W.permute(size),    (0, 2, 1))
        self.assertEqual(RotationType.H.permute(size),    (1, 0, 2))
        self.assertEqual(RotationType.WH.permute(size),   (2, 0, 1))
        self.assertEqual(RotationType.D.permute(size),    (2, 1, 0))
        self.assertEqual(RotationType.WD.permute(size),   (1, 2, 0))

    def test_point_removal(self):
        points = [Point(1, 2, 3), Point(3, 2, 1)]
        points.remove(Point(1, 2, 3))
        self.assertTrue(Point(3, 2, 1) in points)
        self.assertTrue(Point(1, 2, 3) not in points)
        self.assertTrue(len(points) == 1)

    def test_rotations_shallow(self):
        box = get_testing_box(Size((1, 2, 3)))

        box.rotate(RotationType.NONE)
        self.assertEqual(box.size, Size((1, 2, 3)))
        box.rotate(RotationType.W)
        self.assertEqual(box.size, Size((1, 3, 2)))
        box.rotate(RotationType.H)
        self.assertEqual(box.size, Size((3, 1, 2)))
        box.rotate(RotationType.WH)
        self.assertEqual(box.size, Size((2, 3, 1)))
        box.rotate(RotationType.D)
        self.assertEqual(box.size, Size((1, 3, 2)))

    def test_rotations_compound(self):
        box_a = get_testing_box(Size((1, 2, 3)))
        box_b = get_testing_box(Size((1, 2, 1)))
        box = combine(box_a, box_b, box_a.get_common_dims(box_b), 'lower')
        box.set_position(Point(1, 1, 1))
        
        self.assertEqual(box.combination.combination_type, CombinationType.WD_LOWER)
        self.assertEqual(box.size, Size((1, 2, 4)))
        self.assertEqual(box.combination.first.size, Size((1, 2, 3)))
        self.assertEqual(box.combination.second.size, Size((1, 2, 1)))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(1, 1, 4))

        box.rotate(RotationType.NONE)
        self.assertEqual(box.combination.combination_type, CombinationType.WD_LOWER)
        self.assertEqual(box.size, Size((1, 2, 4)))
        self.assertEqual(box.combination.first.size, Size((1, 2, 3)))
        self.assertEqual(box.combination.second.size, Size((1, 2, 1)))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(1, 1, 4))

        box.rotate(RotationType.W)
        self.assertEqual(box.combination.combination_type, CombinationType.WH_LOWER)
        self.assertEqual(box.size, Size((1, 4, 2)))
        self.assertEqual(box.combination.first.size, Size((1, 3, 2)))
        self.assertEqual(box.combination.second.size, Size((1, 1, 2)))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(1, 4, 1))

        box.rotate(RotationType.H)
        self.assertEqual(box.combination.combination_type, CombinationType.HD_LOWER)
        self.assertEqual(box.size, Size((4, 1, 2)))
        self.assertEqual(box.combination.first.size, Size((3, 1, 2)))
        self.assertEqual(box.combination.second.size, Size((1, 1, 2)))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(4, 1, 1))

        box.rotate(RotationType.WH)
        self.assertEqual(box.combination.combination_type, CombinationType.WH_LOWER)
        self.assertEqual(box.size, Size((2, 4, 1)))
        self.assertEqual(box.combination.first.size, Size((2, 3, 1)))
        self.assertEqual(box.combination.second.size, Size((2, 1, 1)))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(1, 4, 1))

        box.rotate(RotationType.D)
        self.assertEqual(box.combination.combination_type, CombinationType.WH_LOWER)
        self.assertEqual(box.size, Size((1, 4, 2)))
        self.assertEqual(box.combination.first.size, Size((1, 3, 2)))
        self.assertEqual(box.combination.second.size, Size((1, 1, 2)))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(1, 4, 1))

        box.rotate(RotationType.WD)
        self.assertEqual(box.combination.combination_type, CombinationType.HD_LOWER)
        self.assertEqual(box.size, Size((4, 2, 1)))
        self.assertEqual(box.combination.first.size, Size((3, 2, 1)))
        self.assertEqual(box.combination.second.size, Size((1, 2, 1)))
        self.assertEqual(box.position, Point(1, 1, 1))
        self.assertEqual(box.combination.first.position, Point(1, 1, 1))
        self.assertEqual(box.combination.second.position, Point(4, 1, 1))


if __name__ == '__main__':
    unittest.main()