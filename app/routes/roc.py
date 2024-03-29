from fastapi import APIRouter, Depends, Body, UploadFile, Form
from ..models.ROCModel import ROCModel
from ..lib.callAPI import callAPI
from typing import List, Union, Any
from typing_extensions import Annotated

roc_router = APIRouter(prefix="/roc", tags=["ROC"])


@roc_router.post("/")
async def post_roc(
    roc: UploadFile,
    credits: List[int] = [],
    docs: List[UploadFile] = [],
    total: int = Form(),
):
    roc_id = await callAPI(ROCModel.post_roc, roc, docs, credits, total)
    return {"msg": "ROC posted successfully"}
