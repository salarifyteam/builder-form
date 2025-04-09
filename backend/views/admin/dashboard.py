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
        response = table.scan()
        items = response.get("Items", [])
        return self.render("admin/dynamo.html", items=items)


admin.add_view(
    DynamoDBView(name="service", endpoint="service", url="/admin/service")
)
