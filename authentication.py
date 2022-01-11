from passlib.context import CryptContext
import jwt
from dotenv import dotenv_values
from fastapi import HTTPException, status
from models import User

config_credential = dotenv_values(".env")

password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_hashed_password(password):
    """'хэшироване пароля пользователя"""
    return password_context.hash(password)


def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)


async def verify_token(token:str):
    """создание подтверждающего токена"""
    try:
        payload = jwt.decode(token, config_credential['SECRET'], algorithms=['HS256'])
        user = await User.get(id = payload.get('id'))
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user