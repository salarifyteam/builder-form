# builder/views/main_views.py
import random
import string
import time
import uuid
from datetime import datetime

import boto3
from flask import Blueprint, request
from flask_restx import Namespace, Resource, fields

bp = Blueprint("main", __name__, url_prefix="/api")
main_ns = Namespace("api/services", description="서비스 관련 API")
dynamodb_client = boto3.client("dynamodb")


def generate_id(prefix):
    timestamp = int(time.time() * 1000)
    random_str = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=4)
    )
    return f"{prefix}{timestamp}{random_str}"


# 모델 정의
service_model = main_ns.model(
    "Service",
    {
        "name": fields.String(required=True, description="서비스 이름"),
        "description": fields.String(required=True, description="서비스 설명"),
    },
)

form_field_model = main_ns.model(
    "FormField",
    {
        "fieldTitle": fields.String(required=True, description="필드 제목"),
        "fieldDescription": fields.String(
            required=True, description="필드 설명"
        ),
        "fieldCategory": fields.String(
            required=True,
            description="주관식: TEXT, 객관식: CHOICE",
            enum=["TEXT"],
        ),
        "fieldType": fields.String(
            required=True,
            description="단답형: SHORT, 서술형: LONG",
            enum=["SHORT", "LONG"],
        ),
        "fieldDataType": fields.String(
            required=True,
            description="숫자만 입력: NUM, 그 외: TEXT",
            enum=["NUM", "TEXT"],
        ),
        "fieldRequired": fields.Boolean(
            required=True,
            description="필드 필수 여부",
        ),
    },
)

form_model = main_ns.model(
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

service_with_form_model = main_ns.model(
    "ServiceWithForm",
    {
        "companyId": fields.String(required=True, description="회사 ID"),
        "service": fields.Nested(service_model, required=True),
        "form": fields.Nested(form_model, required=True),
    },
)

success_response = main_ns.model(
    "SuccessResponse",
    {
        "code": fields.String(description="성공 코드", default="SUCCESS"),
        "message": fields.String(description="성공 메시지", default="Success"),
    },
)

error_response = main_ns.model(
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


@main_ns.route("/with-form", strict_slashes=False)
class ServiceWithFormResource(Resource):
    @main_ns.doc(
        "create_service_with_form",
        description="서비스와 양식을 함께 생성합니다",
        responses={
            201: "Created",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    @main_ns.expect(service_with_form_model)
    @main_ns.response(201, "서비스 생성 성공", success_response)
    @main_ns.response(400, "잘못된 요청", error_response)
    @main_ns.response(500, "서버 오류", error_response)
    def post(self):
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
                                "GSI1PK": {
                                    "S": (f"COMPANY#{item['companyId']}")
                                },
                                "GSI1SK": {"S": (f"SERVICE#{service_id}")},
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
                                                "fieldTitle": {
                                                    "S": field["fieldTitle"]
                                                },
                                                "fieldDescription": {
                                                    "S": field[
                                                        "fieldDescription"
                                                    ]
                                                },
                                                "fieldCategory": {"S": "text"},
                                                "fieldType": {
                                                    "S": field["fieldType"]
                                                },
                                                "fieldDataType": {
                                                    "S": field["fieldDataType"]
                                                },
                                                "fieldId": {
                                                    "S": str(uuid.uuid4())
                                                },
                                                "fieldRequired": {
                                                    "BOOL": field[
                                                        "fieldRequired"
                                                    ]
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
