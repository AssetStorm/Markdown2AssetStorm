from converter import app, request
import unittest


class ConvertTestCase(unittest.TestCase):
    def setUp(self) -> None:
        app.testing = True

    def test_two_paragaraps(self):
        markdown = "This is the text of paragraph 1.\n\nThis is the second text."
        with app.test_client() as test_client:
            response = test_client.post('/', data=markdown)
            tree = response.get_json()
        self.assertEqual({"type": "block-blocks", "blocks": [{
            "type": "block-paragraph",
            "spans": [{"type": "span-regular",
                       "text": "This is the text of paragraph 1."}]
        }, {
            "type": "block-paragraph",
            "spans": [{"type": "span-regular",
                       "text": "This is the second text."}]
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
