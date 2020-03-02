from converter import app, request
from typing import Union
import unittest


class ConvertTestCase(unittest.TestCase):
    def setUp(self) -> None:
        app.testing = True

    def test_two_paragaraps(self,
                            markdown: Union[str, bytes] =
                            "This is the text of paragraph 1.\n\nThis is the second text."):
        with app.test_client() as test_client:
            response = test_client.post('/', data=markdown)
            tree = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertEqual({"type": "conversion-container", "blocks": [{
            "type": "block-paragraph",
            "spans": [{"type": "span-regular",
                       "text": "This is the text of paragraph 1."}]
        }, {
            "type": "block-paragraph",
            "spans": [{"type": "span-regular",
                       "text": "This is the second text."}]
        }]}, tree)

    def test_utf8_bytes_in_request(self):
        utf8_bytes_markdown = "This is the text of paragraph 1.\n\nThis is the second text.".encode('utf-8')
        self.test_two_paragaraps(markdown=utf8_bytes_markdown)

    def test_strange_bytes_in_request(self):
        illegal_bytes = b"\xa5\xb6"
        with app.test_client() as test_client:
            response = test_client.post('/', data=illegal_bytes)
            tree = response.get_json()
            self.assertEqual(b'\xef\xbf\xbd\xef\xbf\xbd',
                             tree['blocks'][0]['spans'][0]['text'].encode('utf-8'))

    def test_typeless_magic_block(self):
        with app.test_client() as test_client:
            response = test_client.post('/', data="<!---\nfoo: bar\n-->")
            tree = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertEqual({'type': 'conversion-container', 'blocks': []}, tree)

    def test_yaml_pipe_style_magic_block(self):
        with app.test_client() as test_client:
            response = test_client.post('/', data="<!---\ntype: test\nfoo: |\n  MD_BLOCK\n-->\n# H1\n\n<!--- -->")
            tree = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertEqual({'type': 'conversion-container',
                          'blocks': [{'type': 'test', 'foo': [{'heading': 'H1', 'type': 'block-heading'}]}]}, tree)

    def no_test_article_standard_magic_block(self):
        markdown = "<!---\nauthor: |\n  MD_BLOCK\n  -->\n\n  Pina Merkert\n\n  <!---\n" + \
                   "catchphrase: Testartikel\ncolumn: Wissen\n" + \
                   "content: \"MD_BLOCK\n-->\n\nText des Artikels.\n\nMehrere Absätze\n\n<!---\n\"\n" + \
                   "subtitle: |\n  MD_BLOCK\n  -->\n\n  ## Untertitel\n\n  <!---\n" + \
                   "teaser: |\n  MD_BLOCK\n  -->\n\n  **Vorlauftext**\n\n  <!---\n" + \
                   "title: |\n  MD_BLOCK\n  -->\n\n  # Titel\n\n  <!---\n" + \
                   "type: article-standard\nworking_title: Standard-Testartikel\n-->"
        with app.test_client() as test_client:
            response = test_client.post('/', data=markdown)
            tree = response.get_json()
        self.assertEqual(
            {'type': 'conversion-container',
             'blocks': []}, tree)

    def test_article_magic_block(self):
        with app.test_client() as test_client:
            response = test_client.post(
                '/', data="<!---\n" +
                "type: article-standard\n" +
                "x_id: \"\"\n" +
                "title: MD_BLOCK\n-->\n# Titel\n\n<!---\n" +
                "subtitle: MD_BLOCK\n-->\n## Untertitel\n\n<!---\n" +
                "teaser: MD_BLOCK\n-->\n**Vorlauftext**\n\n<!---\n" +
                "author: MD_BLOCK\n-->\nPina Merkert\n\n<!---\n" +
                "content: MD_BLOCK\n-->\n" +
                "Text des Artikels.\n\n" +
                "Mehrere Absätze\n\n" +
                "<!--- -->")
            tree = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertEqual({'type': 'conversion-container', 'blocks': [{
            'type': 'article-standard',
            'x_id': '',
            'title': [{'heading': 'Titel', 'type': 'block-heading'}],
            'subtitle': [{'heading': 'Untertitel',
                          'type': 'block-subheading'}],
            'teaser': [{'spans': [{'text': 'Vorlauftext',
                                   'type': 'span-strong'}],
                        'type': 'block-paragraph'}],
            'author': [{'spans': [{'text': 'Pina Merkert',
                                    'type': 'span-regular'}],
                         'type': 'block-paragraph'}],
            'content': [{'spans': [{'text': 'Text des Artikels.',
                                    'type': 'span-regular'}],
                         'type': 'block-paragraph'},
                        {'spans': [{'text': 'Mehrere Absätze',
                                    'type': 'span-regular'}],
                         'type': 'block-paragraph'}]
        }]}, tree)

    def test_article_h2_h4(self):
        markdown = "<!---\n" + \
                   "type: article-standard\n" + \
                   "x_id: 1234567890123456789\n" + \
                   "catchphrase: Testartikel\n" + \
                   "column: Wissen\n" + \
                   "working_title: Standard-Testartikel\n" + \
                   "title: MD_BLOCK\n" + \
                   "-->\n\n# Titel\n\n<!---\n" + \
                   "subtitle: MD_BLOCK\n" + \
                   "-->\n\n## Untertitel\n\n<!---\n" + \
                   "teaser: MD_BLOCK\n" + \
                   "-->\n\n**Vorlauftext**\n\n<!---\n" + \
                   "author: MD_BLOCK\n-->\n\nPina Merkert\n\n<!---\n" + \
                   "content: MD_BLOCK\n" + \
                   "-->\n\n" + \
                   "## \"0x- *'abc' n +X**Ü/0**ÄöM+S ÖR/q+0/ -\"+.I vQ.\" 1\"/+5 " + \
                   ".m+u*-*- 'f0Üxys 10te.' tcut97 0- 1H/ü+uAt.*H\n\n" + \
                   "##### 0\n\n" + \
                   "<!--- -->"
        with app.test_client() as test_client:
            response = test_client.post('/', data=markdown)
            tree = response.get_json()
        self.assertEqual(
            {'type': 'conversion-container', 'blocks': [
                {'type': 'article-standard',
                 'author': [{'type': 'block-paragraph', 'spans': [
                    {'type': 'span-regular', 'text': 'Pina Merkert'}]}],
                 'catchphrase': 'Testartikel',
                 'column': 'Wissen',
                 'subtitle': [{'type': 'block-subheading', 'heading': 'Untertitel'}],
                 'teaser': [{'type': 'block-paragraph', 'spans': [
                     {'type': 'span-strong', 'text': 'Vorlauftext'}]}],
                 'title': [{'type': 'block-heading', 'heading': 'Titel'}],
                 'working_title': 'Standard-Testartikel',
                 'x_id': "1234567890123456789",
                 'content': [
                     {'type': 'block-subheading',
                      'heading': "\"0x- *'abc' n +X**Ü/0**ÄöM+S ÖR/q+0/ -\"+.I vQ.\" 1\"/+5 " +
                                 ".m+u*-*- 'f0Üxys 10te.' tcut97 0- " + '1H/ü+uAt.*H'},
                     {'type': 'block-subsubsubsubheading', 'heading': '0'}]
                }]},
            tree)

    def test_article_ol_a(self):
        markdown = "<!---\n" + \
                   "type: article-standard\n" + \
                   "x_id: 1234567890123456789\n" + \
                   "catchphrase: Testartikel\n" + \
                   "column: Wissen\n" + \
                   "working_title: Standard-Testartikel\n" + \
                   "title: MD_BLOCK\n" + \
                   "-->\n\n# Titel\n\n<!---\n" + \
                   "subtitle: MD_BLOCK\n" + \
                   "-->\n\n## Untertitel\n\n<!---\n" + \
                   "teaser: MD_BLOCK\n" + \
                   "-->\n\n**Vorlauftext**\n\n<!---\n" + \
                   "author: MD_BLOCK\n-->\n\nPina Merkert\n\n<!---\n" + \
                   "content: MD_BLOCK\n" + \
                   "-->\n\n" + \
                   "1. [a](http://b)" + \
                   "\n\n<!--- -->"
        with app.test_client() as test_client:
            response = test_client.post('/', data=markdown)
            tree = response.get_json()
        self.assertEqual({'type': 'conversion-container', 'blocks': [{
            'type': 'article-standard',
            'working_title': 'Standard-Testartikel',
            'x_id': '1234567890123456789',
            'catchphrase': 'Testartikel',
            'column': 'Wissen',
            'title': [{'heading': 'Titel', 'type': 'block-heading'}],
            'subtitle': [{'heading': 'Untertitel',
                          'type': 'block-subheading'}],
            'teaser': [{'spans': [{'text': 'Vorlauftext',
                                   'type': 'span-strong'}],
                        'type': 'block-paragraph'}],
            'author': [{'spans': [{'text': 'Pina Merkert',
                                   'type': 'span-regular'}],
                        'type': 'block-paragraph'}],
            'content': [
                {'type': 'block-ordered-list', 'items': [
                    {'type': 'span-container', 'spans': [
                        {'type': 'span-container', 'spans': [
                            {'type': 'span-link',
                             'url': 'http://b',
                             'link_text': 'a'}
                        ]}
                    ]}
                ]}]
        }]}, tree)

    def test_ol_two_items_with_html(self):
        markdown = "<!---\n" + \
                   "type: article-standard\n" + \
                   "x_id: 1234567890123456789\n" + \
                   "catchphrase: Testartikel\n" + \
                   "column: Wissen\n" + \
                   "working_title: Standard-Testartikel\n" + \
                   "title: MD_BLOCK\n" + \
                   "-->\n\n# Titel\n\n<!---\n" + \
                   "subtitle: MD_BLOCK\n" + \
                   "-->\n\n## Untertitel\n\n<!---\n" + \
                   "teaser: MD_BLOCK\n" + \
                   "-->\n\n**Vorlauftext**\n\n<!---\n" + \
                   "author: MD_BLOCK\n-->\n\nPina Merkert\n\n<!---\n" + \
                   "content: MD_BLOCK\n" + \
                   "-->\n\n" + \
                   "1. A <fs-path>/foo</fs-path> x.\n" + \
                   "1. B <fs-path>/bar</fs-path> y.\n" + \
                   "\n\n<!--- -->"
        with app.test_client() as test_client:
            response = test_client.post('/', data=markdown)
            tree = response.get_json()
        self.assertEqual({'type': 'conversion-container', 'blocks': [{
            'type': 'article-standard',
            'working_title': 'Standard-Testartikel',
            'x_id': '1234567890123456789',
            'catchphrase': 'Testartikel',
            'column': 'Wissen',
            'title': [{'heading': 'Titel', 'type': 'block-heading'}],
            'subtitle': [{'heading': 'Untertitel',
                          'type': 'block-subheading'}],
            'teaser': [{'spans': [{'text': 'Vorlauftext',
                                   'type': 'span-strong'}],
                        'type': 'block-paragraph'}],
            'author': [{'spans': [{'text': 'Pina Merkert',
                                   'type': 'span-regular'}],
                        'type': 'block-paragraph'}],
            'content': [
                {'type': 'block-ordered-list', 'items': [
                    {'type': 'span-container', 'spans': [
                        {'type': 'span-container', 'spans': [
                            {'type': 'span-regular', 'text': 'A '},
                            {'type': 'span-path', 'path': '/foo'},
                            {'type': 'span-regular', 'text': ' x.'}
                        ]}
                    ]},
                    {'type': 'span-container', 'spans': [
                        {'type': 'span-container', 'spans': [
                            {'type': 'span-regular', 'text': 'B '},
                            {'type': 'span-path', 'path': '/bar'},
                            {'type': 'span-regular', 'text': ' y.'}
                        ]}
                    ]}
                ]}
            ]}
        ]}, tree)

    def test_ul_two_items_with_html(self):
        markdown = "<!---\n" + \
                   "type: article-standard\n" + \
                   "x_id: 1234567890123456789\n" + \
                   "catchphrase: Testartikel\n" + \
                   "column: Wissen\n" + \
                   "working_title: Standard-Testartikel\n" + \
                   "title: MD_BLOCK\n" + \
                   "-->\n\n# Titel\n\n<!---\n" + \
                   "subtitle: MD_BLOCK\n" + \
                   "-->\n\n## Untertitel\n\n<!---\n" + \
                   "teaser: MD_BLOCK\n" + \
                   "-->\n\n**Vorlauftext**\n\n<!---\n" + \
                   "author: MD_BLOCK\n-->\n\nPina Merkert\n\n<!---\n" + \
                   "content: MD_BLOCK\n" + \
                   "-->\n\n" + \
                   "* A <fs-path>/foo</fs-path> x.\n" + \
                   "* B <fs-path>/bar</fs-path> y.\n" + \
                   "\n\n<!--- -->"
        with app.test_client() as test_client:
            response = test_client.post('/', data=markdown)
            tree = response.get_json()
        self.assertEqual({'type': 'conversion-container', 'blocks': [{
            'type': 'article-standard',
            'working_title': 'Standard-Testartikel',
            'x_id': '1234567890123456789',
            'catchphrase': 'Testartikel',
            'column': 'Wissen',
            'title': [{'heading': 'Titel', 'type': 'block-heading'}],
            'subtitle': [{'heading': 'Untertitel',
                          'type': 'block-subheading'}],
            'teaser': [{'spans': [{'text': 'Vorlauftext',
                                   'type': 'span-strong'}],
                        'type': 'block-paragraph'}],
            'author': [{'spans': [{'text': 'Pina Merkert',
                                   'type': 'span-regular'}],
                        'type': 'block-paragraph'}],
            'content': [
                {'type': 'block-unordered-list', 'items': [
                    {'type': 'span-container', 'spans': [
                        {'type': 'span-container', 'spans': [
                            {'type': 'span-regular', 'text': 'A '},
                            {'type': 'span-path', 'path': '/foo'},
                            {'type': 'span-regular', 'text': ' x.'}
                        ]}
                    ]},
                    {'type': 'span-container', 'spans': [
                        {'type': 'span-container', 'spans': [
                            {'type': 'span-regular', 'text': 'B '},
                            {'type': 'span-path', 'path': '/bar'},
                            {'type': 'span-regular', 'text': ' y.'}
                        ]}
                    ]}
                ]}
            ]}
        ]}, tree)

    def test_list_with_a_lot_of_formatting(self):
        self.maxDiff = None
        markdown = "<!---\n" + \
                   "type: article-standard\n" + \
                   "x_id: 1234567890123456789\n" + \
                   "catchphrase: Testartikel\n" + \
                   "column: Wissen\n" + \
                   "working_title: Standard-Testartikel\n" + \
                   "title: MD_BLOCK\n" + \
                   "-->\n\n# Titel\n\n<!---\n" + \
                   "subtitle: MD_BLOCK\n" + \
                   "-->\n\n## Untertitel\n\n<!---\n" + \
                   "teaser: MD_BLOCK\n" + \
                   "-->\n\n**Vorlauftext**\n\n<!---\n" + \
                   "author: MD_BLOCK\n-->\n\nPina Merkert\n\n<!---\n" + \
                   "content: MD_BLOCK\n" + \
                   "-->\n\n" + \
                   "* *0 1/00* `.`\n" + \
                   "* **2.0000** <fs-path>- 00R 0</fs-path> *V* 0 P //000 0 0 *0* *1* *01*\n" + \
                   "* *0 0 1+00 1* 1/0 *1 0 7.0* 0 . 0x/ .0\n\n" + \
                   "## 0 1" + \
                   "\n\n<!--- -->"
        with app.test_client() as test_client:
            response = test_client.post('/', data=markdown)
            tree = response.get_json()
        self.assertEqual({'type': 'conversion-container', 'blocks': [{
            'type': 'article-standard',
            'working_title': 'Standard-Testartikel',
            'x_id': '1234567890123456789',
            'catchphrase': 'Testartikel',
            'column': 'Wissen',
            'title': [{'heading': 'Titel', 'type': 'block-heading'}],
            'subtitle': [{'heading': 'Untertitel',
                          'type': 'block-subheading'}],
            'teaser': [{'spans': [{'text': 'Vorlauftext',
                                   'type': 'span-strong'}],
                        'type': 'block-paragraph'}],
            'author': [{'spans': [{'text': 'Pina Merkert',
                                   'type': 'span-regular'}],
                        'type': 'block-paragraph'}],
            'content': [
                {'type': 'block-unordered-list', 'items': [
                    {'type': 'span-container', 'spans': [
                        {'type': 'span-container', 'spans': [
                            {'type': 'span-emphasized', 'text': '0 1/00'},
                            {'type': 'span-regular', 'text': ' '},
                            {'type': 'span-listing', 'listing_text': '.'}
                        ]}
                    ]},
                    {'type': 'span-container', 'spans': [
                        {'type': 'span-container', 'spans': [
                            {'type': 'span-strong', 'text': '2.0000'},
                            {'type': 'span-regular', 'text': ' '},
                            {'type': 'span-path', 'path': '- 00R 0'},
                            {'type': 'span-regular', 'text': ' '},
                            {'type': 'span-emphasized', 'text': 'V'},
                            {'type': 'span-regular', 'text': ' 0 P //000 0 0 '},
                            {'type': 'span-emphasized', 'text': '0'},
                            {'type': 'span-regular', 'text': ' '},
                            {'type': 'span-emphasized', 'text': '1'},
                            {'type': 'span-regular', 'text': ' '},
                            {'type': 'span-emphasized', 'text': '01'}
                        ]}
                    ]},
                    {'type': 'span-container', 'spans': [
                        {'type': 'span-container', 'spans': [
                            {'type': 'span-emphasized', 'text': '0 0 1+00 1'},
                            {'type': 'span-regular', 'text': ' 1/0 '},
                            {'type': 'span-emphasized', 'text': '1 0 7.0'},
                            {'type': 'span-regular', 'text': ' 0 . 0x/ .0'}
                        ]}
                    ]}
                ]},
                {'type': 'block-subheading', 'heading': '0 1'}
            ]}
        ]}, tree)

    def test_magic_block_article_with_bibliography_and_link(self):
        markdown = "<!---\n" + \
                   "type: article-standard\n" + \
                   "x_id: 1234567890123456789\n" + \
                   "catchphrase: Testartikel\n" + \
                   "column: Wissen\n" + \
                   "working_title: Standard-Testartikel\n" + \
                   "title: MD_BLOCK\n" + \
                   "-->\n\n# Titel\n\n<!---\n" + \
                   "subtitle: MD_BLOCK\n" + \
                   "-->\n\n## Untertitel\n\n<!---\n" + \
                   "teaser: MD_BLOCK\n" + \
                   "-->\n\n**Vorlauftext**\n\n<!---\n" + \
                   "author: MD_BLOCK\n-->\n\nPina Merkert\n\n<!---\n" + \
                   "content: MD_BLOCK\n-->\n\n" + \
                   "Article *content*." + \
                   "\n\n<!---\n" + \
                   "article_link:\n" + \
                   "  type: article-link-container\n" + \
                   "  link_description: Dokumentation\n" + \
                   "  link: <ctlink />\n" + \
                   "bibliography: []\n" + \
                   "-->"
        with app.test_client() as test_client:
            response = test_client.post('/', data=markdown)
            tree = response.get_json()
        self.assertEqual({'type': 'conversion-container', 'blocks': [
            {'type': 'article-standard',
             'working_title': 'Standard-Testartikel',
             'x_id': '1234567890123456789',
             'catchphrase': 'Testartikel',
             'column': 'Wissen',
             'title': [{'heading': 'Titel', 'type': 'block-heading'}],
             'subtitle': [{'heading': 'Untertitel',
                           'type': 'block-subheading'}],
             'teaser': [{'spans': [{'text': 'Vorlauftext',
                                    'type': 'span-strong'}],
                         'type': 'block-paragraph'}],
             'author': [{'spans': [{'text': 'Pina Merkert',
                                    'type': 'span-regular'}],
                         'type': 'block-paragraph'}],
             'content': [
                 {'type': 'block-paragraph', 'spans': [
                     {'type': 'span-regular', 'text': 'Article '},
                     {'type': 'span-emphasized', 'text': 'content'},
                     {'type': 'span-regular', 'text': '.'}
                 ]}
             ],
             'article_link': {'type': 'article-link-container',
                              'link_description': 'Dokumentation',
                              'link': {'type': 'span-ct-link'}},
             'bibliography': []}
        ]}, tree)

    def test_toc_small(self):
        markdown = "<!---\ntype: article-table-of-contents\nx_id: 1234567890123456789\ntitle: MD_BLOCK\n-->\n\n" + \
                    "# Inhaltsverzeichnis\n\n" + \
                   "<!---\ncontent: MD_BLOCK\n-->\n\n" + \
                    "<!---\ntype: toc-block\nentries: MD_BLOCK\n-->\n\n" + \
                     "<!---\ntype: toc-small\npage: 21\ntext: MD_BLOCK\n-->\n\n" + \
                      "**Kurztext 3** mit Ergänzung\n\n" + \
                     "<!--- -->\n\n" + \
                    "<!--- -->\n\n" + \
                   "<!--- -->"
        with app.test_client() as test_client:
            response = test_client.post('/', data=markdown)
            tree = response.get_json()
        self.assertEqual({
            'type': 'conversion-container',
            'blocks': [
                {'type': 'article-table-of-contents',
                 'x_id': '1234567890123456789',
                 'title': [{'heading': 'Inhaltsverzeichnis',
                            'type': 'block-heading'}],
                 'content': [
                     {'type': 'toc-block',
                      'entries': [
                          {'type': 'toc-small',
                           'page': '21',
                           'text': [{
                               'type': 'block-paragraph',
                               'spans': [
                                   {'type': 'span-strong', 'text': 'Kurztext 3'},
                                   {'type': 'span-regular', 'text': ' mit Ergänzung'}]}
                           ]}
                      ]}
                 ]}
            ]
        }, tree)

    def test_toc_big(self):
        markdown = "<!---\ntype: article-table-of-contents\nx_id: 1234567890123456789\ntitle: MD_BLOCK\n-->\n\n" + \
            "# Inhaltsverzeichnis\n\n" + \
            "<!---\ncontent: MD_BLOCK\n-->\n\n" + \
                "<!---\ntype: toc-block\nentries: MD_BLOCK\n-->\n\n" + \
                    "<!---\ntype: toc-heading-container\ntitle: Block 1\nentries: MD_BLOCK\n-->\n\n" + \
                        "<!---\ntype: toc-small\npage: 13\ntext: MD_BLOCK\n-->\n\n" + \
                        "**Kurztext 1** mit Ergänzung\n\n" + \
                        "<!--- -->\n\n" + \
                        "<!---\ntype: toc-small\npage: 17\ntext: MD_BLOCK\n-->\n\n" + \
                        "**Kurztext 2** mit Ergänzung\n\n" + \
                        "<!--- -->\n\n" + \
                    "<!--- -->\n\n" + \
                    "<!---\ntype: toc-small\npage: 21\ntext: MD_BLOCK\n-->\n\n" + \
                    "**Kurztext 3** mit Ergänzung\n\n" + \
                    "<!--- -->\n\n" + \
                    "<!---\ntype: toc-heading-container\ntitle: Block 2\nentries: MD_BLOCK\n-->\n\n" + \
                        "<!---\ntype: toc-small\npage: 130\ntext: MD_BLOCK\n-->\n\n" + \
                        "**Kurztext 4** mit Ergänzung\n\n" + \
                        "<!--- -->\n\n" + \
                        "<!---\ntype: toc-small\npage: 134\ntext: MD_BLOCK\n-->\n\n" + \
                        "**Kurztext 5** mit Ergänzung\n\n" + \
                        "<!--- -->\n\n" + \
                        "<!---\ntype: toc-small\npage: 138\ntext: MD_BLOCK\n-->\n\n" + \
                        "**Kurztext 6** mit Ergänzung\n\n" + \
                        "<!--- -->\n\n" + \
                    "<!--- -->\n\n" + \
                "<!--- -->\n\n" + \
            "<!--- -->"
        with app.test_client() as test_client:
            response = test_client.post('/', data=markdown)
            tree = response.get_json()
        self.assertEqual({
            'type': 'conversion-container',
            'blocks': [
                {'type': 'article-table-of-contents',
                 'x_id': '1234567890123456789',
                 'title': [{'heading': 'Inhaltsverzeichnis',
                            'type': 'block-heading'}],
                 'content': [
                     {'type': 'toc-block',
                      'entries': [
                          {'type': 'toc-heading-container',
                           'title': 'Block 1',
                           'entries': [
                               {'type': 'toc-small',
                                'page': '13',
                                'text': [{
                                    'type': 'block-paragraph',
                                    'spans': [
                                        {'type': 'span-strong', 'text': 'Kurztext 1'},
                                        {'type': 'span-regular', 'text': ' mit Ergänzung'}]}
                                ]},
                               {'type': 'toc-small',
                                'page': '17',
                                'text': [{
                                    'type': 'block-paragraph',
                                    'spans': [
                                        {'type': 'span-strong', 'text': 'Kurztext 2'},
                                        {'type': 'span-regular', 'text': ' mit Ergänzung'}]}
                                ]}
                           ]},
                          {'type': 'toc-small',
                           'page': '21',
                           'text': [{
                               'type': 'block-paragraph',
                               'spans': [
                                   {'type': 'span-strong', 'text': 'Kurztext 3'},
                                   {'type': 'span-regular', 'text': ' mit Ergänzung'}]}
                           ]},
                          {'type': 'toc-heading-container',
                           'title': 'Block 2',
                           'entries': [
                               {'type': 'toc-small',
                                'page': '130',
                                'text': [{
                                    'type': 'block-paragraph',
                                    'spans': [
                                        {'type': 'span-strong', 'text': 'Kurztext 4'},
                                        {'type': 'span-regular', 'text': ' mit Ergänzung'}]}
                                ]},
                               {'type': 'toc-small',
                                'page': '134',
                                'text': [{
                                    'type': 'block-paragraph',
                                    'spans': [
                                        {'type': 'span-strong', 'text': 'Kurztext 5'},
                                        {'type': 'span-regular', 'text': ' mit Ergänzung'}]}
                                ]},
                               {'type': 'toc-small',
                                'page': '138',
                                'text': [{
                                    'type': 'block-paragraph',
                                    'spans': [
                                        {'type': 'span-strong', 'text': 'Kurztext 6'},
                                        {'type': 'span-regular', 'text': ' mit Ergänzung'}]}
                                ]}
                           ]}
                      ]}
                 ]}
            ]
        }, tree)


class RequestContextTestCase(unittest.TestCase):
    def setUp(self) -> None:
        app.testing = True

    def test_request_context_multiline_text(self):
        markdown = "This is the text of paragraph 1.\n\nThis is the second text."
        with app.test_request_context('/', method='POST', data=markdown):
            self.assertEqual(request.get_data(as_text=True), markdown)


if __name__ == '__main__':
    unittest.main()
