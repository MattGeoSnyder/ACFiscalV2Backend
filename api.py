from fastapi import HTTPException, Depends, UploadFile
from db import db
import MySQLdb
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Dict, List
from enum import Enum
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from models import User, NewAchCredit, NewROC
import json
from ach import categorize_credit
import csv
import pdb
import io
import math
from datetime import date
import pandas

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Table(Enum):
    USER = "users"
    DEPARTMENTS = "departments"
    ACH = "ach_credits"
    ROC = "rocs"


class CRUDModel: 
    def __init__(self, tablename: str, db):
        self.tablename = tablename
        self.db = db
        self.cursor = db.cursor

    def set_table(self, tablename):
        self.tablename = tablename
        return self

    async def add(self, **args):
        keys = args.keys()
        values = args.values()
        keys_tuple = f"({', '.join(keys)})"
        values_tuple = f"({', '.join(['%s' for _ in range(len(values))])})"
        query = f"""
            INSERT INTO {self.tablename}
            {keys_tuple}
            VALUES
            {values_tuple};
            """
        with self.cursor() as cursor:
            cursor.execute(query, (*values,))

    async def get_by_id(self, id: int, *cols: (str)):
        f_cols = ', '.join(cols)
        query = f"""
            SELECT {f_cols} FROM {self.tablename}
            WHERE id = %s;""" 
        with self.cursor() as cursor:
            cursor.execute(query, (id, ))
            item = cursor.fetchone()
            return item
        
    async def get_all_paginated(self, offset=0, limit=20):
        query = f"""SELECT * FROM {self.tablename}
            LIMIT %s OFFSET %s"""
        with self.cursor() as cursor:
            cursor.execute(query, (limit, offset))
            items = cursor.fetchall()
            return items

    async def update_by_id(self, id, **new_vals):
        keys_tup = ', '.join([f'{key} = %s' for key in new_vals.keys()])
        values_tup = new_vals.values()
        query = f"""
            UPDATE {self.tablename}
            SET {keys_tup}
            WHERE id = %s"""
        with self.cursor() as cursor:
            cursor.execute(query, (*values_tup, id, ))

    async def delete_by_id(self, id):
        query = f"""
            DELETE FROM {self.tablename}
            WHERE id = %s"""
        with self.cursor() as cursor:
            cursor.execute(query, (id, ))


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def create_access_token(data: Dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(
        to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
    )
    return encoded_jwt


def authenticate_user(email: str, password: str):
    user = API.get_user_by_email(email).get("user")
    if not user:
        return False
    if not verify_password(password, user.get("password")):
        return False
    return user


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), os.getenv("ALGORITHM"))
        email: str = payload.get("email")
        if email is None:
            raise HTTPException(401, "Unauthorized")
    except JWTError:
        raise HTTPException(401, "Unauthorized")
    user = API.get_user_by_id(payload.get("id"))
    if user is None:
        raise HTTPException(401, "Unauthorized")
    return user

class UserModel(CRUDModel):

    def __init__(self, db):
        super().__init__('users', db)

    async def signup(self, user):
        # with self.cursor() as cursor:
        #     cursor.execute(
        #         """
        #             SELECT * FROM users
        #             WHERE email = %s;
        #         """,
        #         (user["email"],),
        #     )

        #     existing_user = cursor.fetchone()
        existing_user = await self.get_user_by_email(user.get("email"))

        if existing_user:
            raise HTTPException(
                409, f"Account already registered with email {user['email']}"
            )

        hashed_password = get_password_hash(user["password"])
        new_user = {**user, "password": hashed_password}

        with self.cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO users
                    (first_name, last_name, email, password, department_id)
                    VALUES
                    (%s, %s, %s, %s, %s);
                """,
                new_user.values(),
            )
            id = cursor.lastrowid
            token = create_access_token(data={
                "id": id,
                "email": user.get('email'),
                "department_id": user.get('department_id')
            })

            return token 

    async def verify_token(self, form_data):
        user = self.get_user_by_email(form_data.get("email"))
        if not User:
            raise HTTPException(401, "Unauthorized")
        token = create_access_token(
            data={
                "id": user.get("id"),
                "email": user.get("email"),
                "department_id": user.get("department_id"),
            }
        )
        return token

    async def get_user_by_id(self, id: int):
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users WHERE id = %s;",
                (id,),
            )
            user = cursor.fetchone()

            return user

    async def get_user_by_email(self, email: str):
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users WHERE email = %s;",
                (email,),
            )

            user = cursor.fetchone()
            return user


class ACH_Credits(CRUDModel):
    def __init__(self, db):
        super().__init__('ach_credits', db)
    
    async def search_ach_credits(self, **kwargs):
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

        with self.cursor() as cursor:
            cursor.execute(query, (*params,))

            ach_credits = cursor.fetchall()
            return ach_credits


class API:
    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor
        self.error = MySQLdb.Error


    async def get_all_departments(self):
        with self.cursor() as cursor:
            cursor.execute("SELECT * FROM departments")
            departments = cursor.fetchall()

            return departments

    async def get_department_by_id(self, id: int):
        with self.cursor() as cursor:
            cursor.execute("SELECT * FROM departments WHERE id=%s", (id,))
            department = cursor.fetchone()

            return department

    async def get_all_users(self) -> List[User]:
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users;"
            )

            users = cursor.fetchall()
            return users

    async def get_user_by_id(self, id: int):
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users WHERE id = %s;",
                (id,),
            )
            user = cursor.fetchone()

            return user

    async def get_user_by_email(self, email: str):
        with self.cursor() as cursor:
            cursor.execute(
                "SELECT id, email, first_name, last_name, department_id FROM users WHERE email = %s;",
                (email,),
            )

            user = cursor.fetchone()
            return user

    async def search_ach_credits(self, **kwargs):
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

        with self.cursor() as cursor:
            cursor.execute(query, (*params,))

            ach_credits = cursor.fetchall()
            return ach_credits

    async def get_credit_descriptions(self):
        with self.cursor() as cursor:
            cursor.execute(
                """SELECT * FROM credit_descriptions cd JOIN departments d ON cd.department_id = d.id;"""
            )

            descriptions = cursor.fetchall()
            return descriptions

    async def post_description(self, credit_description: Dict):
        keywords: str = credit_description["description"].split(",")
        for keyword in keywords:
            keyword.strip()
        keywords_array = json.dumps(keywords)

        credit_description["keywords_array"] = keywords_array

        with self.cursor as cursor:
            cursor.execute(
                """
                          INSERT INTO credit_descriptions
                          (keywords_array, fund, department_id) 
                           """,
                credit_description.values(),
            )

    async def post_ach_credit(self, credit: NewAchCredit):
        with self.cursor() as cursor:
            cursor.execute(
                """INSERT INTO ach_credits
                            (amount_in_cents, fund, description, received, claimed, roc_id, department_id) 
                            VALUES
                            (%s, %s, %s, %s, %s, %s, %s)
                           """,
                credit.model_dump().values(),
            )

    async def update_ach_credit(self, credit_data):
        with self.cursor() as cursor:
            cursor.execute(
                """
                UPDATE ach_credits SET 
                    fund = %s, description = %s, received = %s, claimed = %s, department_id = %s
                WHERE id = %s
                """,
                (
                    credit_data["fund"],
                    credit_data["description"],
                    credit_data["received"],
                    credit_data["claimed"],
                    credit_data["department_id"],
                    credit_data["id"],
                ),
            )

    async def delete_ach_credit(self, credit_id):
        with self.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM ach_credits WHERE id = %s
                """,
                (credit_id,),
            )

    async def bulk_import_from_csv(self, file: UploadFile):
        descriptions = self.get_credit_descriptions()
        # pdb.set_trace()
        departments = await self.get_all_departments()
        bytes_file = file.file.read()
        file_string = bytes_file.decode("utf-8")
        string_file = io.StringIO(file_string)
        credits = csv.DictReader(string_file, delimiter=",")

        for credit in credits:
            department_id = categorize_credit(credit, descriptions, departments)

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
            await self.post_ach_credit(new_credit)

    async def post_roc(self, file: UploadFile, user_id: int = 1) -> int:
        bytes_file = file.file.read()
        filename = file.filename
        roc_data = pandas.read_excel(bytes_file)
        # pdb.set_trace()
        print(roc_data.iat[5, 8])
        amount_in_cents = roc_data.iat[5, 8] * 100
        new_roc = NewROC(
            roc=bytes_file,
            filename=filename,
            amount_in_cents=amount_in_cents,
            user_id=user_id,
        )
        with self.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO rocs 
                            (filename, roc, amount_in_cents, user_id)
                            VALUES (%s, %s, %s, %s);
                """,
                (new_roc.model_dump().values()),
            )
            roc_id = cursor.lastrowid
            return roc_id

    async def claim_ach_credit(self, ach_credit_id, roc_id):
        with self.cursor() as cursor:
            cursor.execute(
                """
                UPDATE ach_credits
                SET claimed = %s, roc_id = %s
                WHERE id = %s;
                """,
                (str(date.today()), roc_id, ach_credit_id),
            )


API = API(db)
crud_model = CRUDModel('', db)
user_model = UserModel(db)
credits_model = ACH_Credits(db)