from fastapi import FastAPI, Request, HTTPException, status, Depends
from starlette.requests import Request
from starlette.responses import HTMLResponse
from tortoise.contrib.fastapi import register_tortoise
from tortoise import models
from models import *
from authentication import *
from emails import *

# 3465sd

# auth
from authentication import *
from fastapi.security import (OAuth2PasswordBearer, OAuth2PasswordRequestForm)

# signals
from tortoise.signals import post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient

# response classes
from fastapi.responses import HTMLResponse

# templates
from fastapi.templating import Jinja2Templates

app = FastAPI()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


@app.post('/token')
async def generate_token(request_form: OAuth2PasswordRequestForm = Depends()):
    """создаём токен"""
    token = await token_generator(request_form.username, request_form.password)
    return {"access_token": token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """проверяем текущего пользователя"""
    try:
        payload = jwt.decode(token, config_credential["SECRET"], algorithms=['HS256'])
        user = await User.get(id=payload.get("id"))
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await user


@app.post("/user/me")
async def user_login(user: user_pydanticIn = Depends(get_current_user)):
    """login пользователя"""
    business = await Business.get(owner=user)

    return {
        "status": "ok",
        "data":
        {
            "username": user.username,
            "email": user.email,
            "verified": user.is_verified,
            "joined_data": user.join_data.strtime("%b %d %Y")
        }
    }


@post_save(User)
async def create_business(sender: "Type[User]", instance: User, created: bool, using_db: "Optional[BaseDBAsyncClient]",
                          update_fields: List[str]) -> None:
    """создаём функцию для отправки сингалов для создания бизнес аккаунта при создании пользователя"""
    if created:
        business_obj = await Business.create(
            business_name=instance.username, owner=instance
        )

        await business_pydantic.from_tortoise_orm(business_obj)
        await send_email([instance.email], instance)


@app.post("/registration")
async def user_registration(user: user_pydanticIn):
    """создание пользователя"""
    user_info = user.dict(exclude_unset=True)
    user_info["password"] = get_hashed_password(user_info["password"])
    user_obj = await User.create(**user_info)
    new_user = await user_pydantic.from_tortoise_orm(user_obj)
    return {
        "status": "ok",
        "data": f"Hello {new_user.username}, we are glad to see you here. Check your email inbox to the link to confirm"
                f" your registration"
    }

# template for email verification
templates = Jinja2Templates(directory="templates")


@app.get("/verification", response_class=HTMLResponse)
async def email_verification(request: Request, token: str):
    """подтверждение почты"""
    user = await verify_token(token)
    if user and not user.is_verified:
        user.is_verified = True
        await user.save()
        return templates.TemplateResponse("verification.html", {"request": request, "username": user.username})
    raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/")
def index():
    return {"Message": "hello world"}


register_tortoise(
    app,
    db_url="sqlite://database.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True
                  )