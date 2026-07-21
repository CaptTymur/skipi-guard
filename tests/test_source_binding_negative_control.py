import unittest


class SourceBindingNegativeControlTest(unittest.TestCase):
    def test_guard_check_is_intentionally_non_success(self):
        self.fail("intentional source-binding negative control")


if __name__ == "__main__":
    unittest.main()
