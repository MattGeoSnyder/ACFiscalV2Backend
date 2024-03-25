from fastapi import applications
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi import FastAPI, Path, HTTPException, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Callable, List, Dict, Any
from typing_extensions import Annotated
from enum import Enum
import pdb
from .models.CRUDModel import CRUDModel
from .routes import ach, auth, roc, users
from .lib import callAPI
from .models.UserModel import UserModel
from .models.TokenModel import TokenModel, TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ach_router = ach.ach_router
auth_router = auth.auth_router
roc_router = roc.roc_router
user_router = users.user_router
callAPI = callAPI.callAPI


def swagger_monkey_patch(*args, **kwargs):
    """
    Wrap the function which is generating the HTML for the /docs endpoint and
    overwrite the default values for the swagger js and css.
    """
    return get_swagger_ui_html(
        *args,
        **kwargs,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css"
    )


# Actual monkey patch
applications.get_swagger_ui_html = swagger_monkey_patch


app = FastAPI()
app.include_router(ach_router)
app.include_router(auth_router)
app.include_router(roc_router)
app.include_router(user_router)

origins = [
    "http://localhost:3000",
    "https://localhost:3000",
]

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


# @app.middleware("http")
# async def debug_request(request: Request, call_next):
#     try:
#         response = await call_next(request)
#         return response
#     except Exception as e:
#         print(str(e))
#         raise HTTPException(status_code=500, detail=str(e))


class Tags(Enum):
    auth = "Authentication"
    users = "Users"
    departments = "Departments"
    ach_credits = "ACH Credits"
    rocs = "ROCs"


@app.get("/")
async def root(tokenData: Annotated[TokenData, Depends(TokenModel.decode_token)]):
    print(tokenData)
    return {"message": "Hello World"}


@app.get("/departments", tags=[Tags.departments])
async def get_all_departments():
    CRUDModel.tablename = "departments"
    departments = await callAPI(CRUDModel.get_all_paginated, 0, 100)
    return {"departments": departments}


@app.get("/departments/{department_id}", tags=[Tags.departments])
async def get_department_by_id(
    department_id: Annotated[int, Path(title="The id of the department to get", gt=0)]
):
    CRUDModel.set_table("departments")
    department = await callAPI(CRUDModel.get_by_id, department_id)
    return {"department": department}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
