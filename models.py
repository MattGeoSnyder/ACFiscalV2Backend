from typing import Union
from typing_extensions import Annotated

from pydantic import BaseModel, Field


class NewUser(BaseModel):
    first_name: str = Field("First Name", max_length=25)
    last_name: str = Field("Last Name", max_length=25)
    email: str = Field(
        "Matthew.Snyder@alleghenycounty.us",
        max_length=75,
        pattern=r"[a-z,A-Z]+.[a-z,A-Z]+@alleghenycounty.us$",
    )
    password: str = Field("secret1234", max_length=30)
    department_id: int = Field("1", gt=0)


class User(NewUser):
    id: int
    auth: bool
