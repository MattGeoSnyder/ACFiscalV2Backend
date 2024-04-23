from pydantic import BaseModel
from fastapi import Query
from typing import Union
from .CRUDModel import CRUDModel
from typing import Dict, List


class NewROCLineItem(BaseModel):
    mcu: str
    cost_center: str
    object_number: str
    subsidiary: Union[str, None]
    subledger: Union[str, None]
    explanation: str
    amount_in_cents: int


class ROCDetail(BaseModel):
    id: int
    amount_in_cents: int
    user_id: int
    booked: bool
    fund: str
    line_items: List[NewROCLineItem]


class ROCLineItemModel(BaseModel):
    mcu: Union[str, None] = Query(None)
    cost_center: Union[str, None] = Query(None)
    object_number: Union[str, None] = Query(None)
    subsidiary: Union[str, None] = Query(None)
    explanation: Union[str, None] = Query(None)
    amount_in_cents: Union[int, None] = Query(None)


class ROCLineItem(CRUDModel):
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

    @classmethod
    async def search_line_item_by_roc_id(cls, roc_id: int, repsonse_model=ROCDetail):
        with ROCLineItem._cursor() as cursor:
            cursor.execute(
                """
                SELECT rocs.*, rd.*
                FROM rocs
                JOIN roc_descriptions AS rd
                ON rocs.id = rd.roc_id 
                WHERE roc_id = %s
                """,
                (roc_id,),
            )
            res: List[Dict] = cursor.fetchall()
            roc = {}
            roc["line_items"] = []
            roc["id"] = res[0]["id"]
            roc["amount_in_cents"] = res[0]["amount_in_cents"]
            roc["user_id"] = res[0]["user_id"]
            roc["booked"] = res[0]["booked"]
            roc["fund"] = res[0]["fund"]
            for item in res:
                line_item = {}
                line_item["id"] = item["rd.id"]
                line_item["mcu"] = item["mcu"]
                line_item["cost_center"] = item["cost_center"]
                line_item["object_number"] = item["object_number"]
                line_item["subsidiary"] = item["subsidiary"]
                line_item["subledger"] = item["subledger"]
                line_item["explanation"] = item["explanation"]
                line_item["amount_in_cents"] = item["amount_in_cents"]
                roc["line_items"].append(line_item)
            return roc

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

    @classmethod
    async def search_roc_line_items(
        cls, params: ROCLineItemModel, limit: int = 20, offset: int = 0
    ):
        with ROCLineItem._cursor() as cursor:

            param_values = []
            for val in params.model_dump().values():
                if val:
                    param_values.append(val)

            query = """SELECT * FROM roc_descriptions JOIN rocs ON roc_descriptions.roc_id = rocs.id """
            if params.mcu:
                query += "AND mcu == %s "
            if params.cost_center:
                query += "AND cost_center == %s "
            if params.object_number:
                query += "AND object_number == %s "
            if params.subsidiary:
                query += "AND subsidiary == %s "
            if params.explanation:
                query += "AND explanation LIKE %s "
            if params.amount_in_cents:
                query += "AND amount_in_cents == %s "
            query += "LIMIT %s OFFSET %s;"

            cursor.execute(
                query,
                (*(param_values), limit, offset),
            )
            return cursor.fetchall()
