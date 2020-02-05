import unittest
from helpers import convert_list, convert_list_text_only, json_from_markdown, consume_str
import os


class TestConsumeStr(unittest.TestCase):
    def test_consume_basic_list(self):
        self.assertEqual(
            "My \"bonnie\" is 'over' the ocean.\nNice.",
            consume_str([
                {'t': 'Str', 'c': 'My'},
                {'t': 'Space'},
                {'t': 'Quoted', 'c': [
                    {'t': 'DoubleQuote'},
                    {'t': 'Str', 'c': 'bonnie'},
                    {'t': 'DoubleQuote'}
                ]},
                {'t': 'Space'},
                {'t': 'Str', 'c': 'is'},
                {'t': 'Space'},
                {'t': 'Quoted', 'c': [
                    {'t': 'SingleQuote'},
                    {'t': 'Str', 'c': 'over'},
                    {'t': 'SingleQuote'}
                ]},
                {'t': 'Space'},
                {'t': 'Str', 'c': 'the'},
                {'t': 'Space'},
                {'t': 'Str', 'c': 'ocean.'},
                {'t': 'SoftBreak'},
                {'t': 'Str', 'c': 'Nice.'}
            ])
        )

    def test_non_consumable_list(self):
        illegal_list = [
            {'t': 'Str', 'c': 'My'},
            {'t': 'Space'},
            {'t': 'ErrorousTypeWhichDoesNotExist'}
        ]
        self.assertRaises(SyntaxError, consume_str, illegal_list)
        try:
            consume_str(illegal_list)
        except SyntaxError as ex:
            self.assertEqual(
                "Unable to consume: {'t': 'ErrorousTypeWhichDoesNotExist'}",
                ex.msg
            )


class TestPandocStringConverter(unittest.TestCase):
    def test_single_string(self):
        tree = convert_list([
            {'t': 'Str', 'c': 'Foo.'}
        ], [])
        self.assertIsInstance(tree, list)
        self.assertEqual(1, len(tree))
        self.assertIsInstance(tree[0], dict)
        self.assertIn("type", tree[0])
        self.assertEqual("span-regular", tree[0]["type"])
        self.assertIn("text", tree[0])
        self.assertEqual("Foo.", tree[0]["text"])
        self.assertEqual(2, len(tree[0].keys()))
        self.assertEqual([{
            "type": "span-regular",
            "text": "Foo."
        }], tree)

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
        self.assertEqual([{
            "type": "span-regular",
            "text": "Einleitungstext mit mehreren Wörtern."}], tree)

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
        self.assertEqual([
            {"type": "span-regular", "text": "Foo is "},
            {"type": "span-strong", "text": "very bar."},
            {"type": "span-regular", "text": " Second sentence."}
        ], tree)

    def test_beginning_with_strong(self):
        tree = convert_list([
            {'t': 'Strong', 'c': [{'t': 'Str', 'c': 'Strong'}, {'t': 'Space'}, {'t': 'Str', 'c': 'foo.'}]},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'Second'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'sentence.'}
        ], [])
        self.assertEqual([
            {"type": "span-strong", "text": "Strong foo."},
            {"type": "span-regular", "text": " Second sentence."}
        ], tree)

    def test_listing_merge(self):
        tree = convert_list([
            {'t': 'Code',
             'c': ["", "print(3,"]},
            {'t': 'Code',
             'c': ["", "1)"]}
        ], [])
        self.assertEqual([
            {"type": "span-listing", "listing_text": "print(3,1)"}
        ], tree)

    def test_consume_list_in_link(self):
        tree = convert_list([
            {'t': 'Link',
             'c': [
                 [],
                 [{'t': 'Strong', 'c': [
                     {'t': 'Str', 'c': 'Strong'},
                     {'t': 'Space'},
                     {'t': 'Str', 'c': 'foo.'}
                  ]}],
                 ['https://ct.de']
             ]}
        ], [])
        self.assertEqual([
            {'link_text': 'Strong foo.',
             'type': 'span-link',
             'url': 'https://ct.de'}
        ], tree)

    def test_convert_list_indentation(self):
        illegal_list = [
            {'t': 'Str', 'c': 'Text'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'mit'},
            {'t': 'Strange', 'c': 'Foo'},
            {'t': 'Space'},
            {'t': 'Str', 'c': 'Wörtern.'}
        ]
        self.assertRaises(SyntaxError, convert_list, illegal_list, [])
        try:
            convert_list(illegal_list, [])
        except SyntaxError as ex:
            self.assertEqual("Unknown type: {'t': 'Strange', 'c': 'Foo'}", ex.msg)

    def test_unknown_type_in_consume_str(self):
        self.assertRaises(SyntaxError, convert_list, [
            {'t': 'Link',
             'c': [
                 [],
                 [{'t': 'Unkn0wnType', 'c': 'blah'}],
                 ['https://ct.de']
             ]}
        ], [])

    def test_convert_text_only_quote(self):
        quote = convert_list_text_only([
            {'t': 'Quoted',
             'c': [
                 '"',
                 [{'t': 'Str', 'c': 'some'},
                  {'t': 'Space'},
                  {'t': 'Str', 'c': 'text.'}]
             ]}
        ])
        self.assertEqual('"some text."', quote)

    def test_convert_text_only_code(self):
        text = convert_list_text_only([
            {'t': 'Code',
             'c': ["",
                   "print('foo bar')\nassert True"
                   ]}
        ])
        self.assertEqual("print('foo bar')\nassert True", text)

    def test_convert_text_only_link(self):
        text = convert_list_text_only([
            {'t': 'Link',
             'c': ["",
                   [
                       {'t': 'Str', 'c': 'some'},
                       {'t': 'Space'},
                       {'t': 'Str', 'c': 'text.'}
                    ]
                   ]}
        ])
        self.assertEqual('some text.', text)

    def test_convert_text_only_strong(self):
        text = convert_list_text_only([
            {'t': 'Strong',
             'c': [
                 {'t': 'Str', 'c': 'some'},
                 {'t': 'Space'},
                 {'t': 'Str', 'c': 'text.'}
             ]}
        ])
        self.assertEqual('some text.', text)

    def test_convert_list_quoted_link_strong_emph(self):
        span_list = [
            {'t': 'Str', 'c': 'Write'},
            {'t': 'Space'},
            {'t': 'Quoted',
             'c': [
                 '"',
                 [{'t': 'Str', 'c': 'some'},
                  {'t': 'Space'},
                  {'t': 'Str', 'c': 'text'}]
             ]},
            {'t': 'Space'},
            {'t': 'Link',
             'c': [
                 "",
                 [{'t': 'Str', 'c': 'with'},
                  {'t': 'Space'},
                  {'t': 'Str', 'c': 'link'}],
                 ["https://url.com"]
             ]},
            {'t': 'Space'},
            {'t': 'Strong', 'c': [{'t': 'Emph', 'c': [
                {'t': 'Str', 'c': 'and'},
                {'t': 'Space'},
                {'t': 'Str', 'c': 'strong-emphasized'},
                {'t': 'Space'},
                {'t': 'Str', 'c': 'text'}
            ]}]},
            {'t': 'Str', 'c': '.'}
        ]
        block_list = []
        tree = convert_list(span_list, block_list)
        self.assertEqual('Write "some text" ', tree[0]['text'])
        self.assertEqual('with link', tree[1]['link_text'])
        self.assertEqual('https://url.com', tree[1]['url'])
        self.assertEqual(' ', tree[2]['text'])
        self.assertEqual('and strong-emphasized text', tree[3]['text'])
        self.assertEqual('.', tree[4]['text'])
        self.assertEqual(tree, [
            {'text': 'Write "some text" ', 'type': 'span-regular'},
            {'link_text': 'with link', 'type': 'span-link', 'url': 'https://url.com'},
            {'text': ' ', 'type': 'span-regular'},
            {'text': 'and strong-emphasized text', 'type': 'span-strong-emphasized'},
            {'text': '.', 'type': 'span-regular'}
        ])

    def test_convert_list_unknown_type_in_strong(self):
        illegal_list = [
            {'t': 'Str', 'c': 'Foo'},
            {'t': 'Space'},
            {'t': 'Strong', 'c': [{'t': 'Emph', 'c': [
                {'t': 'Str', 'c': 'bar'},
                {'t': 'IllegalType'}
            ]}]},
            {'t': 'Str', 'c': '.'}
        ]
        self.assertRaises(SyntaxError, convert_list, illegal_list, [])
        try:
            convert_list(illegal_list, [])
        except SyntaxError as ex:
            self.assertEqual("    Unknown type: {'t': 'IllegalType'}", ex.msg)

    def test_unknown_type_in_convert_list_quote(self):
        illegal_list = [
            {'t': 'Str', 'c': 'Foo'},
            {'t': 'Space'},
            {'t': 'Quoted', 'c': ['"', [
                {'t': 'Str', 'c': 'bar'},
                {'t': 'IllegalTypeInQuote'}
            ]]},
            {'t': 'Str', 'c': '.'}
        ]
        try:
            convert_list(illegal_list, [])
        except SyntaxError as ex:
            self.assertEqual("  Unknown type: {'t': 'IllegalTypeInQuote'}", ex.msg)
        self.assertRaises(SyntaxError, convert_list, illegal_list, [])


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

    def test_reference_link(self):
        markdown = "A [link][ref1] in ref style.\n\n[ref1]: https://ct.de"
        tree = json_from_markdown(markdown)
        self.assertEqual([{
            "type": "block-paragraph",
            "spans": [
                {'text': 'A ', 'type': 'span-regular'},
                {'link_text': 'link',
                 'type': 'span-link',
                 'url': 'https://ct.de'},
                {'text': ' in ref style.', 'type': 'span-regular'}
            ]
        }], tree)

    def test_reference_link_no_label(self):
        markdown = "Linking to [Merkert2019] in ref style.\n\n[Merkert2019]: https://ct.de"
        tree = json_from_markdown(markdown)
        self.assertEqual([{
            "type": "block-paragraph",
            "spans": [
                {'text': 'Linking to ', 'type': 'span-regular'},
                {'link_text': 'Merkert2019',
                 'type': 'span-link',
                 'url': 'https://ct.de'},
                {'text': ' in ref style.', 'type': 'span-regular'}
            ]
        }], tree)

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

    def test_meta_info(self):
        markdown = "Anfang.\n\n" + \
                   "<!---\ntype: meta-info\n" + \
                   "a: foo\nb: 3\n-->\n\n" + \
                   "Letzter Absatz."
        block_list = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Anfang."}]},
            {"type": "meta-info", "a": "foo", "b": 3},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Letzter Absatz."}]},
        ], block_list)

    def test_triple_block_meta_info(self):
        markdown = "Anfang.\n\n<!---\ntype: block-triple-box\n" + \
                   "title: Kasten mit Überschrift\ncontent: MD_BLOCK\n-->\n\n" + \
                   "Dieser Text gehört in den Kasten.\n\nEr hat **zwei** Absätze.\n\n" + \
                   "<!---\nextra-content: MD-BLOCK\n-->\n\n" + \
                   "Dies ist Textblock 2 im Kasten.\n\n" + \
                   "<!---\nadditional-extra-content: MDBLOCK\n-->\n\n" + \
                   "Dies ist Textblock 3 im Kasten.\n\n" + \
                   "<!----->\n\nZwischentext." + \
                   "\n\n<!---\ntype: meta-info\n" + \
                   "a: foo\nb: 3\n-->\n\n" + \
                   "Letzter Absatz."
        block_list = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Anfang."}]},
            {"type": "block-triple-box", "title": "Kasten mit Überschrift", "content": [
                {"type": "block-paragraph", "spans": [
                    {"type": "span-regular", "text": "Dieser Text gehört in den Kasten."}
                ]},
                {"type": "block-paragraph", "spans": [
                    {"type": "span-regular", "text": "Er hat "},
                    {"type": "span-strong", "text": "zwei"},
                    {"type": "span-regular", "text": " Absätze."}
                ]}
            ], "extra-content": [
                {"type": "block-paragraph", "spans": [
                    {"type": "span-regular", "text": "Dies ist Textblock 2 im Kasten."}
                ]}
            ], "additional-extra-content": [
                {"type": "block-paragraph", "spans": [
                    {"type": "span-regular", "text": "Dies ist Textblock 3 im Kasten."}
                ]}
            ]},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Zwischentext."}]},
            {"type": "meta-info", "a": "foo", "b": 3},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Letzter Absatz."}]},
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
                   "## Zwischenüberschrift mit Leerzeichen\n\nLetzte Zeile.\n\n" + \
                   "### Heading 3\n\nAbc def.\n\n" + \
                   "#### Heading 4\n\nAbc 2 def.\n\n" + \
                   "##### Heading 5\n\nAbc 3 def.\n\n" + \
                   "###### Heading 6\n\nAbc 4 def."
        block_list = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Erste Zeile."}]},
            {"type": "block-heading", "heading": "Titel"},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Weiterer Text muss sein."}]},
            {"type": "block-subheading", "heading": "Zwischenüberschrift mit Leerzeichen"},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Letzte Zeile."}]},
            {"type": "block-subsubheading", "heading": "Heading 3"},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Abc def."}]},
            {"type": "block-subsubsubheading", "heading": "Heading 4"},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Abc 2 def."}]},
            {"type": "block-subsubsubsubheading", "heading": "Heading 5"},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Abc 3 def."}]},
            {"type": "block-subsubsubsubsubheading", "heading": "Heading 6"},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Abc 4 def."}]}
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

    def test_reference_image(self):
        markdown = "Erste Zeile.\n\n![Bildunterschrift mit Beschreibung][ref]\n\nLetzte Zeile." + \
                   "\n\n[ref]: https://url.to/image.file \"Foo bar baz.\""
        block_list = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Erste Zeile."}]},
            {"type": "block-image",
             "image_uri": "https://url.to/image.file",
             "caption": "Bildunterschrift mit Beschreibung",
             "alt": "Foo bar baz."},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Letzte Zeile."}]}
        ], block_list)

    def test_ol(self):
        markdown = "Zeile 1\n\n1. List item\n1. Item 2\n\nAbsatz mit normalem Text\n\n" + \
                   "1. Ordered *List* 2\n\n   Eingerückter Absatz\n\n1. Aufzählung geht weiter\n1. Punkt 3\n\nEnde."
        block_list = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Zeile 1"}]},
            {"type": "block-ordered-list", "items": [
                {"type": "span-container", "items": [{"type": "span-container", "items": [
                        {"type": "span-regular", "text": "List item"}]}]},
                {"type": "span-container", "items": [{"type": "span-container", "items": [
                        {"type": "span-regular", "text": "Item 2"}]}]}
            ]},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Absatz mit normalem Text"}]},
            {"type": "block-ordered-list", "items": [
                {"type": "span-container", "items": [
                    {"type": "span-container", "items": [
                        {"type": "span-regular", "text": "Ordered "},
                        {"type": "span-emphasized", "text": "List"},
                        {"type": "span-regular", "text": " 2"}]},
                    {"type": "span-line-break-container",
                     "items": [{"type": "span-container", "items": [
                         {"type": "span-regular", "text": "Eingerückter Absatz"}]}]}]},
                {"type": "span-container", "items": [{"type": "span-container", "items": [
                        {"type": "span-regular", "text": "Aufzählung geht weiter"}]}]},
                {"type": "span-container", "items": [{"type": "span-container", "items": [
                        {"type": "span-regular", "text": "Punkt 3"}]}]}
            ]},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Ende."}]}
        ], block_list)

    def test_ul(self):
        markdown = "Zeile 1\n\n* List item\n* Item 2\n\nAbsatz mit normalem Text\n\n" + \
                   "* Ordered *List* 2\n\n  Eingerückter Absatz\n\n* Aufzählung geht weiter\n* Punkt 3\n\nEnde."
        block_list = json_from_markdown(markdown)
        self.assertEqual([
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Zeile 1"}]},
            {"type": "block-unordered-list", "items": [
                {"type": "span-container", "items": [{"type": "span-container", "items": [
                        {"type": "span-regular", "text": "List item"}]}]},
                {"type": "span-container", "items": [{"type": "span-container", "items": [
                        {"type": "span-regular", "text": "Item 2"}]}]}
            ]},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Absatz mit normalem Text"}]},
            {"type": "block-unordered-list", "items": [
                {"type": "span-container", "items": [
                    {"type": "span-container", "items": [
                        {"type": "span-regular", "text": "Ordered "},
                        {"type": "span-emphasized", "text": "List"},
                        {"type": "span-regular", "text": " 2"}]},
                    {"type": "span-line-break-container",
                     "items": [{"type": "span-container", "items": [
                         {"type": "span-regular", "text": "Eingerückter Absatz"}]}]}]},
                {"type": "span-container", "items": [{"type": "span-container", "items": [
                        {"type": "span-regular", "text": "Aufzählung geht weiter"}]}]},
                {"type": "span-container", "items": [{"type": "span-container", "items": [
                        {"type": "span-regular", "text": "Punkt 3"}]}]}
            ]},
            {"type": "block-paragraph", "spans": [{"type": "span-regular", "text": "Ende."}]}
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
