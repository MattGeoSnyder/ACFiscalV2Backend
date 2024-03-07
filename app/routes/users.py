from fastapi import APIRouter, Query, Path
from ..models.UserModel import UserModel
from ..lib.callAPI import callAPI
from typing_extensions import Annotated

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get(
    "/users",
)
async def get_users(offset: Annotated[int, Query], limit: Annotated[int, Query]):
    users = await callAPI(UserModel.get_all_paginated, offset, limit)
    return {"users": users}


@user_router.get(
    "/users/{user_id}",
)
async def get_user_by_id(
    user_id: Annotated[int, Path(title="The id of the user to get")]
):
    user = await callAPI(UserModel.get_by_id, user_id)
    return {"user": user}
