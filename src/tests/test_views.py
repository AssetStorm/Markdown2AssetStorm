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
        self.assertEqual({'type': 'conversion-container', 'blocks': [{'foo': 'bar'}]}, tree)

    def test_yaml_pipe_style_magic_block(self):
        with app.test_client() as test_client:
            response = test_client.post('/', data="<!---\nfoo: |\n  MD_BLOCK\n-->\n# H1\n\n<!--- -->")
            tree = response.get_json()
        self.assertEqual(200, response.status_code)
        self.assertEqual({'type': 'conversion-container',
                          'blocks': [{'foo': [{'heading': 'H1', 'type': 'block-heading'}]}]}, tree)

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


class RequestContextTestCase(unittest.TestCase):
    def setUp(self) -> None:
        app.testing = True

    def test_request_context_multiline_text(self):
        markdown = "This is the text of paragraph 1.\n\nThis is the second text."
        with app.test_request_context('/', method='POST', data=markdown):
            self.assertEqual(request.get_data(as_text=True), markdown)


if __name__ == '__main__':
    unittest.main()
