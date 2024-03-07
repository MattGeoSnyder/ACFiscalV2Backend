from .CRUDModel import CRUDModel
from typing import List, Union, Dict
import csv
import re
import io
from datetime import date
import math
from pydantic import BaseModel, Field
from fastapi import UploadFile
import json


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

    @staticmethod
    async def search_ach_credits(**kwargs):
        query = ""
        params = []

        if kwargs["outstanding"]:
            query += "SELECT * FROM ach_credits WHERE claimed IS NULL "
        else:
            query += "SELECT * FROM ach_credits WHERE claimed IS NOT NULL "

        if kwargs["amount_lb"] and kwargs["amount_ub"]:
            query += "AND amount_in_cents BETWEEN %s AND %s "
            params.append(kwargs["amount_lb"])
            params.append(kwargs["amount_ub"])
        elif kwargs["amount_lb"]:
            query += "AND amount_in_cents >= %s "
            params.append(kwargs["amount_lb"])
        elif kwargs["amount_ub"]:
            query += "AND amount_in_cents <= %s "

        if kwargs["fund"]:
            query += "AND fund = %s "
            params.append(kwargs["fund"])

        if kwargs["description"]:
            query += "AND description LIKE %s "
            key_words: List[str] = [
                key_word.strip() for key_word in kwargs["description"].split(",")
            ]
            description = "%" + "%".join(key_words) + "%"
            params.append(description)

        if kwargs["received_lb"] and kwargs["received_ub"]:
            query += "AND received BETWEEN %s AND %s "
            params.append(kwargs["received_lb"])
            params.append(kwargs["received_ub"])
        elif kwargs["received_lb"]:
            query += "AND received > %s "
            params.append(kwargs["received_lb"])
        elif kwargs["received_ub"]:
            query += "AND received < %s "
            params.append(kwargs["received_ub"])

        if kwargs["claimed_lb"] and kwargs["claimed_ub"]:
            query += "AND claimed BETWEEN %s AND %s "
            params.append(kwargs["claimed_lb"])
            params.append(kwargs["claimed_ub"])
        elif kwargs["claimed_lb"]:
            query += "AND claimed > %s "
            params.append(kwargs["claimed_lb"])
        elif kwargs["claimed_ub"]:
            query += "AND claimed < %s "
            params.append(kwargs["claimed_ub"])

        if kwargs["roc_id"]:
            query += "AND roc_id = %s "
            params.append(kwargs["roc_id"])

        if kwargs["department_id"]:
            query += "AND department_id = %s "
            params.append(kwargs["department_id"])

        query += "ORDER BY received DESC, amount_in_cents DESC "
        if kwargs["skip"]:
            query += "SKIP %s "
            params.append(kwargs["skip"])

        query += "LIMIT %s;"
        params.append(kwargs["limit"])

        with ACHModel._cursor() as cursor:
            cursor.execute(query, (*params,))

            ach_credits = cursor.fetchall()
            return ach_credits

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
        descriptions = ACHModel.get_credit_descriptions()
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
