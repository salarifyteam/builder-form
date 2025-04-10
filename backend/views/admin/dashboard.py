import boto3
from flask import Blueprint
from flask_admin import BaseView, expose
from flask_restx import Namespace

from backend import admin

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
            # 전체 템플릿 경로 지정
            return self.render("/admin/dynamo.html", items=items)
        except Exception as e:
            print(f"Error: {str(e)}")
            return str(e), 500


admin.add_view(
    DynamoDBView(
        name="service",
        endpoint="service",
        url="/admin/service",
        category="Service",
    )
)
