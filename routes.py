from fastapi import FastAPI, HTTPException
import MySQLdb
import uvicorn
from api import API
from typing import Callable, List, Dict, Any

app = FastAPI()


async def callAPI(func: Callable, args: List) -> Dict[str, Any]:
    try:
        return func(*args)
    except MySQLdb.Error as e:
        raise HTTPException(status_code=500, detail=e.args[1])


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/departments")
async def get_all_departments():
    return await callAPI(API.get_all_departments, [])


@app.get("/departments/{department_id}")
async def get_department_by_id(department_id: int):
    return await callAPI(API.get_department_by_id, [department_id])


if __name__ == "__main__":
    uvicorn.run("routes:app", host="0.0.0.0", port=8000, reload=True)
