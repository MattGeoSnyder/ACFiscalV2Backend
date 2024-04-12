from datetime import datetime, timedelta, timezone
from typing import List, Union, Dict
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import (
    OAuth2PasswordBearer,
    SecurityScopes,
)
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError
from typing_extensions import Annotated
from .CRUDModel import CRUDModel

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "user": "Change self, post ROC, view claimed ROCs by dept",
        "admin": "Change other users, edit ACH Credits, view all ROCs, delete ROCs",
    },
)


class Token(BaseModel):
    access_token: str
    type: str


class TokenData(BaseModel):
    user_id: str
    username: str
    department_id: int
    scope: List[str]


class TokenModel(CRUDModel):

    def create_access_token(data: Dict):
        to_encode = data.copy()
        encoded_jwt = jwt.encode(
            to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
        )
        return encoded_jwt

    def get_password_hash(password: str):
        return pwd_context.hash(password)

    @staticmethod
    async def get_user_by_email(email: str):
        with TokenModel._cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id, scope FROM users WHERE email = %s;",
                (email,),
            )

            user = cursor.fetchone()
            return user

    @classmethod
    # here username is email
    async def verify_credentials(cls, form_data):
        print(form_data)
        user = await TokenModel.get_user_by_email(form_data.get("username"))
        if not user:
            raise HTTPException(401, "Unauthorized from verify_token")
        print(user)
        payload = {
            "user_id": user.get("id", "1"),
            "username": form_data.get("username"),
            "department_id": user.get("department_id"),
            "scope": user.get("scope", ""),
        }
        token = TokenModel.create_access_token(data={"id": user.get("id"), **payload})
        return {"access_token": token, "payload": payload}

    @staticmethod
    async def decode_token(
        security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)
    ):
        print(security_scopes.scopes)
        if security_scopes.scopes:
            authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
        else:
            authenticate_value = "Bearer"
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": authenticate_value},
            )
        try:
            payload = jwt.decode(token, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
            username: str = payload.get("username")
            token_scopes = payload.get("scope", "").split(" ")

            print(payload)
            print(token_scopes)
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        user = await TokenModel.get_user_by_email(payload.get("username"))
        if user is None:
            raise credentials_exception
        for scope in token_scopes:
            if scope not in security_scopes.scopes:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not enough permissions",
                    headers={"WWW-Authenticate": authenticate_value},
                )
        return payload

    # TODO: Need to ensure user name
    @classmethod
    async def signup(cls, user):
        existing_user = await cls.get_user_by_email(user.get("email"))

        if existing_user:
            raise HTTPException(
                409, f"Account already registered with email {user['email']}"
            )

        hashed_password = cls.get_password_hash(user["password"])
        new_user = {**user, "password": hashed_password}

        with cls._cursor() as cursor:
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

            return {"access_token": token, "token_type": "bearer"}
