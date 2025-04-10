from flask import jsonify
from flask_restx import Namespace, Resource

from backend.auth import token_required
from backend.db import get_service_resource

form_ns = Namespace(
    path="/company/<string:company_id>/services", name="서비스 폼 조회"
)
table = get_service_resource()


@form_ns.route("/<string:service_id>/form/", strict_slashes=False)
class ServiceFormResource(Resource):
    @form_ns.doc(
        responses={
            200: "OK",
            404: "Not Found",
            500: "Internal Server Error",
        },
    )
    @token_required
    def get(self, current_user, company_id, service_id):
        # query = table.get_item(
        #     IndexName="GSI1PK-GSI1SK-index",
        #     KeyConditionExpression=Key("GSI1PK").eq(f"SERVICE#{service_id}"),
        #     FilterExpression=Attr("entityType").eq("FORM"),
        # )
        # if query.get("Items"):
        #     return jsonify(query["Items"])
        # else:
        #     return jsonify({"message": "Not Found"}), 404
        return jsonify({"message": "OK"})
