from models.CRUDModel import CRUDModel
from typing import List, Union, Dict
import csv
import re
import io
from datetime import date
import math
from pydantic import BaseModel, Field
from fastapi import UploadFile, Query
import json
from lib.constants import MAX_QUERY_LENGTH
from enum import Enum


class SortColumns(Enum):
    received: str = "received"
    amount: str = "amount_in_cents"


class Fund(Enum):
    bond_interest: str = "11102"
    liquid_fuels: str = "11103"
    dpw: str = "11104"
    licensing: str = "11105"
    econ: str = "11106"
    kane: str = "11108"
    aging: str = "11112"
    dhs: str = "11113"
    general_fund: str = "11151"


class AchSearchParams(BaseModel):
    outstanding: bool = Field(False)
    amount_lb: Union[int, None] = Field(None)
    amount_ub: Union[int, None] = Field(None)
    fund: Union[Fund, None] = Field(
        Query(
            None,
            description="Can only search by fund number",
        )
    )
    description: Union[str, None] = Field(None)
    received_lb: Union[str, None] = Field(None)
    received_ub: Union[str, None] = Field(None)
    claimed_lb: Union[str, None] = Field(None)
    claimed_ub: Union[str, None] = Field(None)
    roc_id: Union[int, None] = Field(None)
    department_id: Union[int, None] = Field(None)
    order_by: Union[SortColumns, None] = Field(
        Query(
            SortColumns.received,
            description="Can only sort by received or amount_in_cents",
        )
    )
    desc: Union[bool, None] = Field(True)
    limit: Union[int, None] = Field(MAX_QUERY_LENGTH)
    skip: int = Field(0)


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


class ACHModel(CRUDModel):
    _tablename = "ach_credits"

    def __init__(self):
        super().__init__()

    @staticmethod
    def is_credit(credit):
        return credit["Transaction"] == "ACH Credits"

    @staticmethod
    def categorize_credit(credit, descriptions):
        department_id = None
        if credit.get("AccountName"):
            if credit.get("AccountName")[-5:] == "11108":
                department_id = 16
            elif credit.get("AccountName")[-5:] == "11106":
                department_id = 9

        else:
            for description in descriptions:
                keywords_arr: List[str] = description["keywords_array"]
                keywords = ".*" + ".*".join(keywords_arr) + ".*"
                if re.match(keywords, description):
                    department_id = description["department_id"]

        return department_id

    @classmethod
    async def search_ach_credits(
        cls,
        search: AchSearchParams,
    ):
        query = "SELECT ach_credits.*, departments.name as department FROM ach_credits JOIN departments ON ach_credits.department_id = departments.id "
        params = []

        if search.outstanding:
            query += "WHERE claimed IS NULL "
        else:
            query += "WHERE claimed IS NOT NULL "

        if search.amount_lb and search.amount_ub:
            query += "AND amount_in_cents BETWEEN %s AND %s "
            params.append(search.amount_lb)
            params.append(search.amount_ub)
        elif search.amount_lb:
            query += "AND amount_in_cents >= %s "
            params.append(search.amount_lb)
        elif search.amount_ub:
            query += "AND amount_in_cents <= %s "
            params.append(search.amount_ub)

        if search.fund:
            query += "AND fund = %s "
            params.append(search.fund)

        if search.description:
            query += "AND description LIKE %s "
            key_words: List[str] = [
                key_word.strip() for key_word in search.description.split(",")
            ]
            description = "%" + "%".join(key_words) + "%"
            params.append(description)

        if search.received_lb and search.received_ub:
            query += "AND received BETWEEN %s AND %s "
            params.append(search.received_lb)
            params.append(search.received_ub)
        elif search.received_lb:
            query += "AND received > %s "
            params.append(search.received_lb)
        elif search.received_ub:
            query += "AND received < %s "
            params.append(search.received_ub)

        if search.claimed_lb and search.claimed_ub:
            query += "AND claimed BETWEEN %s AND %s "
            params.append(search.claimed_lb)
            params.append(search.claimed_ub)
        elif search.claimed_lb:
            query += "AND claimed > %s "
            params.append(search.claimed_lb)
        elif search.claimed_ub:
            query += "AND claimed < %s "
            params.append(search.claimed_ub)

        if search.roc_id:
            query += "AND roc_id = %s "
            params.append(search.roc_id)

        if search.department_id:
            query += "AND department_id = %s "
            params.append(search.department_id)

        if search.order_by:
            query += "ORDER BY %s "
            params.append(search.order_by)
            if search.desc:
                query += "DESC "
            else:
                query += "ASC "
        else:
            query += "ORDER BY received DESC, amount_in_cents DESC "

        if search.skip:
            query += "SKIP %s "
            params.append(search.skip)

        query += "LIMIT %s;"
        params.append(search.limit)

        with cls._cursor() as cursor:
            cursor.execute(query, (*params,))

            ach_credits = cursor.fetchall()
            return ach_credits

    @staticmethod
    async def post_ach_credit(credit: NewAchCredit):
        with ACHModel._cursor() as cursor:
            cursor.execute(
                """INSERT INTO ach_credits
                            (amount_in_cents, fund, description, received, claimed, roc_id, department_id) 
                            VALUES
                            (%s, %s, %s, %s, %s, %s, %s)
                            """,
                credit.model_dump().values(),
            )

    @staticmethod
    async def get_credit_descriptions():
        with ACHModel._cursor() as cursor:
            cursor.execute(
                """SELECT * FROM credit_descriptions cd JOIN departments d ON cd.department_id = d.id;"""
            )

            descriptions = cursor.fetchall()
            return descriptions

    @staticmethod
    async def post_description(credit_description: Dict):
        keywords: str = credit_description["description"].split(",")
        for keyword in keywords:
            keyword.strip()
        keywords_array = json.dumps(keywords)

        credit_description["keywords_array"] = keywords_array

        with ACHModel._cursor() as cursor:
            cursor.execute(
                """
                          INSERT INTO credit_descriptions
                          (keywords_array, fund, department_id) 
                           """,
                credit_description.values(),
            )

    @staticmethod
    async def bulk_import_from_csv(file: UploadFile):
        descriptions = await ACHModel.get_credit_descriptions()
        # pdb.set_trace()
        bytes_file = file.file.read()
        file_string = bytes_file.decode("utf-8")
        string_file = io.StringIO(file_string)
        credits = csv.DictReader(string_file, delimiter=",")

        for credit in credits:
            department_id = ACHModel.categorize_credit(credit, descriptions)

            credit_dict = {}
            credit_dict["amount_in_cents"] = math.floor(float(credit["Amount"]) * 100)
            date_vals = [int(number) for number in credit["AsOfDate"].split("/")]
            credit_dict["received"] = str(
                date(date_vals[2], date_vals[0], date_vals[1])
            )
            credit_dict["fund"] = int(credit["AccountName"][-5:])
            credit_dict["description"] = credit["Description"]
            credit_dict["department_id"] = department_id
            new_credit: NewAchCredit = NewAchCredit(**credit_dict)
            await ACHModel.post_ach_credit(new_credit)
