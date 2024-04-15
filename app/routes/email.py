from fastapi import APIRouter
import smtplib
from email.message import EmailMessage
from lib.callAPI import callAPI
from models.ROCModel import ROCModel
from models.ROCLineItemModel import ROCLineItem
from models.UserModel import UserModel
from typing import Dict
from dotenv import load_dotenv
import os

load_dotenv()


s = smtplib.SMTP("localhost:1025")

email_router = APIRouter(prefix="/email", tags=["Email"])


@email_router.post("/bookRoc", summary="Send email to control cage when ROC is booked")
async def book_roc_email(roc_id, fund: str):

    roc_detail = await callAPI(ROCLineItem.search_line_item_by_roc_id, roc_id)
    roc_detail.get("line_items")

    claimed_by: Dict[str, any] = await UserModel.get_user_by_id(
        roc_detail.get("user_id")
    )

    body = f"""Please book the following ROC into {fund}:\n"""

    for item in roc_detail.get("line_items", []):
        body += f"{item.get('mcu')} {item.get('cost_center')} {item.get('object_number')} {item.get('explanation')} {item.get('amount_in_cents')}\n"

    message = EmailMessage()
    message.set_content(body)
    message["Subject"] = (
        f"ROC--{claimed_by.get('name', 'Unknown')}--{roc_detail.get('booked', 'Today')}"
    )

    # TODO: Change email addresses after testing. Do not hard code
    message["From"] = s.user
    message["To"] = "mattgeosnyder@gmail.com"

    s.send_message(message)
    s.quit()
