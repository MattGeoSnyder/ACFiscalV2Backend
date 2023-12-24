from fastapi import FastAPI, Path, HTTPException, Depends, Body, Form
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import MySQLdb
import uvicorn
from api import API
from typing import Callable, List, Dict, Any
from pydantic import ValidationError
from typing_extensions import Annotated
from models import NewUser, User, Token, TokenRequestForm, AchSearchParams, NewAchCredit

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def callAPI(
    func: Callable, *args: List, **kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    try:
        return func(*args, **kwargs)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e["msg"])
    except MySQLdb.Error as e:
        raise HTTPException(status_code=500, detail=e["msg"])
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Unknown Error")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/token", response_model=Token)
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
    return {"token": token, "token_type": "bearer"}


@app.post("/signup")
async def signup(new_user: NewUser = Body()):
    await callAPI(API.signup, new_user.model_dump())
    return {"msg": "User created successfully"}


@app.get("/departments")
async def get_all_departments():
    departments = await callAPI(API.get_all_departments, [])
    return {"departments": departments}


@app.get("/departments/{department_id}")
async def get_department_by_id(
    department_id: Annotated[int, Path(title="The id of the department to get")]
):
    department = await callAPI(API.get_department_by_id, department_id)
    return {"department": department}


@app.get("/users")
async def get_users():
    users = await callAPI(API.get_all_users)
    return {"users": users}


@app.get("/users/{user_id}")
async def get_user_by_id(
    user_id: Annotated[int, Path(title="The id of the user to get")]
):
    user = await callAPI(API.get_user_by_id, user_id)
    return {"user": user}


@app.get("/ach")
async def search_ach_credits(params: AchSearchParams = Depends()):
    ach_credits = await callAPI(API.search_ach_credits, **params.model_dump())
    return {"ach_credits": ach_credits}


@app.post("/ach")
async def post_ach_credit(ach_credit: NewAchCredit = Body(NewAchCredit)):
    return {"msg": "Credit successfully posted"}


if __name__ == "__main__":
    uvicorn.run("routes:app", host="0.0.0.0", port=8000, reload=True)
