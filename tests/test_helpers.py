import unittest
from helpers import consume_str, json_from_markdown


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

    def test_conversion(self):
        markdown = '''
Heading
=======

This is text with **important** content. It needs to be *blockwise emphasized* 
and even ***strong and emphasized***. It contains `inline code` and a 
[link](https://www.markdownguide.org "Link with alternate text").

## smaller Heading

![This is the caption for an image.](https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Cscr-featured.png/50px-Cscr-featured.png)

The text continues below the second heading.

```python
import json
print(
  json.dumps({"key": "value"})
)
```

Not only listings can be embedded. Citations are pretty interesting too:

> This is a citation
> 
> which spans over two blocks.

After that the text continues a usual.
'''
        tree = json_from_markdown(markdown)
        print(tree)


if __name__ == '__main__':
    unittest.main()
