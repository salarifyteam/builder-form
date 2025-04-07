import random
import string
import time
import uuid
from datetime import datetime

import boto3
from flask import Flask, jsonify, render_template, request
from flask_admin import Admin, BaseView, expose

from auth import token_required


def generate_id(prefix):
    timestamp = int(time.time() * 1000)
    random_str = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=4)
    )
    return f"{prefix}{timestamp}{random_str}"


app = Flask(__name__)
app.config["FLASK_ADMIN_SWATCH"] = "cerulean"
dynamodb_client = boto3.client("dynamodb")
table = boto3.resource("dynamodb").Table("service")


class DynamoDBView(BaseView):
    @expose("/")
    def index(self):
        response = table.scan()
        items = response.get("Items", [])
        return self.render("admin/dynamo.html", items=items)


admin = Admin(app, name="Form Admin", template_mode="bootstrap3")
admin.add_view(DynamoDBView(name="service", endpoint="service"))


@app.route("/")
def index():
    return jsonify({"message": "Form API가 실행 중입니다"})


@app.route("/admin-login")
def admin_login():
    return render_template("admin_login.html")


@app.route("/api/service/with-form/", methods=["POST"])
@token_required
def create_service_with_form():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    item = data.copy()
    service_id = generate_id("SVC")
    form_id = generate_id("FORM")
    current_time = datetime.now().isoformat()
    try:
        dynamodb_client.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "Item": {
                            "PK": {"S": service_id},
                            "SK": {"S": "METADATA"},
                            "entityType": {"S": "SERVICE"},
                            "name": {"S": item["service"]["name"]},
                            "description": {
                                "S": item["service"]["description"]
                            },
                            "createdAt": {"S": current_time},
                            "updatedAt": {"S": current_time},
                        },
                        "TableName": "service",
                    },
                },
                {
                    "Put": {
                        "Item": {
                            "PK": {"S": form_id},
                            "SK": {"S": service_id},
                            "entityType": {"S": "FORM"},
                            "name": {"S": item["form"]["name"]},
                            "description": {"S": item["form"]["description"]},
                            "createdAt": {"S": current_time},
                            "updatedAt": {"S": current_time},
                            "formSchema": {
                                "L": [
                                    {
                                        "M": {
                                            "fieldId": {
                                                "S": str(uuid.uuid4())
                                            },
                                            "fieldType": {"S": "text"},
                                            "fieldTitle": {
                                                "S": field["fieldTitle"]
                                            },
                                            "fieldDescription": {
                                                "S": field["fieldDescription"]
                                            },
                                            "fieldRequired": {"BOOL": True},
                                        }
                                    }
                                    for field in item["form"]["formSchema"]
                                ]
                            },
                        },
                        "TableName": "service",
                    }
                },
            ],
        )
        return jsonify({"message": "Service created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
