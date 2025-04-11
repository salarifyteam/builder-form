from boto3.dynamodb.conditions import Key
from flask import jsonify
from flask_restx import Namespace, Resource, fields

from backend.db import get_dynamodb_client, get_service_resource

form_ns = Namespace(
    path="/company/<string:company_id>/services", name="서비스 폼 조회"
)
table = get_service_resource()
client = get_dynamodb_client()

service_model = form_ns.model(
    "Service",
    {
        "name": fields.String(description="서비스 이름"),
        "description": fields.String(description="서비스 설명"),
    },
)
form_model = form_ns.model(
    "Form",
    {
        "fieldCategory": fields.String(description="필드 카테고리"),
        "fieldDataType": fields.String(description="필드 데이터 타입"),
        "fieldDescription": fields.String(description="필드 설명"),
        "fieldId": fields.String(description="필드 ID"),
        "fieldNumber": fields.Integer(description="필드 순서"),
        "fieldRequired": fields.Boolean(description="필드 필수 여부"),
        "fieldTitle": fields.String(description="필드 제목"),
        "fieldType": fields.String(description="필드 타입"),
    },
)

success_response = form_ns.model(
    "SuccessResponse",
    {
        "service": fields.Nested(service_model),
        "form": fields.List(fields.Nested(form_model)),
    },
)


error_response = form_ns.model(
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

not_found_response = form_ns.model(
    "NotFoundResponse",
    {
        "code": fields.String(description="에러 코드", default="NOT_FOUND"),
        "message": fields.String(
            description="에러 메시지", default="Not Found"
        ),
    },
)


@form_ns.route("/<string:service_id>/form/", strict_slashes=False)
class ServiceFormResource(Resource):
    @form_ns.doc(
        responses={
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    @form_ns.response(200, "OK", success_response)
    @form_ns.response(404, "Not Found", not_found_response)
    @form_ns.response(500, "Internal Server Error", error_response)
    # @token_required
    def get(self, company_id, service_id):
        """
        서비스 폼 조회

        서비스 고유 식별자를 기반으로 서비스 폼을 조회합니다.
        """
        try:
            service_response = table.get_item(
                Key={"PK": service_id, "SK": f"COMPANY#{company_id}"}
            )

            if not service_response.get("Item"):
                return (
                    {"message": "Service Not Found"},
                    404,
                )

            service_data = service_response["Item"]

            # 폼 데이터 조회
            form_response = table.query(
                IndexName="GSI1PK-GSI1SK-index",
                KeyConditionExpression=Key("GSI1PK").eq(
                    f"SERVICE#{service_id}"
                ),
                FilterExpression=Key("entityType").eq("FORM"),
            )

            if not form_response.get("Items"):
                return jsonify(
                    {
                        "service": {
                            "name": service_data.get("name"),
                            "description": service_data.get("description"),
                        },
                        "form": [],
                    }
                )

            form_data = form_response["Items"][0]
            form_fields = form_data.get("formSchema", [])

            # fieldNumber 기준으로 정렬
            sorted_fields = sorted(
                form_fields, key=lambda x: float(x["fieldNumber"])
            )

            # fieldNumber를 정수로 변환
            for field in sorted_fields:
                if "fieldNumber" in field:
                    field["fieldNumber"] = int(float(field["fieldNumber"]))

            return jsonify(
                {
                    "service": {
                        "name": service_data.get("name"),
                        "description": service_data.get("description"),
                    },
                    "form": sorted_fields,
                }
            )

        except Exception as e:
            return (
                jsonify({"message": "Internal Server Error", "error": str(e)}),
                500,
            )
