import jwt
from datetime import datetime, timedelta
from app.core.config import Settings

settings = Settings()


async def verify_access_token(token: str):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        print("Hii")
        print(payload)
        return payload
    except jwt.ExpiredSignatureError:
        return None
