from fastapi import APIRouter, Depends, Body, UploadFile, Query, Security, Form, File
from lib.callAPI import callAPI
from models.ACHModel import (
    ACHModel,
    NewAchCredit,
    ACHCredit,
    NewCreditDescription,
    AchSearchParams,
)
from pydantic import BaseModel, Field
from typing import Union
from typing_extensions import Annotated
from models.TokenModel import TokenModel, TokenData
from lib.constants import MAX_QUERY_LENGTH

ach_router = APIRouter(prefix="/ach", tags=["ACH Credits"])


@ach_router.get("/")
async def search_ach_credits(
    token: Annotated[
        TokenData, Security(TokenModel.decode_token, scopes=["user", "admin"])
    ],
    params: Annotated[AchSearchParams, Depends()],
):
    ach_credits = await callAPI(ACHModel.search_ach_credits, params)
    return {"ach_credits": ach_credits}


@ach_router.post(
    "/",
)
async def post_ach_credit(
    ach_credit: Annotated[ACHCredit, Body()],
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])],
):
    await callAPI(ACHModel.add, ach_credit)
    return {"msg": "Credit successfully posted"}


@ach_router.patch(
    "/",
)
async def patch_ach_credit(
    ach_credit_id: Annotated[int, Body()],
    roc_id: Annotated[int, Body()],
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])],
):
    await callAPI(ACHModel.claim_ach_credit, ach_credit_id, roc_id)
    return {"msg": "Credit claimed successfully"}


@ach_router.put(
    "/",
)
async def update_ach_credit(
    ach_credit: Annotated[ACHCredit, Body()],
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])],
):
    await callAPI(ACHModel.update_by_id, ach_credit)
    return {"msg": "Credit successfully updated"}


@ach_router.delete(
    "/",
)
async def delete_ach_credit(
    credit_id: Annotated[int, Body()],
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])],
):
    await callAPI(ACHModel.delete_by_id, credit_id)
    return {"msg": "Credit successfully deleted"}


@ach_router.post(
    "/batch",
)
async def import_ach_credits_from_csv(
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])],
    file: UploadFile = File(),
):
    await callAPI(ACHModel.bulk_import_from_csv, file)
    return {"msg": "Credits successfully imported"}


@ach_router.post(
    "/descriptions",
)
async def post_description(
    credit_description: Annotated[NewCreditDescription, Body()],
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])],
):
    await callAPI(ACHModel.post_description, credit_description)
    return {"msg": "Credit description added successfully"}


@ach_router.get(
    "/descriptions",
)
async def get_descriptions(
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])]
):
    descriptions = await callAPI(ACHModel.get_credit_descriptions)
    return {"descriptions": descriptions}
