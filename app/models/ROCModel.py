from .CRUDModel import CRUDModel
from pydantic import BaseModel, Field
from fastapi import UploadFile
from typing import List, Union
from datetime import datetime
from lib.parse_roc import parse_roc
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

    @classmethod
    async def post_roc(
        cls,
        roc: UploadFile,
        supporting_docs: List[UploadFile],
        creditIds: List[int],
        total: int,
        user_id: str = "1",
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
                    (user_id, total),
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

    @classmethod
    async def get_roc_by_id(roc_id: int):
        with ROCModel._cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM rocs WHERE id = %s
                """,
                (roc_id,),
            )
            return cursor.fetchone()

    @classmethod
    async def get_rocs(cls, limit=10, offset=0, booked=False):
        with ROCModel._cursor() as cursor:
            cursor.execute(
                f"""
                SELECT rocs.*, users.first_name, users.last_name, departments.name as department_name, SUM(ach_credits.amount_in_cents) as ach_total
                FROM rocs 
                JOIN ach_credits ON rocs.id = ach_credits.roc_id
                JOIN users ON rocs.user_id = users.id
                JOIN departments ON users.department_id = departments.id
                WHERE booked IS {"NOT NULL" if booked else "NULL"}
                GROUP BY rocs.id 
                LIMIT %s
                OFFSET %s;
                """,
                (limit, offset),
            )
            return cursor.fetchall()
