from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from models import *
from authentication import *
# 3465sd

#signals
from tortoise.signals import post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient

app = FastAPI()


@post_save(User)
async  def create_business(sender: "Type[User]",
                           instance: User,
                           created: bool,
                           using_db: "Optional[BaseDBAsyncClient]",
                           update_fields: List[str]) -> None:
    """создаём функцию для отправки сингалов для создания бизнес аккаунта при создании пользователя"""
    if created:
        business_obj = await Business.create(
            business_name = instance.username, owner = instance
        )

        await business_pydantic.from_tortoise_orm(business_obj)


@app.post("/registration")
async def user_registration(user: user_pydanticIn):
    """создание пользователя"""
    user_info = user.dict(exclude_unset=True)
    user_info["password"] = get_hashed_password(user_info["password"])
    user_obj = await User.create(**user_info)
    new_user = await user_pydantic.from_tortoise_orm(user_obj)
    return {
        "status": "ok",
        "data" : f"Hello {new_user.username}, we are glad to see you here. Check your email inbox to the link to confirm your registration"
}


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