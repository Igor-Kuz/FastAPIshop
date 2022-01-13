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


async def verify_password(plain_password, hashed_password):
    """проверка пароля с паролем в ДБ"""
    return password_context.verify(plain_password, hashed_password)


async def authenticate_user(username, password):
    """аутентификация пользователя"""
    user = await User.get(username=username)
    if user and verify_password(password, user.password):
        return user
    return False


async def token_generator(username: str, password: str):
    """генератор токена"""
    user = await authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {
        "id": user.id,
        "username": user.username
    }

    token = jwt.encode(token_data, config_credential["SECRET"])
    return token
