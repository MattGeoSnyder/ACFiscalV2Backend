from fastapi import FastAPI, Path, HTTPException
import MySQLdb
import uvicorn
from api import API
from typing import Callable, List, Dict, Any
from pydantic import ValidationError
from typing_extensions import Annotated
from models import NewUser, User

app = FastAPI()


async def callAPI(
    func: Callable, *args: List, **kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    try:
        return func(*args, **kwargs)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e["detail"][0]["msg"])
    except MySQLdb.Error as e:
        raise HTTPException(status_code=500, detail=e.args[1])


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/auth/signup")
async def signup(new_user: NewUser):
    return await callAPI(API.signup, **new_user.model_dump())


@app.get("/departments")
async def get_all_departments():
    return await callAPI(API.get_all_departments, [])


@app.get("/departments/{department_id}")
async def get_department_by_id(
    department_id: Annotated[int, Path(title="The id of the department to get")]
):
    return await callAPI(API.get_department_by_id, [department_id])


if __name__ == "__main__":
    uvicorn.run("routes:app", host="0.0.0.0", port=8000, reload=True)
