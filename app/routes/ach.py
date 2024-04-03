from fastapi import APIRouter, Depends, Body, UploadFile, Query, Security, Form
from lib.callAPI import callAPI
from models.ACHModel import ACHModel, NewAchCredit, ACHCredit, NewCreditDescription
from pydantic import BaseModel, Field
from typing import Union
from typing_extensions import Annotated
from models.TokenModel import TokenModel, TokenData

ach_router = APIRouter(prefix="/ach", tags=["ACH Credits"])


class AchSearchParams(BaseModel):
    outstanding: bool
    amount_lb: Union[int, None] = Field(None)
    amount_ub: Union[int, None] = Field(None)
    fund: Union[int, None] = Field(None)
    description: Union[str, None] = Field(None)
    received_lb: Union[str, None] = Field(None)
    received_ub: Union[str, None] = Field(None)
    claimed_lb: Union[str, None] = Field(None)
    claimed_ub: Union[str, None] = Field(None)
    roc_id: Union[int, None] = Field(None)
    department_id: Union[int, None] = Field(None)
    limit: Union[int, None] = Field()
    skip: int = Field(0, ge=0)


@ach_router.get("/")
async def search_ach_credits(
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["user"])],
    params: Annotated[AchSearchParams, Depends()],
):
    print(token)
    ach_credits = await callAPI(ACHModel.search_ach_credits, **params.model_dump())
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
    file: Annotated[UploadFile, Form()],
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])],
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
