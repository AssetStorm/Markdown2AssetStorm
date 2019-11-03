# -*- coding: utf-8 -*-
from flask import Flask
from helpers import json_from_markdown
import json
app = Flask(__name__)


@app.route("/")
def convert(md_str=""):
    data = {"type": "block-blocks",
            "blocks": json_from_markdown(md_str)}
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response


if __name__ == "__main__":
    app.run()
