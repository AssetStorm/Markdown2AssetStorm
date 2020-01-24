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


class RequestContextTestCase(unittest.TestCase):
    def setUp(self) -> None:
        app.testing = True

    def test_request_context_multiline_text(self):
        markdown = "This is the text of paragraph 1.\n\nThis is the second text."
        with app.test_request_context('/', method='POST', data=markdown):
            self.assertEqual(request.get_data(as_text=True), markdown)


if __name__ == '__main__':
    unittest.main()
