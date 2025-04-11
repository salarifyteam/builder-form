from boto3.dynamodb.conditions import Key
from flask import jsonify
from flask_restx import Namespace, Resource

from backend.db import get_dynamodb_client, get_service_resource

form_ns = Namespace(
    path="/company/<string:company_id>/services", name="서비스 폼 조회"
)
table = get_service_resource()
client = get_dynamodb_client()


@form_ns.route("/<string:service_id>/form/", strict_slashes=False)
class ServiceFormResource(Resource):
    @form_ns.doc(
        responses={
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    # @token_required
    def get(self, company_id, service_id):
        try:
            # 서비스 메타데이터 조회
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
