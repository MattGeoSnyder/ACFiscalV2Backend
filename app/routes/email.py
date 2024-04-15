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
import ssl

load_dotenv()


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
    message["From"] = "actreasurersoffice@gmail.com"
    message["To"] = "mattgeosnyder@gmail.com"

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login("actreasurersoffice@gmail.com", os.getenv("GMAIL_PASSWORD"))
        server.send_message(message)
        server.send_message(message)
        server.quit()
