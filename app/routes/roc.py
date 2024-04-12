from fastapi import APIRouter, UploadFile, Form, Security, Query, File, Body, Path
from models.ROCModel import ROCModel, Fund
from models.TokenModel import TokenModel, TokenData
from lib.callAPI import callAPI
from typing import List, Union, Any
from typing_extensions import Annotated

roc_router = APIRouter(prefix="/roc", tags=["ROC"])


@roc_router.get("/")
async def get_rocs(
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])],
    limit: int = Query(20),
    offset: int = Query(0),
    booked: bool = Query(False),
):
    rocs = await callAPI(ROCModel.get_rocs, limit, offset, booked)
    return {"rocs": rocs}


@roc_router.post("/")
async def post_roc(
    token: Annotated[
        TokenData, Security(TokenModel.decode_token, scopes=["user", "admin"])
    ],
    roc: Annotated[UploadFile, File()],
    credits: List[int] = Form(),
    total: int = Form(),
    docs: Annotated[Union[List[UploadFile], None], File()] = [],
):
    print(token, roc, credits, total, docs)
    roc_id = await callAPI(
        ROCModel.post_roc, roc, docs, credits, total, token.get("user_id")
    )
    return {"message": "ROC posted successfully"}


@roc_router.patch("/{roc_id}")
async def book_roc(
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])],
    roc_id: Annotated[int, Path()],
    fund: Annotated[Fund, Body()],
):
    await callAPI(ROCModel.book_roc, roc_id, **fund.model_dump())
    return {"message": "ROC booked successfully"}
