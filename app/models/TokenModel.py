from datetime import datetime, timedelta, timezone
from typing import List, Union, Dict
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
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
    id: int
    department_id: int
    scope: str


class TokenModel(CRUDModel):

    def create_access_token(data: Dict):
        to_encode = data.copy()
        encoded_jwt = jwt.encode(
            to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
        )
        return encoded_jwt

    @staticmethod
    async def get_user_by_email(email: str):
        with TokenModel._cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users WHERE email = %s;",
                (email,),
            )

            user = cursor.fetchone()
            return user

    @staticmethod
    # here username is email
    async def verify_token(form_data):
        user = await TokenModel.get_user_by_email(form_data.get("username"))
        if not user:
            raise HTTPException(401, "Unauthorized")
        token = TokenModel.create_access_token(
            data={
                "id": user.get("id"),
                "department_id": user.get("department_id"),
                "scope": user.get("scope"),
            }
        )
        return token

    @staticmethod
    async def decode_token(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(token, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
            username: str = payload.get("username")
            if username is None:
                raise HTTPException(401, "Unauthorized")
        except JWTError:
            raise HTTPException(401, "Unauthorized")
        user = await TokenModel.get_user_by_email(payload.get("username"))
        if user is None:
            raise HTTPException(401, "Unauthorized")
        return payload
