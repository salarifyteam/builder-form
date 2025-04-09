# builder/views/doc_views.py
from flask import Blueprint, jsonify

from backend import api

bp = Blueprint("redoc", __name__, url_prefix="")


@bp.route("/redoc/")
def redoc():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ReDoc API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {
                margin: 0;
                padding: 0;
            }
        </style>
    </head>
    <body>
        <redoc spec-url='/swagger.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """


@bp.route("/swagger.json")
def swagger_json():
    return jsonify(api.__schema__)
