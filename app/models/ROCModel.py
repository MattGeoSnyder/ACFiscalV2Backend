from .CRUDModel import CRUDModel
from pydantic import BaseModel, Field
from fastapi import UploadFile
from typing import List, Union
from datetime import datetime
from ..lib.parse_roc import parse_roc


class NewROC(BaseModel):
    filename: str
    roc: bytes
    amount_in_cents: int
    # TODO: Need to change default value

    user_id: int = Field(1)


class ROCModel(CRUDModel):
    _tablename = "rocs"

    def __init__(self):
        super().__init__()

    @staticmethod
    async def post_roc(
        roc: UploadFile,
        supporting_docs: List[UploadFile],
        creditIds: List[int],
        total: int,
    ):
        if supporting_docs:
            for doc in supporting_docs:
                print(doc.filename)
        current = datetime.now()
        roc_line_items = await parse_roc(roc)
        print(roc_line_items)
        # with CRUDModel._cursor as cursor:
        #     cursor.execute(
        #         """START TRANSACTION;

        #         INSERT INTO rocs (user_id, amount_in_cents) VALUES (%s, %s)

        #         SET @roc_id = LAST_INSERT_ID();

        #         UPDATE ach_credits SET roc_id = @roc_id, claimed = %s WHERE id IN (%s);

        #         INSERT INTO supporting_docs (roc_id, filename, doc) VALUES
        #             (@roc_id, %s, %s)

        #         """,
        #         (1, total, current, creditIds),
        #     )
