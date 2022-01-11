from fastapi import BackgroundTasks, UploadFile, File, Form, Depends, HTTPException, status

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import dotenv_values
from pydantic import BaseModel, EmailStr
from typing import List
from models import User
import jwt

config_credentials = dotenv_values(".env")

conf = ConnectionConfig(
    MAIL_USERNAME=config_credentials["EMAIL"],
    MAIL_PASSWORD=config_credentials["PASSWORD"],
    MAIL_FROM=config_credentials["EMAIL"],
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True
)


class EmailSchema(BaseModel):
    """отправка почты"""
    email: List[EmailStr]


async def send_email(email: List, instance: User):
    token_data = {
        "id": instance.id,
        "username": instance.username
    }

    token = jwt.encode(token_data, config_credentials["SECRET"], algorithm="HS256")

    template = f"""
        <!DOCTYPE html>
        <html>
            <head>
            </head>
            <body>
                <div style = "display: flex; align-items: center; justify-content:
                                center; flex-direction: column">
                    <h3> Account Verificcation </h3>
                    <br>
                    <p> Thank you, please click on link </p>
                    <a href="http://localhost:8000/verification/?token={token}">Verify</a>
                </div>
            </body>
        </html>
    """

    message = MessageSchema(
        subject="Shop verification",
        recipients=email,  # Список получателей
        body=template,
        subtype="html"
    )

    fastmail = FastMail(conf)
    await fastmail.send_message(message=message)