import unittest
import main as main_file


class TestMessage:
    def __init__(self):
        self.text = ''


class UserTest(unittest.TestCase):
    def test_is_correct_message(self):
        m = TestMessage()

        m.text = 'ололол'
        self.assertFalse(main_file.is_correct_message(m))

        m.text = 'надоело всё'
        self.assertFalse(main_file.is_correct_message(m))

        m.text = 'Москва сегодня'
        self.assertTrue(main_file.is_correct_message(m))


if __name__ == '__main__':
    unittest.main()
