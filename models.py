from typing import Union
from typing_extensions import Annotated
from pydantic import BaseModel, Field
from fastapi import Form
from enum import Enum


class Token(BaseModel):
    token: str
    token_type: str


class TokenRequestForm(BaseModel):
    email: str = Annotated[
        str,
        Form(
            max_length=75,
            pattern=r"[a-z,A-Z]+.[a-z,A-Z]+@alleghenycounty.us$",
            description="Must use Allegheny County email. Email must be less than 75 characters long.",
            examples=["Matthew.Snyder@alleghenycounty.us"],
        ),
    ]
    password: str = Annotated[str, Form(examples=["secret1234"])]


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

    model_config = {
        "examples": [
            {
                "first_name": "Matthew",
                "last_name": "Snyder",
                "email": "Matthew.Snyder@alleghenycounty.us",
                "password": "secret1234",
                "department_id": 1,
            }
        ]
    }


class Role(Enum):
    USER = "user"
    ADMIN = "admin"


print(Role.USER)


class User(NewUser):
    id: int = Field(gt=0)
    password: str = Field(exclude=True)
    role: Role = Field(default=Role.USER)


class UserPermissions(BaseModel):
    id: int = Field(gt=0)
    permitted: bool
    role: Role
    department: str


class NewAchCredit(BaseModel):
    amount_in_cents: int = Field(ge=0)
    fund: int
    description: str
    received: str
    claimed: Union[str, None] = Field(None)
    roc_id: Union[int, None] = Field(None, gt=0)
    department_id: Union[int, None] = Field(None, gt=0)


class ACHCredit(NewAchCredit):
    id: int = Field(gt=0)


class NewCreditDescription(BaseModel):
    description: str
    fund: int
    department_id: int


class AchSearchParams(BaseModel):
    outstanding: bool
    amount_lb: Union[int, None] = Field(None)
    amount_ub: Union[int, None] = Field(None)
    fund: Union[int, None] = Field(None)
    description: Union[str, None] = Field(None)
    received_lb: Union[str, None] = Field(None)
    received_ub: Union[str, None] = Field(None)
    claimed_lb: Union[str, None] = Field(None)
    claimed_ub: Union[str, None] = Field(None)
    roc_id: Union[int, None] = Field(None)
    department_id: Union[int, None] = Field(None)
    limit: Union[int, None] = Field()
    skip: int = Field(0, ge=0)


class NewROC(BaseModel):
    filename: str
    roc: bytes
    amount_in_cents: int
    # TODO: Need to change default value

    user_id: int = Field(1)


class Test:
    role: Role
