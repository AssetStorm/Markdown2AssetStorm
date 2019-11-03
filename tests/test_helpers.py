import unittest
from helpers import consume_str, json_from_markdown
import os


class TestPandocStringConsumer(unittest.TestCase):
    def test_single_string(self):
        string, rest = consume_str([
            {'t': 'Str', 'c': 'Foo.'}
        ])
        self.assertEquals("Foo.", string)
        self.assertEquals([], rest)

    def test_only_text(self):
        string, rest = consume_str([
            {'t': 'Str', 'c': 'Einleitungstext'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'mit'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'mehreren'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'Wörtern.'}
        ])
        self.assertEquals("Einleitungstext mit mehreren Wörtern.", string)
        self.assertEquals([], rest)

    def test_strong_in_the_middle(self):
        string, rest = consume_str([
            {'t': 'Str', 'c': 'Foo'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'is'},
            {'t': 'Space'},
            {'t': 'Strong', 'c': [{'t': 'Str', 'c': 'very'}, {'t': 'Space'}, {'t': 'Str', 'c': 'bar.'}]},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'Second'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'sentence.'}
        ])
        self.assertEquals("Foo is ", string)
        self.assertEquals([
            {'t': 'Strong', 'c': [{'t': 'Str', 'c': 'very'}, {'t': 'Space'}, {'t': 'Str', 'c': 'bar.'}]},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'Second'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'sentence.'}], rest)

    def test_beginning_with_strong(self):
        string, rest = consume_str([
            {'t': 'Strong', 'c': [{'t': 'Str', 'c': 'Strong'}, {'t': 'Space'}, {'t': 'Str', 'c': 'foo.'}]},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'Second'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'sentence.'}
        ])
        self.assertEquals("", string)
        self.assertEquals([
            {'t': 'Strong', 'c': [{'t': 'Str', 'c': 'Strong'}, {'t': 'Space'}, {'t': 'Str', 'c': 'foo.'}]},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'Second'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'sentence.'}], rest)


class TestPandocMarkdownConverter(unittest.TestCase):
    fixtures = ['span_assets.yaml', 'caption-span_assets.yaml', 'block_assets.yaml', 'table.yaml']

    def test_two_paragaraps(self):
        markdown = "This is the text of paragraph 1.\n\nThis is the second text."
        list = json_from_markdown(markdown)
        self.assertEqual(list, [{
            "type": "block-paragraph",
            "spans": [{"type": "span-regular",
                       "text": "This is the text of paragraph 1."}]
        }, {
            "type": "block-paragraph",
            "spans": [{"type": "span-regular",
                       "text": "This is the second text."}]
        }])

    def test_conversion(self):
        with open(os.path.join(
                os.path.abspath(os.curdir),
                "tests" if os.path.abspath(os.curdir).split(os.path.sep)[-1] != "tests" else "",
                "mixed_document.md"), 'r') as md_file:
            markdown = md_file.read()
        tree = json_from_markdown(markdown)
        #print(json.dumps(tree, indent=2))


if __name__ == '__main__':
    unittest.main()
