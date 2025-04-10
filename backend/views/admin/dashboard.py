import logging

import boto3
from flask import Blueprint
from flask_admin import BaseView, expose
from flask_restx import Namespace

bp = Blueprint("admin_blueprint", __name__, url_prefix="/admin")
admin_ns = Namespace("admin", description="관리자 관련 API")
table = boto3.resource("dynamodb").Table("service")


# 관리자 뷰 설정
class DynamoDBView(BaseView):
    @expose("/")
    def index(self):
        try:
            response = table.scan()
            items = response.get("Items", [])
            return self.render("admin/dynamo.html", items=items)
        except Exception as e:
            logging.error(f"Error in DynamoDBView: {str(e)}")  # 상세 에러 로그
            return str(e), 500


def register_admin_views(admin):
    admin.add_view(
        DynamoDBView(
            name="Service",
            endpoint="service",
            url="/admin/service",
        )
    )
