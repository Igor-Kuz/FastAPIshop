## Shop project built with FastAPI 
### This repository contains code of API for small e-commerce shop and built on the top of FastAPI framework.
### In this repository implemented such functions as:
   1) User registration with OAuth2, passlib[bcrypt];
   2) Sending verification email to confirm user registration with jwt;
   3) Creating supplier company;
   4) User login/logout;
   5) Uploading images for user profile;
   6) Uploading images of products;
   7) CRUD functionality.
   
### Development tools
#### stak:
- Python >= 3.8
- fastapi>=0.70.0
- fastapi-mail>=1.0.2
- Jinja2>=3.0.3
- Pillow>=9.0.0
- PyJWT>=2.3.0
- python-dotenv>=0.19.2
- starlette>=0.16.0
- tortoise-orm>=0.18.1
- uvicorn>=0.16.0
- passlib>=1.7.4
- sqlite3
#### To run this repository clone it via
    git clone https://github.com/Igor-Kuz/FastAPIshop.git   
#### After cloning this repository don't forget to give it *!
#### To run code just create and activate your virtual environment
#### Then install requirement libraries from requirements.txt file wia
    pip install -r requirements.txt
#### Create .env file and input there your sensitive data
#### Don't forget to create in project root static directory with images directory inside it to upload images there.
#### And then to run your code use:
    uvicorn mani:app
##### or
    uvicorn main:app --reload
##### to use autorestart after changing code
#### To look through autodocumentation please visit
    localhos:8000/docs 
#### and you'll be redirected to swagger documentation or use 
    localhost:8000/redoc 
#### for alternative version.