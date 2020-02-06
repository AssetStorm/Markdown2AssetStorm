# -*- coding: utf-8 -*-
from flask import Flask, request
from helpers import json_from_markdown
import json
app = Flask(__name__)


@app.route("/", methods=['POST'])
def convert():
    md_str = request.get_data(as_text=True)
    data = {
        "type": "conversion-container",
        "blocks": json_from_markdown(md_str)}
    print(data)
    print(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    response = app.response_class(
        response=json.dumps(data, ensure_ascii=False).encode('utf-8'),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route("/live", methods=['GET'])
def live():
    response = app.response_class(
        response="",
        status=200,
        mimetype='text/plain'
    )
    return response


if __name__ == "__main__":  # pragma: no mutate
    app.run()
