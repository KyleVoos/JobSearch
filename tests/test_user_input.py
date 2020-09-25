import unittest
from unittest.mock import patch, MagicMock
import src.User_Input.user_input as user_input
from src.User_Input.user_input import InputData


class UserInputTests(unittest.TestCase):
    def setUp(self):
        self.input_data = InputData()

    @patch.multiple('src.User_Input.user_input', get_job_titles=MagicMock(return_value=['junior software engineer']),
                    get_locations=MagicMock(return_value=['portland']), get_title_filters=MagicMock(return_value=[]))
    def test_get_user_input(self):
        result = user_input.get_user_input()
        self.assertEqual(result.get_job_titles(), ['junior software engineer'])
        self.assertEqual(result.get_locations(), ['portland'])
        self.assertEqual(result.get_title_filters(), [])

    @patch('src.User_Input.user_input.input', create=True)
    def test_get_search_filters(self, mocked_input):
        mocked_input.side_effect = ['y', '3', 'y', '4']
        user_input.get_search_filters('portland', self.input_data)
        self.assertDictEqual(self.input_data.get_search_filter(key='portland'),
                             {'l': 'portland', 'fromage': 7, 'radius': 15})
        mocked_input.side_effect = ['n']
        user_input.get_search_filters('seattle', self.input_data)
        self.assertDictEqual(self.input_data.search_filters,
                             {'portland': {'l': 'portland', 'fromage': 7, 'radius': 15}, 'seattle': {'l': 'seattle'}})

    @patch('src.User_Input.user_input.input', create=True)
    def test_get_titles_extra_spaces(self, mocked_input):
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
