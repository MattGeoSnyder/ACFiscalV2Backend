from fastapi import FastAPI, Path, HTTPException, Depends, Body, Form, UploadFile, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import MySQLdb
import uvicorn
from api import API, CRUDModel
from typing import Callable, List, Dict, Any
from pydantic import ValidationError
from typing_extensions import Annotated
from models import (
    NewUser,
    User,
    Token,
    TokenRequestForm,
    AchSearchParams,
    NewAchCredit,
    NewCreditDescription,
    ACHCredit,
)
from enum import Enum
import pdb

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


user_model = CRUDModel
user_model.add(username="MattgeoSnyder", password="test1234")

async def callAPI(
    func: Callable, *args: List, **kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    try:
        return await func(*args, **kwargs)
    except HTTPException as e:
        raise e
    except MySQLdb.Error as e:
        print(str(e))
        raise HTTPException(500, str(e)) 
    except Exception as e:
        # pdb.set_trace()
        raise HTTPException(500, str(e))

# @app.middleware("http")
# async def debug_request(request: Request, call_next):
#     body = await request.body()
#     print(body)
#     try:
#         response = await call_next(request)
#         return response
#     except Exception as e:
#         print(str(e))
#         raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    return JSONResponse(exc["detail"]["msg"], status_code=422)

class Tags(Enum):
    auth = "Authentication"
    users = "Users"
    departments = "Departments"
    ach_credits = "ACH Credits"
    rocs = "ROCs"

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/token", response_model=Token, tags=[Tags.auth])
async def get_access_token(
    email: str = Form(
        max_length=75,
        pattern=r"[a-z,A-Z]+.[a-z,A-Z]+@alleghenycounty.us$",
        description="Must use Allegheny County email, i.e: First Name.Last Name@alleghenycounty.us. Email must be less than 75 characters long.",
        examples=["Matthew.Snyder@alleghenycounty.us"],
    ),
    password: str = Form(examples=["secret1234"]),
):
    token = await callAPI(API.verify_token, {"email": email, "password": password})
    return token


@app.post("/signup", status_code=201, tags=[Tags.auth])
async def signup(new_user: Annotated[NewUser, Body]):
    print(new_user)
    new_user
    token = await callAPI(API.signup, new_user.model_dump())
    return { "token": token, "token_type": "bearer" } 


@app.get("/departments", tags=[Tags.departments])
async def get_all_departments():
    departments = await callAPI(API.get_all_departments)
    return {"departments": departments}


@app.get("/departments/{department_id}", tags=[Tags.departments])
async def get_department_by_id(
    department_id: Annotated[int, Path(title="The id of the department to get", gt=0)]
):
    department = await callAPI(API.get_department_by_id, department_id)
    return {"department": department}


@app.get("/users", tags=[Tags.users])
async def get_users():
    users = await callAPI(API.get_all_users)
    return {"users": users}


@app.get("/users/{user_id}", tags=[Tags.users])
async def get_user_by_id(
    user_id: Annotated[int, Path(title="The id of the user to get")]
):
    user = await callAPI(API.get_user_by_id, user_id)
    return {"user": user}


@app.get("/ach", tags=[Tags.ach_credits])
async def search_ach_credits(params: AchSearchParams = Depends()):
    ach_credits = await callAPI(API.search_ach_credits, **params.model_dump())
    return {"ach_credits": ach_credits}


@app.post("/ach", tags=[Tags.ach_credits])
async def post_ach_credit(ach_credit: NewAchCredit = Body()):
    await callAPI(API.post_ach_credit, ach_credit)
    return {"msg": "Credit successfully posted"}


@app.patch("/ach", tags=[Tags.ach_credits])
async def patch_ach_credit(ach_credit_id: int = Body(), roc_id: int = Body()):
    await callAPI(API.claim_ach_credit, ach_credit_id, roc_id)
    return {"msg": "Credit claimed successfully"}


@app.put("/ach", tags=[Tags.ach_credits])
async def update_ach_credit(ach_credit: ACHCredit = Body()):
    await callAPI(API.update_ach_credit, ach_credit)
    return {"msg": "Credit successfully updated"}


@app.delete("/ach", tags=[Tags.ach_credits])
async def delete_ach_credit(credit_id=Body()):
    await callAPI(API.delete_ach_credit, credit_id)
    return {"msg": "Credit successfully deleted"}


@app.post("/ach/batch", tags=[Tags.ach_credits])
async def import_ach_credits_from_csv(file: UploadFile):
    await callAPI(API.bulk_import_from_csv, file)
    return {"msg": "Credits successfully imported"}


@app.post("/ach/descriptions", tags=[Tags.ach_credits])
async def post_description(credit_description: NewCreditDescription = Body()):
    await callAPI(API.post_description, credit_description)
    return {"msg": "Credit description added successfully"}


@app.get("/ach/descriptions", tags=[Tags.ach_credits])
async def get_descriptions():
    descriptions = await callAPI(API.get_credit_descriptions)
    return {"descriptions": descriptions}


@app.post("/roc", tags=[Tags.rocs])
async def post_roc(roc: UploadFile, user_id: int):
    roc_id = await callAPI(API.post_roc, roc, user_id)
    print(roc_id)
    return {"msg": "ROC posted successfully"}


if __name__ == "__main__":
    uvicorn.run("routes:app", host="0.0.0.0", port=8000, reload=True)
