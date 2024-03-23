from pydantic import BaseModel
from typing import Union


class ROCLineItem(BaseModel):
    id: int
    mcu: str
    cost_center: str
    object_number: str
    subsidiary: Union[str, None]
    subledger: Union[str, None]
    explanation: str
    amount_in_cents: int

    @staticmethod
    def search_line_item_by_roc_id(roc_id: int):
        pass

    @staticmethod
    def create_line_item(
        roc_id: int,
        mcu: str,
        cost_center: str,
        object_number: str,
        subsidiary: Union[str, None],
        subledger: Union[str, None],
        explanation: str,
        amount_in_cents: int,
    ):
        pass

    @staticmethod
    def update_line_item(
        roc_id: int,
        mcu: str,
        cost_center: str,
        object_number: str,
        subsidiary: Union[str, None],
        subledger: Union[str, None],
        explanation: str,
        amount_in_cents: int,
    ):
        pass

    @staticmethod
    def delete_line_item(roc_id: int):
        pass

    @staticmethod
    def search_line_item_by_roc_id(roc_id: int):
        with NewROCLineItem._cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM roc_descriptions WHERE roc_id = %s
                """,
                (roc_id,),
            )
            return cursor.fetchall()

    @staticmethod
    def search_line_item_by_department_id(department_id: int):
        with NewROCLineItem._cursor() as cursor:
            cursor.execute(
                """
                SELECT rd.* FROM ach_credits 
                JOIN rocs AS r ON ach_credits.roc_id = rocs.id
                JOIN roc_descriptions AS rd ON rocs.id = roc_descriptions.roc_id
                WHERE claimed IS NOT NULL AND department_id = %s
                """,
                (department_id,),
            )
            return cursor.fetchall()


class NewROCLineItem(BaseModel):
    mcu: str
    cost_center: str
    object_number: str
    subsidiary: Union[str, None]
    subledger: Union[str, None]
    explanation: str
    amount_in_cents: int
