#!/bin/env python
import unittest


class SampleTest(unittest.TestCase):
    def test_sample(self):
        self.assertEqual("test", "test")
