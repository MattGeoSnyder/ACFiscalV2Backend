from fastapi import HTTPException, Depends
from db import db
import MySQLdb
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Dict
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models import User

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def create_access_token(data: Dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(
        to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
    )
    return encoded_jwt


def authenticate_user(email: str, password: str):
    user = API.get_user_by_email(email).get("user")
    if not user:
        return False
    if not verify_password(password, user.get("password")):
        return False
    return user


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
        email: str = payload.get("email")
        if email is None:
            raise HTTPException(401, "Unauthorized")
    except JWTError:
        raise HTTPException(401, "Unauthorized")
    user = API.get_user_by_id(payload.get("id"))
    if user is None:
        raise HTTPException(401, "Unauthorized")
    return user


class API:
    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor
        self.error = MySQLdb.Error

    def signup(self, user):
        # with self.cursor() as cursor:
        #     cursor.execute(
        #         """
        #             SELECT * FROM users
        #             WHERE email = %s;
        #         """,
        #         (user["email"],),
        #     )

        #     existing_user = cursor.fetchone()
        existing_user = self.get_user_by_id(user.get("id"))

        if existing_user:
            raise HTTPException(
                409, f"Account already registered with email {user['email']}"
            )

        hashed_password = get_password_hash(user["password"])
        new_user = {**user, "password": hashed_password}

        with self.cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO users
                    (first_name, last_name, email, password, department_id)
                    VALUES
                    (%s, %s, %s, %s, %s);
                """,
                new_user.values(),
            )

            return {"msg": "User successfully created!"}

    def verify_token(self, form_data):
        user = API.get_user_by_email(form_data.get("email"))
        if not User:
            raise HTTPException(401, "Unauthorized")
        token = create_access_token(
            data={
                "id": user.get("id"),
                "email": user.get("email"),
                "department_id": user.get("department_id"),
            }
        )
        return token

    def get_all_departments(self):
        with self.cursor() as cursor:
            cursor.execute("SELECT * FROM departments")
            departments = cursor.fetchall()

            return departments

    def get_department_by_id(self, id: int):
        with self.cursor() as cursor:
            cursor.execute("SELECT * FROM departments WHERE id=%s", (id,))
            department = cursor.fetchone()

            return department

    def get_user_by_id(self, id: int):
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users WHERE id = %s;",
                (id,),
            )
            user = cursor.fetchone()

            return user

    def get_user_by_email(self, email: str):
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users WHERE email = %s;",
                (email,),
            )

            user = cursor.fetchone()
            return user


API = API(db)
