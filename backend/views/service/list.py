from boto3.dynamodb.conditions import Attr, Key
from flask_restx import Namespace, Resource, fields

from backend.auth import token_required
from backend.db import get_service_resource

list_ns = Namespace(
    name="서비스 조회",
    path="/api/services",
)
table = get_service_resource()


service_model = list_ns.model(
    "Service",
    {
        "name": fields.String(required=True, description="서비스 이름"),
        "description": fields.String(required=True, description="서비스 설명"),
        "createdAt": fields.String(required=True, description="서비스 생성일"),
        "PK": fields.String(required=True, description="서비스 고유 식별자"),
    },
)
service_list_model = list_ns.model(
    "ServiceList",
    {
        "total": fields.Integer(required=True, description="서비스 총 개수"),
        "services": fields.List(fields.Nested(service_model)),
    },
)


success_response = list_ns.model(
    "SuccessResponse",
    {
        "code": fields.String(description="성공 코드", default="SUCCESS"),
        "message": fields.String(description="성공 메시지", default="Success"),
    },
)

error_response = list_ns.model(
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


@list_ns.route("/company/<int:company_id>", strict_slashes=False)
class ServiceListResource(Resource):
    @list_ns.doc("list_services")
    @list_ns.response(200, "서비스 목록 조회 성공", service_list_model)
    @list_ns.response(500, "서버 오류", error_response)
    @token_required
    def get(self, request, company_id):
        """
        회사 서비스 목록 조회

        회사 고유 식별자를 기반으로 회사 서비스 목록을 조회합니다.
        """
        query = table.query(
            IndexName="GSI1PK-GSI1SK-index",
            KeyConditionExpression=Key("GSI1PK").eq(f"COMPANY#{company_id}"),
            FilterExpression=Attr("entityType").eq("SERVICE"),
            ProjectionExpression=(
                "#serviceName,"
                "#serviceCreatedAt,"
                "#servicePK,"
                "#serviceDescription"
            ),
            ExpressionAttributeNames={
                "#serviceName": "name",
                "#serviceDescription": "description",
                "#serviceCreatedAt": "createdAt",
                "#servicePK": "PK",
            },
        )
        response = {
            "total": query["Count"],
            "services": query["Items"],
        }
        return response
