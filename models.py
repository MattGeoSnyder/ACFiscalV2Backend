from typing import Union
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from fastapi import Form


class Token(BaseModel):
    token: str
    token_type: str


class TokenRequestForm(BaseModel):
    email: str = Form(
        max_length=75,
        pattern=r"[a-z,A-Z]+.[a-z,A-Z]+@alleghenycounty.us$",
        description="Must use Allegheny County email. Email must be less than 75 characters long.",
        examples=["Matthew.Snyder@alleghenycounty.us"],
    )
    password: str = Form(examples=["secret1234"])


class NewUser(BaseModel):
    first_name: str = Field(max_length=25, examples=["First Name"])
    last_name: str = Field(max_length=25, examples=["Last Name"])
    email: str = Field(
        max_length=75,
        pattern=r"[a-z,A-Z]+.[a-z,A-Z]+@alleghenycounty.us$",
        description="Must use Allegheny County email. Email must be less than 75 characters long.",
        examples=["Matthew.Snyder@alleghenycounty.us"],
    )
    password: str = Field(examples=["secret1234"])
    department_id: int = Field(gt=0, examples=[1])

    # model_config = {
    #     "examples": [
    #         {
    #             "first_name": "Matthew",
    #             "last_name": "Snyder",
    #             "email": "Matthew.Snyder@alleghenycounty.us",
    #             "password": "secret1234",
    #             "department_id": 1,
    #         }
    #     ]
    # }


class User(BaseModel):
    first_name: str = Field("First Name", max_length=25)
    last_name: str = Field("Last Name", max_length=25)
    email: str = Field(
        "Matthew.Snyder@alleghenycounty.us",
        max_length=75,
        pattern=r"[a-z,A-Z]+.[a-z,A-Z]+@alleghenycounty.us$",
        description="Must use Allegheny County email. Email must be less than 75 characters long.",
    )
    department_id: int = Field("1", gt=0)


class User(NewUser):
    id: int
    auth: bool
