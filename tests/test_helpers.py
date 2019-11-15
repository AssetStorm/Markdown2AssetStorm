import unittest
from helpers import convert_list, json_from_markdown
import os
import json


class TestPandocStringConverter(unittest.TestCase):
    def test_single_string(self):
        tree = convert_list([
            {'t': 'Str', 'c': 'Foo.'}
        ], [])
        self.assertEqual(tree, [{
            "type": "span-regular",
            "text": "Foo."
        }])

    def test_only_text(self):
        tree = convert_list([
            {'t': 'Str', 'c': 'Einleitungstext'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'mit'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'mehreren'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'Wörtern.'}
        ], [])
        self.assertEqual(tree, [{
            "type": "span-regular",
            "text": "Einleitungstext mit mehreren Wörtern."}])

    def test_strong_in_the_middle(self):
        tree = convert_list([
            {'t': 'Str', 'c': 'Foo'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'is'},
            {'t': 'Space'},
            {'t': 'Strong', 'c': [{'t': 'Str', 'c': 'very'}, {'t': 'Space'}, {'t': 'Str', 'c': 'bar.'}]},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'Second'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'sentence.'}
        ], [])
        self.assertEqual(tree, [
            {"type": "span-regular", "text": "Foo is "},
            {"type": "span-strong", "text": "very bar."},
            {"type": "span-regular", "text": " Second sentence."}
        ])

    def test_beginning_with_strong(self):
        tree = convert_list([
            {'t': 'Strong', 'c': [{'t': 'Str', 'c': 'Strong'}, {'t': 'Space'}, {'t': 'Str', 'c': 'foo.'}]},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'Second'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'sentence.'}
        ], [])
        self.assertEqual(tree, [
            {"type": "span-strong", "text": "Strong foo."},
            {"type": "span-regular", "text": " Second sentence."}
        ])


class TestPandocMarkdownConverter(unittest.TestCase):
    def test_two_paragaraps(self):
        markdown = "This is the text of paragraph 1.\n\nThis is the second text."
        span_list = json_from_markdown(markdown)
        self.assertEqual([{
            "type": "block-paragraph",
            "spans": [{"type": "span-regular",
                       "text": "This is the text of paragraph 1."}]
        }, {
            "type": "block-paragraph",
            "spans": [{"type": "span-regular",
                       "text": "This is the second text."}]
        }], span_list)

    def test_single_quotes(self):
        markdown = "This 'test' is a fun-test!"
        span_list = json_from_markdown(markdown)
        self.assertEqual([{
            "type": "block-paragraph",
            "spans": [
                {'text': "This 'test' is a fun-test!", 'type': 'span-regular'}
            ]
        }], span_list)

    def test_strong(self):
        markdown = "Pinas **fette Beute**"
        span_list = json_from_markdown(markdown)
        self.assertEqual([{
            "type": "block-paragraph",
            "spans": [
                {'text': 'Pinas ', 'type': 'span-regular'},
                {'text': 'fette Beute', 'type': 'span-strong'}
            ]
        }], span_list)

    def test_em_strong(self):
        markdown = "The **strong** man *emphasized*: \"I can do ***both***! I can 'strongly' emphasize!\""
        span_list = json_from_markdown(markdown)
        self.assertEqual([{
            "type": "block-paragraph",
            "spans": [
                {'text': 'The ', 'type': 'span-regular'},
                {'text': 'strong', 'type': 'span-strong'},
                {'text': ' man ', 'type': 'span-regular'},
                {'text': 'emphasized', 'type': 'span-emphasized'},
                {'text': ': "I can do ', 'type': 'span-regular'},
                {'text': 'both', 'type': 'span-strong-emphasized'},
                {'text': "! I can 'strongly' emphasize!\"", 'type': 'span-regular'}
            ]
        }], span_list)

    def test_inline_code(self):
        markdown = "Code can be `inline = 2`. Fascinating!"
        span_list = json_from_markdown(markdown)
        self.assertEqual([{
            "type": "block-paragraph",
            "spans": [
                {'text': 'Code can be ', 'type': 'span-regular'},
                {'listing_text': 'inline = 2', 'type': 'span-listing'},
                {'text': '. Fascinating!', 'type': 'span-regular'}
            ]
        }], span_list)

    def test_link(self):
        markdown = "An [inline link](https://ct.de \"c't Homepage\") with title."
        span_list = json_from_markdown(markdown)
        self.assertEqual([{
            "type": "block-paragraph",
            "spans": [
                {'text': 'An ', 'type': 'span-regular'},
                {'link_text': 'inline link',
                 'type': 'span-link',
                 'url': 'https://ct.de'},
                {'text': ' with title.', 'type': 'span-regular'}
            ]
        }], span_list)

    def test_blockquotes(self):
        markdown = "As Kayne West said:\n\n> We are living in the future so\n> the present is our past."
        span_list = json_from_markdown(markdown)
        self.assertEqual([{
            "type": "block-paragraph",
            "spans": [
                {'text': 'As Kayne West said:', 'type': 'span-regular'}
            ]
        }, {
            "type": "block-citation",
            "statement": "We are living in the future so the present is our past.\n",
            "attribution": ""
        }], span_list)

    def test_custom_asset(self):
        markdown = "Erste Zeile.\n\n<!---\ntype: block-citation\n" + \
                   "statement: Winter is coming.\nattribution: Ned Stark\n-->\n\nAbsatz."
        block_list = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Erste Zeile."}]},
            {"type": "block-citation", "statement": "Winter is coming.", "attribution": "Ned Stark"},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Absatz."}]},
        ], block_list)

    def test_info_box(self):
        markdown = "Erste Zeile.\n\n<!---\ntype: block-info-box\n" + \
                   "title: Kastenüberschrift\ncontent: MD_BLOCK\n-->\n\n" + \
                   "Dieser Text gehört in den Kasten.\n\nEr hat **zwei** Absätze.\n\n" + \
                   "<!----->\n\nAbsatz."
        block_list = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Erste Zeile."}]},
            {"type": "block-info-box", "title": "Kastenüberschrift", "content": [
                {"type": "block-paragraph", "spans": [
                    {"type": "span-regular", "text": "Dieser Text gehört in den Kasten."}
                ]},
                {"type": "block-paragraph", "spans": [
                    {"type": "span-regular", "text": "Er hat "},
                    {"type": "span-strong", "text": "zwei"},
                    {"type": "span-regular", "text": " Absätze."}
                ]}
            ]},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Absatz."}]},
        ], block_list)

    def test_info_box_late_title(self):
        markdown = "Erste Zeile.\n\n<!---\ntype: block-info-box\n" + \
                   "content: MD_BLOCK\n-->\n\n" + \
                   "Dieser Text gehört in den Kasten.\n\nEr hat **zwei** Absätze.\n\n" + \
                   "<!---\ntitle: Kastenüberschrift\n-->\n\nAbsatz."
        block_list = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Erste Zeile."}]},
            {"type": "block-info-box", "title": "Kastenüberschrift", "content": [
                {"type": "block-paragraph", "spans": [
                    {"type": "span-regular", "text": "Dieser Text gehört in den Kasten."}
                ]},
                {"type": "block-paragraph", "spans": [
                    {"type": "span-regular", "text": "Er hat "},
                    {"type": "span-strong", "text": "zwei"},
                    {"type": "span-regular", "text": " Absätze."}
                ]}
            ]},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Absatz."}]},
        ], block_list)

    def test_code_block(self):
        markdown = "Erste Zeile.\n\n```python\na = 2\n\nprint(a+3)\n```\n\nLetzte Zeile."
        block_list = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Erste Zeile."}]},
            {"type": "block-listing", "language": "python", "code": "a = 2\n\nprint(a+3)"},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Letzte Zeile."}]}
        ], block_list)

    def test_headings(self):
        markdown = "Erste Zeile.\n\n# Titel\n\nWeiterer Text muss sein.\n\n" + \
                   "## Zwischenüberschrift mit Leerzeichen\n\nLetzte Zeile."
        block_list = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Erste Zeile."}]},
            {"type": "block-heading", "heading": "Titel"},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Weiterer Text muss sein."}]},
            {"type": "block-subheading", "heading": "Zwischenüberschrift mit Leerzeichen"},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Letzte Zeile."}]}
        ], block_list)

    def test_standard_image(self):
        markdown = "Erste Zeile.\n\n![Bildunterschrift mit Beschreibung](https://url.to/image.file)\n\nLetzte Zeile."
        block_list = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Erste Zeile."}]},
            {"type": "block-image",
             "image_uri": "https://url.to/image.file",
             "caption": "Bildunterschrift mit Beschreibung",
             "alt": ""},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Letzte Zeile."}]}
        ], block_list)

    def test_conversion(self):
        with open(os.path.join(
                os.path.abspath(os.curdir),
                "tests" if os.path.abspath(os.curdir).split(os.path.sep)[-1] != "tests" else "",
                "mixed_document.md"), 'r') as md_file:
            markdown = md_file.read()
        tree = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-heading", "heading": "Heading"},
            {"type": "block-paragraph", "spans": [
                {"type": "span-regular", "text": "This is text with "},
                {"type": "span-strong", "text": "important"},
                {"type": "span-regular", "text": " content. It needs to be "},
                {"type": "span-emphasized", "text": "blockwise emphasized"},
                {"type": "span-regular", "text": "\nand even "},
                {"type": "span-strong-emphasized", "text": "strong and emphasized"},
                {"type": "span-regular", "text": ". It contains "},
                {"type": "span-listing", "listing_text": "inline code"},
                {"type": "span-regular", "text": " and a\n"},
                {"type": "span-link", "link_text": "link", "url": "https://ct.de"},
                {"type": "span-regular", "text": "."}
            ]},
            {"type": "block-subheading", "heading": "smaller Heading"},
            {"type": "block-image",
             "image_uri": "https://upload.wikimedia.org/wikipedia/commons/thumb/" +
                          "c/cf/Cscr-featured.png/50px-Cscr-featured.png",
             "caption": "This is the caption for an image.",
             "alt": ""},
            {"type": "block-paragraph", "spans": [
                {"type": "span-regular", "text": "The text continues below the second heading."}
            ]},
            {"type": "block-listing",
             "language": "python",
             "code": "import json\nprint(\n  json.dumps({\"key\": \"value\"})\n)"},
            {"type": "block-paragraph", "spans": [
                {"type": "span-regular",
                 "text": "Not only listings can be embedded. Citations are pretty interesting too:"}
            ]},
            {"type": "block-citation", "statement": "This is a citation\nwhich spans over two blocks.\n", "attribution": ""},
            {"type": "block-paragraph", "spans": [
                {"type": "span-regular", "text": "After that the text continues a usual."}
            ]}
        ], tree)


if __name__ == '__main__':
    unittest.main()
