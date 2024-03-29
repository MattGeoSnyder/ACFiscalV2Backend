from fastapi import (
    APIRouter,
    Form,
    Body,
)
from typing import Dict
from typing_extensions import Annotated
from ..models.UserModel import UserModel, NewUser
from ..lib.callAPI import callAPI
from ..models.TokenModel import TokenModel, Token
from pydantic import BaseModel

auth_router = APIRouter(tags=["Auth"])


@auth_router.post(
    "/token",
    response_model=Token,
)
async def get_access_token(
    username: str = Form(
        max_length=75,
        pattern=r"[a-z,A-Z]+.[a-z,A-Z]+@alleghenycounty.us$",
        description="Must use Allegheny County email, i.e: First Name.Last Name@alleghenycounty.us. Email must be less than 75 characters long.",
        examples=["Matthew.Snyder@alleghenycounty.us"],
    ),
    password: str = Form(examples=["secret1234"]),
    scope: str = Form(default="user"),
):
    token = await callAPI(
        TokenModel.verify_token,
        {"username": username, "password": password, "scope": scope},
    )
    return {"access_token": token, "type": "bearer"}


@auth_router.post(
    "/signup",
    status_code=201,
)
async def signup(new_user: Annotated[NewUser, Body]):
    token = await callAPI(TokenModel.signup, new_user.model_dump())
    return {"access_token": token, "type": "bearer"}
