import unittest
from unittest.mock import patch
import src.User_Input.user_input as user_input


class UserInputTests(unittest.TestCase):
    @patch('src.User_Input.user_input.input', create=True)
    def test_get_titles_extra_spaces(self, mocked_input):
        print("test_get_titles")
        mocked_input.side_effect = ['       software       engineer   ', '']
        result = user_input.get_job_titles()
        self.assertEqual(result, ['software engineer'])

    @patch('src.User_Input.user_input.input', create=True)
    def test_get_titles_4_entries(self, mocked_input):
        mocked_input.side_effect = ['software engineer', 'associate software developer', 'sdet', 'qa engineer', '']
        result = user_input.get_job_titles()
        self.assertEqual(result, ['software engineer', 'associate software developer', 'sdet', 'qa engineer'])


if __name__ == '__main__':
    unittest.main()