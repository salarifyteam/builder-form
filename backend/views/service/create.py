# builder/views/main_views.py
import random
import string
import time
import uuid
from datetime import datetime

from flask import request
from flask_restx import Namespace, Resource, fields
from marshmallow import ValidationError

from backend.db import get_dynamodb_client

from .validators import (
    ServiceWithFormSchema,
)

create_ns = Namespace(path="/service", name="서비스 생성")
dynamodb_client = get_dynamodb_client()


def generate_id():
    timestamp = int(time.time() * 1000)
    random_str = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=4)
    )
    return f"{timestamp}{random_str}"


create_service_model = create_ns.model(
    "ServiceModel",
    {
        "name": fields.String(required=True, description="서비스 이름"),
        "description": fields.String(required=True, description="서비스 설명"),
    },
)

form_model = create_ns.model(
    "Form",
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
        "fieldNumber": fields.Integer(
            required=True,
            description="필드 순서",
        ),
    },
)

service_with_form_model = create_ns.model(
    "ServiceWithForm",
    {
        "companyId": fields.String(required=True, description="회사 ID"),
        "service": fields.Nested(create_service_model, required=True),
        "form": fields.Nested(form_model, required=True),
    },
)

success_response = create_ns.model(
    "SuccessResponse",
    {
        "code": fields.String(description="성공 코드", default="SUCCESS"),
        "message": fields.String(description="성공 메시지", default="Success"),
    },
)

error_response = create_ns.model(
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
validate_response = create_ns.model(
    "ValidateResponse",
    {
        "code": fields.String(
            description="검증 코드", default="VALIDATION_ERROR"
        ),
        "message": fields.String(
            description="검증 메시지",
            default="payload 형식이 올바르지 않습니다.",
        ),
    },
)


@create_ns.route("/with-form", strict_slashes=False)
class ServiceWithFormResource(Resource):
    @create_ns.doc(
        responses={
            201: "Created",
            400: "Bad Request",
            500: "Internal Server Error",
        },
    )
    @create_ns.expect(service_with_form_model)
    @create_ns.response(201, "서비스 생성 성공", success_response)
    @create_ns.response(400, "잘못된 요청", validate_response)
    @create_ns.response(500, "서버 오류", error_response)
    def post(self):
        """
        서비스+양식 생성

        요청 본문에 서비스 정보와 양식 정보를 함께 전달하면 DynamoDB에 저장합니다.
        각 서비스와 양식에는 고유 ID가 자동으로 생성됩니다.
        """
        data = request.json
        try:
            ServiceWithFormSchema().load(data)
        except ValidationError as e:
            return {
                "code": "VALIDATION_ERROR",
                "message": "payload 형식이 올바르지 않습니다.",
                "errors": e.messages,
            }, 400

        item = data.copy()
        service_id = generate_id()
        form_id = generate_id()
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
                                "SK": {"S": f"SERVICE#{service_id}"},
                                "entityType": {"S": "FORM"},
                                "createdAt": {"S": current_time},
                                "updatedAt": {"S": current_time},
                                "GSI1PK": {"S": (f"SERVICE#{service_id}")},
                                "GSI1SK": {"S": (f"FORM#{form_id}")},
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
                                                "fieldNumber": {
                                                    "N": str(
                                                        field["fieldNumber"]
                                                    )
                                                },
                                            }
                                        }
                                        for field in item["form"]
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
