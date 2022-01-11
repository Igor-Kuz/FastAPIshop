from passlib.context import CryptContext

password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_hashed_password(password):
    """'хэшироване пароля пользователя"""
    return password_context.hash(password)