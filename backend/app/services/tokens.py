from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import jwt
from ..config import settings


def student_token(student_id: int, course_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"student_id": student_id, "course_id": course_id, "role": "student",
                       "iat": now, "exp": now + timedelta(hours=12)}, settings.jwt_secret, algorithm="HS256")


def signed_material_url(material_id: int, student_id: int) -> str:
    expires = int(datetime.now(timezone.utc).timestamp()) + 300
    value = f"{material_id}:{student_id}:{expires}"
    signature = hmac.new(settings.jwt_secret.encode(), value.encode(), hashlib.sha256).hexdigest()
    return f"/api/v1/student/materials/{material_id}/file?student_id={student_id}&expires={expires}&signature={signature}"


def valid_material_signature(material_id: int, student_id: int, expires: int, signature: str) -> bool:
    if expires < int(datetime.now(timezone.utc).timestamp()):
        return False
    value = f"{material_id}:{student_id}:{expires}"
    expected = hmac.new(settings.jwt_secret.encode(), value.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
