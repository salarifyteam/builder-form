import os
from functools import wraps

import jwt
from dotenv import load_dotenv
from flask import jsonify, request

load_dotenv()

# JWT 설정 - 다른 서비스와 동일한 시크릿 키 사용
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Authorization 헤더에서 토큰 추출
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        if not token:
            return jsonify(
                message="인증 토큰이 필요합니다", code="UNAUTHORIZED"
            )
        try:
            # 토큰 디코딩 - 여기서 서명 검증이 이루어집니다
            payload = jwt.decode(
                token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
            )
            current_user = payload  # 토큰에서 사용자 정보 추출
        except jwt.ExpiredSignatureError:
            return (
                jsonify(
                    message="토큰이 만료되었습니다",
                    code="UNAUTHORIZED",
                ),
                401,
            )
        except jwt.InvalidTokenError:
            return (
                jsonify(
                    message="유효하지 않은 토큰입니다",
                    code="UNAUTHORIZED",
                ),
                401,
            )
        return f(current_user, *args, **kwargs)

    return decorated
