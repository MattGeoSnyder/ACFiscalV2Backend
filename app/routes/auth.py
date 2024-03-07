from fastapi import (
    APIRouter,
    Form,
    Body,
)
from typing_extensions import Annotated
from ..models.UserModel import UserModel, NewUser, Token
from ..lib.callAPI import callAPI

auth_router = APIRouter(tags=["Auth"])


@auth_router.post(
    "/token",
    response_model=Token,
)
async def get_access_token(
    email: str = Form(
        max_length=75,
        pattern=r"[a-z,A-Z]+.[a-z,A-Z]+@alleghenycounty.us$",
        description="Must use Allegheny County email, i.e: First Name.Last Name@alleghenycounty.us. Email must be less than 75 characters long.",
        examples=["Matthew.Snyder@alleghenycounty.us"],
    ),
    password: str = Form(examples=["secret1234"]),
):
    token = await callAPI(
        UserModel.verify_token, {"email": email, "password": password}
    )
    return token


@auth_router.post(
    "/signup",
    status_code=201,
)
async def signup(new_user: Annotated[NewUser, Body]):
    print(new_user)
    new_user
    token = await callAPI(UserModel.signup, new_user.model_dump())
    return {"token": token, "token_type": "bearer"}
