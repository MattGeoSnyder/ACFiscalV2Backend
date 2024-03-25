from .CRUDModel import CRUDModel
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from jose import JWTError, jwt
from typing import Dict
from enum import Enum
from .TokenModel import TokenModel
import os


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


class NewUser(BaseModel):
    first_name: str = Field(max_length=25, examples=["First Name"])
    last_name: str = Field(max_length=25, examples=["Last Name"])
    email: str = Field(
        max_length=75,
        pattern=r"[a-z,A-Z]+.[a-z,A-Z]+@alleghenycounty.us$",
        description="Must use Allegheny County email. Email must be less than 75 characters long.",
        examples=["Matthew.Snyder@alleghenycounty.us"],
    )
    password: str = Field(examples=["secret1234"])
    department_id: int = Field(gt=0, examples=[1])

    model_config = {
        "examples": [
            {
                "first_name": "Matthew",
                "last_name": "Snyder",
                "email": "Matthew.Snyder@alleghenycounty.us",
                "password": "secret1234",
                "department_id": 1,
            }
        ]
    }


class User(NewUser):
    id: int = Field(gt=0)
    password: str = Field(exclude=True)
    scope = Field(default="user")


class UserPermissions(BaseModel):
    id: int = Field(gt=0)
    department: str


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def authenticate_user(email: str, password: str):
    user = UserModel.get_user_by_email(email).get("user")
    if not user:
        return False
    if not verify_password(password, user.get("password")):
        return False
    return user


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
        username: str = payload.get("email")
        if username is None:
            raise HTTPException(401, "Unauthorized")
    except JWTError:
        raise HTTPException(401, "Unauthorized")
    user = UserModel.get_user_by_id(payload.get("id"))
    if user is None:
        raise HTTPException(401, "Unauthorized")
    return user


class UserModel(CRUDModel):

    _tablename = "users"

    def __init__(self):
        super().__init__("users")

    @staticmethod
    async def signup(user):
        # with cursor() as cursor:
        #     cursor.execute(
        #         """
        #             SELECT * FROM users
        #             WHERE email = %s;
        #         """,
        #         (user["email"],),
        #     )

        #     existing_user = cursor.fetchone()
        existing_user = await UserModel.get_user_by_email(user.get("email"))

        if existing_user:
            raise HTTPException(
                409, f"Account already registered with email {user['email']}"
            )

        hashed_password = get_password_hash(user["password"])
        new_user = {**user, "password": hashed_password}

        with UserModel._cursor as cursor:
            cursor.execute(
                """
                    INSERT INTO users
                    (first_name, last_name, email, password, department_id)
                    VALUES
                    (%s, %s, %s, %s, %s);
                """,
                new_user.values(),
            )
            id = cursor.lastrowid
            token = TokenModel.create_access_token(
                data={
                    "id": id,
                    "department_id": user.get("department_id"),
                    "scope": user.get("scope"),
                }
            )

            return {"acess_token": token, "token_type": "bearer"}

    @staticmethod
    async def get_user_by_id(id: int):
        with UserModel._cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users WHERE id = %s;",
                (id,),
            )
            user = cursor.fetchone()

            return user

    @staticmethod
    async def get_user_by_email(email: str):
        with UserModel._cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users WHERE email = %s;",
                (email,),
            )

            user = cursor.fetchone()
            return user

    @staticmethod
    async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
        try:
            payload = jwt.decode(token, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
            email: str = payload.get("email")
            if email is None:
                raise HTTPException(401, "Unauthorized")
        except JWTError:
            raise HTTPException(401, "Unauthorized")
        user = UserModel.get_user_by_email(email)
        if user is None:
            raise HTTPException(401, "Unauthorized")
        return user
