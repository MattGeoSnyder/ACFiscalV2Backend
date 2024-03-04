from fastapi import APIRouter, Depends, Body, UploadFile
from ..models.ROCModel import ROCModel
from ..lib.callAPI import callAPI

roc_router = APIRouter(prefix="/roc", tags=["ROC"])


@roc_router.post("/roc")
async def post_roc(roc: UploadFile, user_id: int):
    roc_id = await callAPI(ROCModel.post_roc, roc, user_id)
    return {"msg": "ROC posted successfully"}
