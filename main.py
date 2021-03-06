from fastapi import FastAPI, Request, HTTPException, status, Depends
from starlette.requests import Request
from starlette.responses import HTMLResponse
from tortoise.contrib.fastapi import register_tortoise
from tortoise import models
from models import *
from authentication import *
from emails import *


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

# upload images
from fastapi import File, UploadFile
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image

# CORS headers
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS url
origins = [
    'http://localhost:3000'
]

# adding middleware
app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=['*'],
                   allow_headers=['*']
                   )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

# config for static files
app.mount("/static", StaticFiles(directory="static"), name="static")


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
            headers={"WWW-Authenticate": "Bearer"}
        )
    return await user


@app.post("/user/me")
async def user_login(user: user_pydanticIn = Depends(get_current_user)):
    """login пользователя"""
    business = await Business.get(owner=user)
    logo = business.logo
    logo_path = "localhost:8000/static/images"+logo

    return {
        "status": "ok",
        "data":
        {
            "username": user.username,
            "email": user.email,
            "verified": user.is_verified,
            "joined_data": user.join_data.strtime("%b %d %Y"),
            "logo": logo_path
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
            headers={"WWW-Authenticate": "Bearer"}
        )


@app.get("/")
def index():
    return {"Message": "hello world"}


@app.post("/uplloadfile/profile")
async def create_upload_file(file: UploadFile = File(...),
                             user: user_pydantic = Depends(get_current_user)):
    """загрузка аватара пользователя"""
    FILEPATH = "./static/images"
    filename = file.filename
    extension = filename.split(".")[1]

    if extension not in ["png", "jpg"]:
        return {"status": "error", "detail": "File extension not allowed"}

    token_name = secrets.token_hex(10)+"." + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()

    with open(generated_name, "wb") as file:
        file.write(file_content)

    img = Image.open(generated_name)
    img = img.resize(size=(150, 150))
    img.save(generated_name)
    file.close()

    business = await Business.get(owner=user)
    owner = await business.owner
    if owner == user:
        business.logo = token_name
        await business.save()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated to do this",
            headers={"WWW-Authenticate": "Bearer"}
        )
    file_url = "localhost:8000" + generated_name[1:]
    return {"status": "ok", "filename": file_url}


@app.post("/uploadfile/product/{id}")
async def create_upload_productfile(id: int, file: UploadFile = File(...),
                                    user: user_pydantic = Depends(get_current_user)):
    """загрузка изображения продукта"""
    FILEPATH = "./static/images"
    filename = file.filename
    extension = filename.split(".")[1]

    if extension not in ["png", "jpg"]:
        return {"status": "error", "detail": "File extension not allowed"}

    token_name = secrets.token_hex(10) + "." + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()

    with open(generated_name, "wb") as file:
        file.write(file_content)

    img = Image.open(generated_name)
    img = img.resize(size=(150, 150))
    img.save(generated_name)
    file.close()
    product = await Product.get(id=id)
    business = await product.business
    owner = await business.owner

    if owner == user:
        product.product_image = token_name
        await product.save()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated to do this",
            headers={"WWW-Authenticate": "Bearer"}
        )
    file_url = "localhost:8000" + generated_name[1:]
    return {"status": "ok", "filename": file_url}


# CRUD
@app.post("/product")
async def add_new_product(product: product_pydanticIn,
                          user: user_pydantic = Depends(get_current_user)):
    """добавление продукта"""
    product = product.dict(exclude_unset=True)

    if product["original_price"] > 0:
        product["percentage_discount"] = ((product["original_price"] - product["new_price"])
                                          / product["original_price"]) * 100

        product_obj = await Product.create(**product, business=user)
        product_obj = await product_pydantic.from_tortoise_orm(product_obj)
        return {"status": "ok", "data": product_obj}

    else:
        return {"status": "error"}


@app.get("/products")
async def get_products():
    """получение данных прдуктов"""
    response = await product_pydantic.from_queryset(Product.all())
    return {"status": "ok", "data": response}


@app.get("/product/{id}")
async def get_single_product(id: int):
    """получение информации о конкретном продукте"""
    product = await Product.get(id=id)
    business = await product.business
    owner = await business.owner
    response = await product_pydantic.from_queryset_single(Product.get(id=id))
    return {
        "status": "ok",
        "data": {
            "product_details": response,
            "business_details": {
                "name": business.business_name,
                "city": business.city,
                "region": business.region,
                "description": business.business_description,
                "logo": business.logo,
                "owner_id": owner.id,
                "business_id": business.id,
                "email": owner.email,
                "join_date": owner.join_date.strftime("%b %d %Y")
            }
        }
    }


@app.delete("/product/{id}")
async def delete_product(id: int, user: user_pydantic = Depends(get_current_user)):
    """удаление продукта"""
    product = await Product.get(id=id)
    business = await product.business
    owner = await business.owner
    if user == owner:
        await product.delete()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated to do this",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return {"status": "ok"}


@app.put("/product/{id}")
async def update_product(id: int,
                         update_info: product_pydanticIn,
                         user: user_pydantic = Depends(get_current_user)):
    """обновление информации о продукте"""
    product = await Product.get(id=id)
    business = await product.business
    owner = await business.owner
    update_info = update_info.dict(exclude_unset=True)
    update_info["date_published"] = datetime.utcnow()
    if user == owner and update_info["original_price"] > 0:
        update_info["percentage_discount"] = \
            ((update_info["original_price"]-update_info["new_price"]) / update_info["original_price"]) * 100
        product = await product.update_from_dict(update_info)
        await product.save()
        response = await product_pydantic.from_tortoise_orm(product)
        return {"status": "ok", "data": response}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated to do this",
            headers={"WWW-Authenticate": "Bearer"}
        )


@app.put("update_business/{id}")
async def update_business(id: int, update_business: business_pydanticIn,
                          user: user_pydantic = Depends(get_current_user)):
    """Обновление информации о бизнессе"""
    update_business = update_business.dict()
    business = await Business.get(id=id)
    business_owner = await business.owner
    if user == business_owner:
        await business.update_from_dict(update_business)
        await business.save()
        response = await business_pydantic.from_tortoise_orm(business)
        return {"status": "ok", "data": response}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated to do this",
            headers={"WWW-Authenticate": "Bearer"}
        )


@app.delete("delete_business/{id}")
async def delete_business(id: int, user: user_pydantic = Depends(get_current_user)):
    """удаление бизнесса"""
    business = await Business.get(id=id)
    business_owner = await business.owner
    if user == business_owner:
        await business.delete()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated to do this",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return {"status": "ok"}


register_tortoise(
    app,
    db_url="sqlite://database.sqlite3",
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True
                  )