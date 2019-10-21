# -*- coding: utf-8 -*-
from flask import Flask
import json
app = Flask(__name__)


@app.route("/")
def convert():
    data = {"Success": True}
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response


if __name__ == "__main__":
    app.run()
