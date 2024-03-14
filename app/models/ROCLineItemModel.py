from pydantic import BaseModel
from typing import Union


class NewROCLineItem(BaseModel):
    mcu: str
    cost_center: str
    object_number: str
    subsidiary: Union[str, None]
    subledger: Union[str, None]
    explanation: str
    amount_in_cents: int
