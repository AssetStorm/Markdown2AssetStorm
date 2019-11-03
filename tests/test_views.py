from converter import app, convert
import unittest
import json


class ConvertTestCase(unittest.TestCase):
    def test_two_paragaraps(self):
        markdown = "This is the text of paragraph 1.\n\nThis is the second text."
        response = convert(markdown)
        tree = json.loads(response.data)
        self.assertEqual(tree, {"type": "block-blocks", "blocks": [{
            "type": "block-paragraph",
            "spans": [{"type": "span-regular",
                       "text": "This is the text of paragraph 1."}]
        }, {
            "type": "block-paragraph",
            "spans": [{"type": "span-regular",
                       "text": "This is the second text."}]
        }]})


if __name__ == '__main__':
    unittest.main()
