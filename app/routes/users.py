from fastapi import APIRouter, Query, Path
from models.UserModel import UserModel
from lib.callAPI import callAPI
from typing import Union
from typing_extensions import Annotated

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get(
    "/",
)
async def get_users(
    offset: Annotated[Union[int, None], Query], limit: Annotated[Union[int], Query]
):
    users = await callAPI(UserModel.get_all_paginated, offset, limit)
    return {"users": users}


@user_router.get(
    "/{user_id}",
)
async def get_user_by_id(
    user_id: Annotated[int, Path(title="The id of the user to get")]
):
    user = await callAPI(UserModel.get_by_id, user_id)
    return {"user": user}
