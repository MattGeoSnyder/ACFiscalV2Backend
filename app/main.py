from fastapi import FastAPI, Path, Request, Security
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from typing_extensions import Annotated
from enum import Enum
from models.CRUDModel import CRUDModel
from routes import ach, auth, roc, users, email
from lib import callAPI
from models.TokenModel import TokenModel, TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ach_router = ach.ach_router
auth_router = auth.auth_router
roc_router = roc.roc_router
user_router = users.user_router
email_router = email.email_router
callAPI = callAPI.callAPI

app = FastAPI()

app.include_router(ach_router)
app.include_router(auth_router)
app.include_router(roc_router)
app.include_router(user_router)
app.include_router(email_router)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    print(exc)


# #
# @app.middleware("http")
# async def debug_request(request: Request, call_next):
#     print(request.headers)
#     response = await call_next(request)
#     return response


class Tags(Enum):
    auth = "Authentication"
    users = "Users"
    departments = "Departments"
    ach_credits = "ACH Credits"
    rocs = "ROCs"


@app.get("/")
async def root(
    tokenData: Annotated[
        TokenData, Security(TokenModel.decode_token, scopes=["admin"])
    ],
):
    print(tokenData)
    return {"message": "Hello World"}


@app.get("/departments", tags=[Tags.departments])
async def get_all_departments():
    CRUDModel._tablename = "departments"
    departments = await callAPI(CRUDModel.get_all_paginated, 0, 100)
    return {"departments": departments}


@app.get("/departments/{department_id}", tags=[Tags.departments])
async def get_department_by_id(
    department_id: Annotated[int, Path(title="The id of the department to get", gt=0)]
):
    CRUDModel.set_table("departments")
    department = await callAPI(CRUDModel.get_by_id, department_id)
    return {"department": department}
