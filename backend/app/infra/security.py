import uuid

from pwdlib import PasswordHash
from datetime import datetime, timedelta, timezone
import jwt
from app.infra.config import settings

password_hash = PasswordHash.recommended()

def hash_password(plain) -> str:
    hash =  password_hash.hash(plain) 
    return hash

def verify_password(plain, hash) -> bool:
    return password_hash.verify(plain, hash)

def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc) 
    expire =now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,   # subject = user id
        "exp": expire,    # expiry time
        "iat": now,  
        "jti": str(uuid.uuid4()),  
    }

    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_access_token(token: str) -> dict:
    try:
        decoded_payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return decoded_payload
        
    except jwt.ExpiredSignatureError:
        print("The token has expired.")
    except jwt.InvalidTokenError:
        print("Invalid token structure or signature.")
 