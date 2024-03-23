from .CRUDModel import CRUDModel
from pydantic import BaseModel, Field
from fastapi import UploadFile
from typing import List, Union
from datetime import datetime
from ..lib.parse_roc import parse_roc
import pdb


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
        print(creditIds)
        if supporting_docs:
            for doc in supporting_docs:
                print(doc.filename)
        placeholders = ", ".join(["%s" for _ in range(len(creditIds))])
        print(placeholders)
        current = datetime.now()
        roc_line_items = await parse_roc(roc)
        try:
            with ROCModel._cursor() as cursor:
                cursor.execute(
                    """START TRANSACTION;

                    INSERT INTO rocs (user_id, amount_in_cents) VALUES (%s, %s);

                    """,
                    (1, total),
                )

                cursor.execute("SET @roc_id = LAST_INSERT_ID();")

                cursor.execute(
                    f"""
                    UPDATE ach_credits SET roc_id = @roc_id, claimed = %s WHERE id IN ({placeholders});
                    """,
                    (current, *creditIds),
                )

                for doc in supporting_docs:
                    cursor.execute(
                        """
                        INSERT INTO supporting_docs (roc_id, filename, doc) VALUES
                        (@roc_id, %s, %s)
                        """,
                        (doc.filename, doc.file),
                    )

                for line_item in roc_line_items:
                    cursor.execute(
                        """
                        INSERT INTO roc_descriptions (roc_id, mcu, cost_center, object_number, subsidiary, subledger, explanation, amount_in_cents)
                        VALUES (@roc_id, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            line_item["mcu"],
                            line_item["cost_center"],
                            line_item["object_number"],
                            line_item["subsidiary"],
                            line_item["subledger"],
                            line_item["explanation"],
                            line_item["amount_in_cents"],
                        ),
                    )

                cursor.execute("COMMIT;")

        except Exception as e:
            print(e)
            ROCModel._cursor().execute("ROLLBACK;")
            raise e

    @staticmethod
    async def get_roc_by_id(roc_id: int):
        with ROCModel._cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM rocs WHERE id = %s
                """,
                (roc_id,),
            )
            return cursor.fetchone()
