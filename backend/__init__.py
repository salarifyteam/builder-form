import os
import random
import string
import time

import sentry_sdk
from flask import Flask
from flask_admin import Admin
from flask_cors import CORS
from flask_restx import Api


def generate_id(prefix):
    timestamp = int(time.time() * 1000)
    random_str = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=4)
    )
    return f"{prefix}{timestamp}{random_str}"


if not os.environ.get("FLASK_ENV") == "local":
    sentry_sdk.init(
        dsn="https://f85843617cf8e6a951273f242d0f11d1@o1125048.ingest.us.sentry.io/4509127847903232",
        send_default_pii=True,
        traces_sample_rate=1.0,
        profile_session_sample_rate=1.0,
        profile_lifecycle="trace",
    )


def create_app(debug=False):
    # 프로덕션 환경에서만 Sentry 초기화
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    CORS(
        app,
        resources={
            r"/*": {
                "origins": [
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                    "https://via-dev.worked.im",
                ],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )
    app.config["FLASK_ADMIN_SWATCH"] = "cerulean"

    from .views import doc_views
    from .views.admin import dashboard
    from .views.service import create, form, list

    api.init_app(app)
    admin.init_app(app)

    from .views.admin.dashboard import register_admin_views

    register_admin_views(admin)

    api.add_namespace(create.create_ns)
    api.add_namespace(list.list_ns)
    api.add_namespace(form.form_ns)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(doc_views.bp)

    return app


api = Api(
    title="Service & Form API Documentation",
    version="1.0",
    description="빌더서비스 API 문서",
    doc="/docs",
    authorizations={
        "apikey": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "인증을 위한 토큰을 입력하세요. 예: Bearer YOUR_TOKEN",
        }
    },
    security="apikey",
)

admin = Admin(name="Form Admin", template_mode="bootstrap3")

app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
