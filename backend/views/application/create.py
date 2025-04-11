import logging
from datetime import datetime

from flask import request
from flask_restx import Namespace, Resource, fields
from marshmallow import ValidationError

from backend.db import get_dynamodb_client
from backend.utils import generate_id

from .validators import ApplicationSchema

application_ns = Namespace(
    name="신청",
    path=(
        "/api/company/<string:company_id>/service"
        "/<string:service_id>/form/<string:form_id>/applications"
    ),
)


dynamodb_client = get_dynamodb_client()


success_response = application_ns.model(
    "ApplicationCreateSuccessResponse",
    {
        "name": fields.String(required=True, description="이름"),
        "phoneNumber": fields.String(required=True, description="전화번호"),
    },
)

error_response = application_ns.model(
    "ApplicationCreateErrorResponse",
    {
        "code": fields.String(
            description="에러 코드", default="INTERNAL_SERVER_ERROR"
        ),
        "message": fields.String(
            description="에러 메시지", default="Internal Server Error"
        ),
    },
)
validate_response = application_ns.model(
    "ApplicationCreateValidateResponse",
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


field_data_model = application_ns.model(
    "FieldDataModel",
    {
        "fieldId": fields.String(required=True, description="필드 ID"),
        "fieldTitle": fields.String(required=True, description="필드 제목"),
        "fieldDescription": fields.String(
            required=True, description="필드 설명"
        ),
        "fieldCategory": fields.String(
            required=True, description="필드 카테고리"
        ),
        "fieldType": fields.String(required=True, description="필드 타입"),
        "fieldDataType": fields.String(
            required=True, description="필드 데이터 타입"
        ),
        "fieldRequired": fields.Boolean(
            required=True, description="필드 필수 여부"
        ),
        "fieldNumber": fields.Integer(required=True, description="필드 번호"),
        "fieldValue": fields.String(required=True, description="필드 값"),
    },
)

application_create_model = application_ns.model(
    "ApplicationCreateModel",
    {
        "name": fields.String(required=True, description="이름"),
        "phoneNumber": fields.String(required=True, description="전화번호"),
        "fieldData": fields.List(fields.Nested(field_data_model)),
    },
)


@application_ns.route("/create", strict_slashes=False)
class ApplicationCreateResource(Resource):
    @application_ns.expect(application_create_model)
    @application_ns.response(201, "신청서 생성 성공", success_response)
    @application_ns.response(400, "잘못된 요청", validate_response)
    @application_ns.response(500, "서버 오류", error_response)
    def post(self, company_id, service_id, form_id):
        """
        신청서 생성
        """
        application_id = generate_id()
        data = request.json
        try:
            ApplicationSchema().load(data)
        except ValidationError as e:
            return {
                "code": "VALIDATION_ERROR",
                "message": "payload 형식이 올바르지 않습니다.",
                "errors": e.messages,
            }, 400
        item = data.copy()
        try:
            dynamodb_client.put_item(
                TableName="service",
                Item={
                    "PK": {"S": application_id},
                    "SK": {"S": "STATUS#SUBMITTED"},
                    "entityType": {"S": "APPLICATION"},
                    "serviceId": {"S": service_id},
                    "formId": {"S": form_id},
                    "companyId": {"S": company_id},
                    "userId": {"N": "1"},
                    "GSI1PK": {"S": f"USER#{1}"},
                    "GSI1SK": {"S": f"APPLICATION#{application_id}"},
                    "GSI2PK": {"S": f"COMPANY#{company_id}"},
                    "GSI2SK": {"S": f"APPLICATION#{application_id}"},
                    "GSI3PK": {"S": f"SERVICE#{service_id}"},
                    "GSI3SK": {"S": f"APPLICATION#{application_id}"},
                    "createdAt": {"S": datetime.now().isoformat()},
                    "updatedAt": {"S": datetime.now().isoformat()},
                    "phoneNumber": {"S": item["phoneNumber"]},
                    "name": {"S": item["name"]},
                    "fieldData": {
                        "L": [
                            {
                                "M": {
                                    "fieldCategory": {
                                        "S": field["fieldCategory"]
                                    },
                                    "fieldDataType": {
                                        "S": field["fieldDataType"]
                                    },
                                    "fieldDescription": {
                                        "S": field["fieldDescription"]
                                    },
                                    "fieldId": {"S": field["fieldId"]},
                                    "fieldNumber": {
                                        "N": str(field["fieldNumber"])
                                    },
                                    "fieldRequired": {
                                        "BOOL": field["fieldRequired"]
                                    },
                                    "fieldTitle": {"S": field["fieldTitle"]},
                                    "fieldType": {"S": field["fieldType"]},
                                    "fieldValue": {"S": field["fieldValue"]},
                                }
                            }
                            for field in item["fieldData"]
                        ]
                    },
                },
            )
        except Exception as e:
            logging.error(e)
            return {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal Server Error",
            }, 500
        return {
            "name": item["name"],
            "phoneNumber": item["phoneNumber"],
        }, 201
