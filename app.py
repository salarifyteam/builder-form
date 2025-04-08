import random
import string
import time
import uuid
from datetime import datetime

import boto3
from flask import Flask, jsonify, render_template, request
from flask_admin import Admin, BaseView, expose
from flask_restx import Api, Resource, fields

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

# API 문서화를 위한 설정
authorizations = {
    "apikey": {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "인증을 위한 토큰을 입력하세요. 예: Bearer YOUR_TOKEN",
    }
}

# API 설정
api = Api(
    app,
    version="1.0",
    title="Service & Form API Documentation",
    description="프론트엔드 개발자를 위한 서비스 및 양식 관리 API 문서",
    doc="/docs",  # Swagger UI URL
    authorizations=authorizations,
    security="apikey",  # 모든 엔드포인트에 기본적으로 인증 요구
)

# 네임스페이스 생성
service_ns = api.namespace("api/service", description="서비스 관련 엔드포인트")


# 관리자 뷰 설정
class DynamoDBView(BaseView):
    @expose("/")
    def index(self):
        response = table.scan()
        items = response.get("Items", [])
        return self.render("admin/dynamo.html", items=items)


admin = Admin(app, name="Form Admin", template_mode="bootstrap3")
admin.add_view(DynamoDBView(name="service", endpoint="service"))


# 메인 라우트
@app.route("/")
def index():
    return jsonify({"message": "Form API가 실행 중입니다"})


@app.route("/admin-login")
def admin_login():
    return render_template("admin_login.html")


# API 모델 정의
service_model = api.model(
    "Service",
    {
        "name": fields.String(required=True, description="서비스 이름"),
        "description": fields.String(required=True, description="서비스 설명"),
    },
)

form_field_model = api.model(
    "FormField",
    {
        "fieldTitle": fields.String(required=True, description="필드 제목"),
        "fieldDescription": fields.String(
            required=True, description="필드 설명"
        ),
    },
)

form_model = api.model(
    "Form",
    {
        "name": fields.String(required=True, description="양식 이름"),
        "description": fields.String(required=True, description="양식 설명"),
        "formSchema": fields.List(
            fields.Nested(form_field_model),
            required=True,
            description="양식 필드 스키마",
        ),
    },
)

service_with_form_model = api.model(
    "ServiceWithForm",
    {
        "service": fields.Nested(service_model, required=True),
        "form": fields.Nested(form_model, required=True),
    },
)

bad_request_response = api.model(
    "BadRequestResponse",
    {
        "code": fields.String(description="에러 코드", default="BAD_REQUEST"),
        "message": fields.String(
            description="에러 메시지", default="No data provided"
        ),
    },
)

# 응답 모델 정의
success_response = api.model(
    "SuccessResponse",
    {
        "code": fields.String(description="성공 코드", default="SUCCESS"),
        "message": fields.String(description="성공 메시지", default="Success"),
    },
)

error_response = api.model(
    "ErrorResponse",
    {
        "code": fields.String(
            description="에러 코드", default="INTERNAL_SERVER_ERROR"
        ),
        "message": fields.String(
            description="에러 메시지", default="Internal Server Error"
        ),
    },
)


# API 엔드포인트 정의
@service_ns.route("/with-form/")
class ServiceWithFormResource(Resource):
    @service_ns.doc(
        "create_service_with_form",
        description="서비스와 양식을 함께 생성합니다",
        responses={
            201: "Created",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    @service_ns.expect(service_with_form_model)
    @service_ns.response(201, "서비스 생성 성공", success_response)
    @service_ns.response(400, "잘못된 요청", error_response)
    @service_ns.response(500, "서버 오류", error_response)
    @token_required
    def post(self, data):
        """
        서비스와 양식을 함께 생성합니다.

        요청 본문에 서비스 정보와 양식 정보를 함께 전달하면 DynamoDB에 저장합니다.
        각 서비스와 양식에는 고유 ID가 자동으로 생성됩니다.
        """
        data = request.json
        if not data:
            return {"code": "BAD_REQUEST", "message": "No data provided"}, 400

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
                                "description": {
                                    "S": item["form"]["description"]
                                },
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
                                                    "S": field[
                                                        "fieldDescription"
                                                    ]
                                                },
                                                "fieldRequired": {
                                                    "BOOL": True
                                                },
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
            return {
                "code": "SUCCESS",
                "message": "SUCCESS",
            }, 201
        except Exception as e:
            print(e)
            return {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal Server Error",
            }, 500


# ReDoc을 위한 설정
@app.route("/redoc/")
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


@app.route("/swagger.json")
def swagger_json():
    return jsonify(api.__schema__)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
