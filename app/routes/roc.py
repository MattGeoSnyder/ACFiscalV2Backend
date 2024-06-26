from fastapi import (
    APIRouter,
    UploadFile,
    Form,
    Security,
    Query,
    File,
    Body,
    Path,
    Depends,
)
from models.ROCModel import ROCModel, Fund
from models.TokenModel import TokenModel, TokenData
from models.ROCLineItemModel import ROCLineItem
from lib.callAPI import callAPI
from typing import List, Union, Any
from typing_extensions import Annotated
from models.ROCLineItemModel import ROCLineItemModel

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


@roc_router.get("/{roc_id: int}")
async def get_roc_line_items_by_id(
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])],
    roc_id: Annotated[int, Path()],
):
    roc = await callAPI(ROCLineItem.search_line_item_by_roc_id, roc_id)
    return {"roc": roc}


@roc_router.patch("/{roc_id: int}")
async def book_roc(
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])],
    roc_id: Annotated[int, Path()],
    fund: Annotated[Fund, Body()],
):
    await callAPI(ROCModel.book_roc, roc_id, **fund.model_dump())
    return {"message": "ROC booked successfully"}


@roc_router.get("/search")
async def search_roc_line_items(
    token: Annotated[TokenData, Security(TokenModel.decode_token, scopes=["admin"])],
    params: ROCLineItemModel = Depends(),
    limit: int = Query(20),
    offset: int = Query(0),
):
    line_items = await callAPI(ROCLineItem.search_roc_line_items, params, limit, offset)
    return {"line_items": line_items}
